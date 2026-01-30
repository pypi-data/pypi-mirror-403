from __future__ import annotations

import json
import requests
from abc import abstractmethod
from typing import TYPE_CHECKING, Any
from typing_extensions import override
from enum import Enum
from loguru import logger
from .workflow_event import WorkflowResult

if TYPE_CHECKING:
    from .node import Node
    from .workflow import Workflow

class CallbackEvent(Enum):
    ON_WORKFLOW_START = "on_workflow_start"
    ON_WORKFLOW_END = "on_workflow_end"
    ON_WORKFLOW_ERROR = "on_workflow_error"
    ON_NODE_START = "on_node_start"
    ON_NODE_END = "on_node_end"
    ON_NODE_OUTPUT = "on_node_output"
    ON_NODE_STREAM_OUTPUT = "on_node_stream_output"

class WorkflowCallback:
    @abstractmethod
    async def on_workflow_start(self, workflow: Workflow) -> None:
        ...

    @abstractmethod
    async def on_workflow_end(self, workflow: Workflow, output: Any) -> None:
        pass

    @abstractmethod
    async def on_workflow_error(self, workflow: Workflow, node: Node, error: Any) -> None:
        pass

    @abstractmethod
    async def on_node_start(self, node: Node) -> None:
        ...

    @abstractmethod
    async def on_node_end(self, node: Node) -> None:
        ...

    @abstractmethod
    async def on_node_stream_output(self, node: Node, output: Any) -> None:
        ...

class BuiltinWorkflowCallback(WorkflowCallback):
    def __init__(self):
        self._websocket_manager = None
    
    def _get_websocket_manager(self):
        if self._websocket_manager is None:
            from service_forge.api.routers.websocket.websocket_manager import websocket_manager
            self._websocket_manager = websocket_manager
        return self._websocket_manager
    
    def _serialize_result(self, result: Any) -> Any:
        try:
            json.dumps(result)
            return result
        except (TypeError, ValueError):
            return str(result)
    
    def _get_service_name(self) -> str | None:
        try:
            from service_forge.current_service import get_service
            service = get_service()
            if service is not None:
                return service.config.name
        except Exception:
            pass
        return None
    
    async def _send_service_event(self, workflow: Workflow, event: str) -> None:
        if workflow.entry_config is None or workflow.entry_config.url is None:
            return
        
        url = None
        try:
            service_name = self._get_service_name()
            if service_name is None:
                logger.warning("Cannot get service_name, skip sending service-event")
                return
            
            url = f"{workflow.entry_config.url.rstrip('/')}/service-event"
            payload = {
                "user_id": str(workflow.trigger_event.user_id),
                "service_name": service_name,
                "workflow_name": workflow.name,
                "task_id": str(workflow.trigger_event.task_id),
                "event": event
            }
            
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
        except Exception as e:
            url_str = url if url else workflow.entry_config.url if workflow.entry_config else "unknown"
            logger.error(f"Failed to send service-event to {url_str}: {e}")
    
    @override
    async def on_workflow_start(self, workflow: Workflow) -> None:
        ...

    @override
    async def on_workflow_end(self, workflow: Workflow, output: Any) -> None:
        workflow_result = WorkflowResult(result=output, is_end=True, is_error=False)
        
        if workflow.trigger_event.task_id in workflow.real_trigger_node.result_queues:
            workflow.real_trigger_node.result_queues[workflow.trigger_event.task_id].put_nowait(workflow_result)
        if workflow.trigger_event.task_id in workflow.real_trigger_node.stream_queues:
            workflow.real_trigger_node.stream_queues[workflow.trigger_event.task_id].put_nowait(workflow_result)

        # print(workflow.entry_config, workflow.trigger_event.task_id, workflow.trigger_event.user_id)
        
        await self._send_service_event(workflow, "on_workflow_end")
        
        try:
            manager = self._get_websocket_manager()
            message = {
                "type": "workflow_end",
                "task_id": str(workflow.trigger_event.task_id),
                "result": self._serialize_result(output),
                "is_end": True,
                "is_error": False
            }
            await manager.send_to_task(workflow.trigger_event.task_id, message)
        except Exception as e:
            logger.error(f"发送 workflow_end 消息到 websocket 失败: {e}")

    @override
    async def on_workflow_error(self, workflow: Workflow, node: Node | None, error: Any) -> None:
        workflow_result = WorkflowResult(result=error, is_end=False, is_error=True)
        
        if workflow.trigger_event.task_id in workflow.real_trigger_node.result_queues:
            workflow.real_trigger_node.result_queues[workflow.trigger_event.task_id].put_nowait(workflow_result)
        if workflow.trigger_event.task_id in workflow.real_trigger_node.stream_queues:
            workflow.real_trigger_node.stream_queues[workflow.trigger_event.task_id].put_nowait(workflow_result)
        
        await self._send_service_event(workflow, "on_workflow_error")
        
        try:
            manager = self._get_websocket_manager()
            message = {
                "type": "workflow_error",
                "task_id": str(workflow.trigger_event.task_id),
                "node": node.name if node else None,
                "error": self._serialize_result(error),
                "is_end": False,
                "is_error": True
            }
            await manager.send_to_task(workflow.trigger_event.task_id, message)
        except Exception as e:
            logger.error(f"发送 workflow_error 消息到 websocket 失败: {e}")

    @override
    async def on_node_start(self, node: Node) -> None:
        try:
            manager = self._get_websocket_manager()
            message = {
                "type": "node_start",
                "task_id": str(node.workflow.trigger_event.task_id),
                "node": node.name,
                "is_end": False,
                "is_error": False
            }
            await manager.send_to_task(node.workflow.trigger_event.task_id, message)
        except Exception as e:
            logger.error(f"发送 node_start 消息到 websocket 失败: {e}")

    @override
    async def on_node_end(self, node: Node) -> None:
        try:
            manager = self._get_websocket_manager()
            message = {
                "type": "node_end",
                "task_id": str(node.workflow.trigger_event.task_id),
                "node": node.name,
                "is_end": False,
                "is_error": False
            }
            await manager.send_to_task(node.workflow.trigger_event.task_id, message)
        except Exception as e:
            logger.error(f"发送 node_end 消息到 websocket 失败: {e}")

    @override
    async def on_node_stream_output(self, node: Node, output: Any) -> None:
        workflow_result = WorkflowResult(result=output, is_end=False, is_error=False)
        
        if node.workflow.trigger_event.task_id in node.workflow.real_trigger_node.stream_queues:
            node.workflow.real_trigger_node.stream_queues[node.workflow.trigger_event.task_id].put_nowait(workflow_result)
        
        try:
            manager = self._get_websocket_manager()
            message = {
                "type": "node_stream_output",
                "task_id": str(node.workflow.trigger_event.task_id),
                "node": node.name,
                "output": self._serialize_result(output),
                "is_end": False,
                "is_error": False
            }
            await manager.send_to_task(node.workflow.trigger_event.task_id, message)
        except Exception as e:
            logger.error(f"发送 node_stream_output 消息到 websocket 失败: {e}")