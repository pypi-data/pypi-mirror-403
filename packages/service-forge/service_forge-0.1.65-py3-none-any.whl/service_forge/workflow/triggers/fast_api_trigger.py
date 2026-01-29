from __future__ import annotations
import traceback
import uuid
import asyncio
import json
from loguru import logger
from service_forge.workflow.trigger import Trigger
from typing import AsyncIterator, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from service_forge.workflow.port import Port
from service_forge.utils.default_type_converter import type_converter
from service_forge.api.routers.websocket.websocket_manager import websocket_manager
from service_forge.workflow.trigger_event import TriggerEvent
from fastapi import HTTPException
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToJson
from opentelemetry import context as otel_context_api

class FastAPITrigger(Trigger):
    DEFAULT_INPUT_PORTS = [
        Port("app", FastAPI),
        Port("path", str),
        Port("method", str),
        Port("data_type", type),
        Port("is_stream", bool),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("trigger", bool),
        Port("user_id", str),
        Port("token", str),
        Port("data", Any),
        Port("path_params", dict),
    ]

    def __init__(self, name: str):
        super().__init__(name)
        self.events = {}
        self.is_setup_route = False
        self.task_contexts: dict[uuid.UUID, otel_context_api.Context] = {}
        self.app = None
        self.route_path = None
        self.route_method = None

    @staticmethod
    def serialize_result(result: Any):
        if isinstance(result, Message):
            return MessageToJson(result, preserving_proto_field_name=True)
        return result

    def _normalize_result_or_raise(self, result: Any):
        # TODO: 检查合并
        if hasattr(result, "is_error") and hasattr(result, "result"):
            if result.is_error:
                if isinstance(result.result, HTTPException):
                    raise result.result
                raise HTTPException(status_code=500, detail=str(result.result))
            return self.serialize_result(result.result)

        if isinstance(result, HTTPException):
            raise result
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=str(result))

        return self.serialize_result(result)

    async def handle_request(
        self,
        request: Request,
        data_type: type,
        extract_data_fn: callable[[Request], dict],
        is_stream: bool,
        path_params: Optional[dict] = None,
    ):
        task_id = uuid.uuid4()
        self.result_queues[task_id] = asyncio.Queue()

        # parse trace context
        trace_ctx = otel_context_api.get_current()
        self.task_contexts[task_id] = trace_ctx

        body_data = await extract_data_fn(request)
        # Merge path parameters into body_data (path params take precedence)
        if path_params:
            body_data = {**body_data, **path_params}
        converted_data = data_type(**body_data)

        # TODO: remove this
        # client_id = (
        #     body_data.get("client_id")
        #     or request.query_params.get("client_id")
        #     or request.headers.get("X-Client-ID")
        # )
        # if client_id:
        #     workflow_name = getattr(self.workflow, "name", "Unknown")
        #     steps = len(self.workflow.nodes) if hasattr(self.workflow, "nodes") else 1
        #     websocket_manager.create_task_with_client(task_id, client_id, workflow_name, steps)

        # trigger_queue with trace_context, used in _run()
        logger.info(f'user_id {getattr(request.state, "user_id", None)} token {getattr(request.state, "auth_token", None)}')

        self.trigger_queue.put_nowait({
            "id": task_id,
            "user_id": getattr(request.state, "user_id", None),
            "token": getattr(request.state, "auth_token", None),
            "data": converted_data,
            "trace_context": trace_ctx,
            "path_params": path_params,
        })

        if is_stream:
            self.stream_queues[task_id] = asyncio.Queue()

            async def generate_sse():
                try:
                    while True:
                        item = await self.stream_queues[task_id].get()

                        if getattr(item, "is_error", False):
                            yield f"event: error\ndata: {json.dumps({'detail': str(item.result)})}\n\n"
                            break

                        if getattr(item, "is_end", False):
                            break

                        # TODO: modify
                        serialized = self.serialize_result(item.result)
                        data = serialized if isinstance(serialized, str) else json.dumps(serialized)
                        yield f"data: {data}\n\n"

                except Exception as e:
                    yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"
                finally:
                    self.stream_queues.pop(task_id, None)

                    if task_id in self.stream_queues:
                        del self.stream_queues[task_id]
                    if task_id in self.result_queues:
                        del self.result_queues[task_id]
            
            return StreamingResponse(
                generate_sse(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # 非流式：等待结果
        result = await self.result_queues[task_id].get()
        self.result_queues.pop(task_id, None)
        return self._normalize_result_or_raise(result)

    def _setup_route(self, app: FastAPI, path: str, method: str, data_type: type, is_stream: bool) -> None:
        async def get_data(request: Request) -> dict:
            return dict(request.query_params)

        async def body_data(request: Request) -> dict:
            raw = await request.body()
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))

        extractor = get_data if method == "GET" else body_data

        async def handler(request: Request):
            # Get path parameters from FastAPI request
            # request.path_params is always available in FastAPI and contains path parameters
            path_params = dict(request.path_params)
            return await self.handle_request(request, data_type, extractor, is_stream, path_params)

        # Save route information for cleanup
        self.app = app
        self.route_path = path
        self.route_method = method.upper()

        if method == "GET":
            app.get(path)(handler)
        elif method == "POST":
            app.post(path)(handler)
        elif method == "PUT":
            app.put(path)(handler)
        elif method == "DELETE":
            app.delete(path)(handler)
        else:
            raise ValueError(f"Invalid method {method}")

    async def _run(
        self, 
        app: FastAPI, 
        path: str, 
        method: str, 
        data_type: type, 
        is_stream: bool = False,
    ) -> AsyncIterator[bool]:
        if not self.is_setup_route:
            self._setup_route(app, path, method, data_type, is_stream)
            self.is_setup_route = True

        while True:
            try:
                trigger = await self.trigger_queue.get()

                # TODO: remove this?
                if trace_ctx := trigger.get("trace_context"):
                    self.task_contexts[trigger["id"]] = trace_ctx

                logger.info(f"FastAPITrigger._run: user_id {trigger['user_id']} token {trigger['token']} data {trigger['data']} path_params {trigger['path_params']}")
                self.prepare_output_edges(self.get_output_port_by_name('user_id'), trigger['user_id'])
                self.prepare_output_edges(self.get_output_port_by_name('token'), trigger['token'])
                self.prepare_output_edges(self.get_output_port_by_name('data'), trigger['data'])
                self.prepare_output_edges(self.get_output_port_by_name('path_params'), trigger['path_params'])
                event = TriggerEvent(self, trigger['id'], trigger['trace_context'], trigger['user_id'])
                self.trigger(event)
                yield event
            except Exception as e:
                traceback.print_exc()
                logger.error(f"Error in FastAPITrigger._run: {e}")
                continue

    async def _stop(self) -> AsyncIterator[bool]:
        if self.is_setup_route:
            # Remove the route from the app
            if self.app and self.route_path and self.route_method:
                # Find and remove matching route
                routes_to_remove = []
                for route in self.app.routes:
                    if hasattr(route, "path") and hasattr(route, "methods"):
                        if route.path == self.route_path and self.route_method in route.methods:
                            routes_to_remove.append(route)
                
                # Remove found routes
                for route in routes_to_remove:
                    try:
                        self.app.routes.remove(route)
                        logger.info(f"Removed route {self.route_method} {self.route_path} from FastAPI app")
                    except ValueError:
                        logger.warning(f"Route {self.route_method} {self.route_path} not found in app.routes")
            
            # Reset route information
            self.app = None
            self.route_path = None
            self.route_method = None
            self.is_setup_route = False