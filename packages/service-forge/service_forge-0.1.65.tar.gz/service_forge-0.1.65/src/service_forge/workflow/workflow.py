from __future__ import annotations
import traceback
import asyncio
import uuid
from typing import Any, AsyncIterator, Awaitable, Callable

from loguru import logger
from opentelemetry import trace

from ..db.database import DatabaseManager
from ..trace.execution_context import (
    ExecutionContext,
    get_current_context,
    reset_current_context,
    set_current_context,
)
from ..trace.trace_scope import workflow_span, node_span, node_output_attributes
from .edge import Edge
from .node import Node
from .port import Port
from .trigger_event import TriggerEvent
from .trigger import Trigger
from ..db.database import DatabaseManager
from .workflow_clone import workflow_clone
from .workflow_callback import WorkflowCallback, BuiltinWorkflowCallback, CallbackEvent
from .workflow_config import WorkflowConfig
from .context import Context
from ..service_config import EntryConfig
from ..llm import SfLLM

class Workflow:
    def __init__(
        self,
        id: uuid.UUID,
        config: WorkflowConfig,
        entry_config: EntryConfig,
        nodes: list[Node],
        input_ports: list[Port],
        output_ports: list[Port],
        _handle_stream_output: Callable[[str, AsyncIterator[str]], Awaitable[None]] = None, # deprecated
        _handle_query_user: Callable[[str, str], Awaitable[str]] = None,
        database_manager: DatabaseManager = None,
        llm: SfLLM = None,
        callbacks: list[WorkflowCallback] = [],
        debug_version: bool = False,    # 是否为debug过程中的临时版本

        # for run
        trigger_event: TriggerEvent = None,
        # task_id: uuid.UUID = None,
        real_trigger_node: Trigger = None,

        # global variables
        global_context: Context = None,
    ) -> None:
        self.id = id
        self.config = config
        self.entry_config = entry_config
        self.nodes = nodes
        self.ready_nodes: list[Node] = []
        self.input_ports = input_ports
        self.output_ports = output_ports
        self._handle_stream_output = _handle_stream_output
        self._handle_query_user = _handle_query_user
        self.database_manager = database_manager
        self.llm = llm
        self.run_semaphore = asyncio.Semaphore(config.max_concurrent_runs)
        self.callbacks = callbacks
        self.debug_version = debug_version
        self.trigger_event = trigger_event
        # self.task_id = task_id
        self.real_trigger_node = real_trigger_node
        self.global_context = global_context
        self._validate()
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def version(self) -> str:
        return self.config.version
    
    @property
    def description(self) -> str:
        return self.config.description

    def register_callback(self, callback: WorkflowCallback) -> None:
        self.callbacks.append(callback)

    def unregister_callback(self, callback: WorkflowCallback) -> None:
        self.callbacks.remove(callback)

    async def call_callbacks(self, callback_type: CallbackEvent, *args, **kwargs) -> None:
        for callback in self.callbacks:
            if callback_type == CallbackEvent.ON_WORKFLOW_START:
                await callback.on_workflow_start(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_WORKFLOW_END:
                await callback.on_workflow_end(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_WORKFLOW_ERROR:
                await callback.on_workflow_error(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_NODE_START:
                await callback.on_node_start(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_NODE_END:
                await callback.on_node_end(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_NODE_STREAM_OUTPUT:
                await callback.on_node_stream_output(*args, **kwargs)

    def add_nodes(self, nodes: list[Node]) -> None:
        for node in nodes:
            node.workflow = self
        self.nodes.extend(nodes)

    def remove_nodes(self, nodes: list[Node]) -> None:
        for node in nodes:
            self.nodes.remove(node)

    def load_config(self) -> None: ...

    def _validate(self) -> None:
        # DAG
        ...

    def get_input_port_by_name(self, name: str) -> Port:
        for input_port in self.input_ports:
            if input_port.name == name:
                return input_port
        return None

    def get_output_port_by_name(self, name: str) -> Port:
        for output_port in self.output_ports:
            if output_port.name == name:
                return output_port
        return None

    def get_trigger_node(self) -> Trigger:
        trigger_nodes = [node for node in self.nodes if isinstance(node, Trigger)]
        if not trigger_nodes:
            raise ValueError("No trigger nodes found in workflow.")
        if len(trigger_nodes) > 1:
            raise ValueError("Multiple trigger nodes found in workflow.")
        return trigger_nodes[0]

    async def stop(self):
        trigger = self.get_trigger_node()
        await trigger._stop()

    def trigger(self, trigger_name: str, assigned_task_id: uuid.UUID | None, **kwargs) -> uuid.UUID:
        trigger = self.get_trigger_node()
        task_id = assigned_task_id or uuid.uuid4()
        for key, value in kwargs.items():
            trigger.prepare_output_edges(key, value)
        task = asyncio.create_task(self._run(task_id, trigger))
        return task_id

    async def handle_node_stream_output(
        self,
        node: Node,
        stream: AsyncIterator[Any],
    ) -> None:
        async for data in stream:
            await self.call_callbacks(CallbackEvent.ON_NODE_STREAM_OUTPUT, node=node, output=data)

    # TODO: refactor this
    async def handle_query_user(self, node_name: str, prompt: str) -> Awaitable[str]:
        return await asyncio.to_thread(input, f"[{node_name}] {prompt}: ")
    
    def _clone(self, event: TriggerEvent, trigger_node: Trigger) -> Workflow:
        return workflow_clone(self, event, trigger_node)

    async def _run_node_with_callbacks(self, node: Node) -> bool:
        await self.call_callbacks(CallbackEvent.ON_NODE_START, node=node)
        
        try:
            result = node.run()
            if hasattr(result, '__anext__'):
                await self.handle_node_stream_output(node, result)
            elif asyncio.iscoroutine(result):
                await result
        except Exception as e:
            await self.call_callbacks(CallbackEvent.ON_WORKFLOW_ERROR, workflow=self, node=node, error=e)
            logger.error(f"Error when running node {node.name}: {traceback.format_exc()}, task_id: {self.trigger_event.task_id}")
            return False
        finally:
            await self.call_callbacks(CallbackEvent.ON_NODE_END, node=node)
        return True

    async def _run_node_with_span(self, node: Node) -> bool:
        async with node_span(
            tracer=trace.get_tracer("service_forge.node"),
            node=node,
        ) as span:
            result = await self._run_node_with_callbacks(node)
            # node_output_attributes(span, node)
            return result

    async def run_after_trigger(self) -> Any:
        async with workflow_span(
            tracer=trace.get_tracer("service_forge.workflow"),
            workflow=self,
            parent_context=self.trigger_event.trace_context,
        ):
            logger.info(f"Running workflow: {self.name}")

            await self.call_callbacks(CallbackEvent.ON_WORKFLOW_START, workflow=self)

            self.ready_nodes = []
            for edge in self.get_trigger_node().output_edges:
                edge.end_port.trigger()

            for input_port in self.input_ports:
                if input_port.value is not None:
                    input_port.port.node.fill_input(input_port.port, input_port.value)

            for node in self.nodes:
                for key in node.AUTO_FILL_INPUT_PORTS:
                    if key[0] not in [edge.end_port.name for edge in node.input_edges]:
                        node.fill_input_by_name(key[0], key[1])

            while self.ready_nodes:
                nodes = self.ready_nodes.copy()
                self.ready_nodes = []

                tasks = []
                for node in nodes:
                    tasks.append(asyncio.create_task(self._run_node_with_span(node)))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
                        return
                        # raise result
                    elif result is False:
                        logger.error(f"Node execution failed, stopping workflow: {nodes[i].name}")
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
                        return
                        # raise RuntimeError(f"Workflow stopped due to node execution failure: {nodes[i].name}")

            if len(self.output_ports) > 0:
                if len(self.output_ports) == 1:
                    if self.output_ports[0].is_prepared:
                        result = self.output_ports[0].value
                    else:
                        result = None
                else:
                    result = {}
                    for port in self.output_ports:
                        if port.is_prepared:
                            result[port.name] = port.value
                await self.call_callbacks(CallbackEvent.ON_WORKFLOW_END, workflow=self, output=result)
            else:
                await self.call_callbacks(CallbackEvent.ON_WORKFLOW_END, workflow=self, output=None)

    async def _run(self, event: TriggerEvent, trigger_node: Trigger) -> None:
        async with self.run_semaphore:
            try:
                new_workflow = self._clone(event, trigger_node)

                result = await new_workflow.run_after_trigger()

                if event.task_id in trigger_node.result_queues:
                    trigger_node.result_queues[event.task_id].put_nowait(result)

                for node in new_workflow.nodes:
                    await node.clear()

            except Exception as e:
                traceback.print_exc()
                logger.error(
                    f"Error running workflow: {e}",
                    exc_info=True,
                )
                await self.call_callbacks(
                    CallbackEvent.ON_WORKFLOW_ERROR,
                    workflow=self,
                    node=None,
                    error=e,
                )
                return

    async def run(self):
        tasks = []
        trigger = self.get_trigger_node()

        # event is TriggerEvent
        async for event in trigger.run():
            if isinstance(event, TriggerEvent):
                tasks.append(asyncio.create_task(self._run(event, trigger)))
            else:
                logger.error(f"Unexpected event type: {type(event)}")

        if tasks:
            await asyncio.gather(*tasks)