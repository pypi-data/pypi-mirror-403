from __future__ import annotations
import uuid
import asyncio
import json
from loguru import logger
from service_forge.workflow.trigger import Trigger
from service_forge.workflow.trigger_event import TriggerEvent
from typing import AsyncIterator, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from service_forge.workflow.port import Port
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToJson

class WebSocketAPITrigger(Trigger):
    DEFAULT_INPUT_PORTS = [
        Port("app", FastAPI),
        Port("path", str),
        Port("data_type", type),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("trigger", bool),
        Port("client_id", uuid.UUID),
        Port("user_id", str),
        Port("token", str),
        Port("data", Any),
    ]

    def __init__(self, name: str):
        super().__init__(name)
        self.events = {}
        self.is_setup_websocket = False

    @staticmethod
    def serialize_result(result: Any):
        if isinstance(result, Message):
            return MessageToJson(
                result,
                preserving_proto_field_name=True
            )
        return result

    async def send_message(
        self,
        websocket: WebSocket,
        type: str,
        task_id: uuid.UUID,
        data: Any,
    ):
        # Check if WebSocket is closed before sending
        if websocket.client_state != WebSocketState.CONNECTED:
            logger.warning(f"WebSocket is closed, cannot send message for task {task_id}")
            return
        
        message = {
            "type": type,
            "task_id": str(task_id),
            "data": data
        }
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to WebSocket for task {task_id}: {e}")

    async def handle_stream_output(
        self,
        websocket: WebSocket,
        task_id: uuid.UUID,
    ):
        try:
            while True:
                item = await self.stream_queues[task_id].get()

                if item.is_error:
                    await self.send_message(websocket, "stream_error", task_id, str(item.result))
                    break
                
                if item.is_end:
                    # Stream ended, send final result if available
                    if item.result is not None:
                        serialized = self.serialize_result(item.result)
                        if isinstance(serialized, str):
                            try:
                                data = json.loads(serialized)
                            except json.JSONDecodeError:
                                data = serialized
                        else:
                            data = serialized
                        await self.send_message(websocket, "stream_end", task_id, data)
                    else:
                        await self.send_message(websocket, "stream_end", task_id, None)
                    break

                # Send stream data
                serialized = self.serialize_result(item.result)
                if isinstance(serialized, str):
                    try:
                        data = json.loads(serialized)
                    except json.JSONDecodeError:
                        data = serialized
                else:
                    data = serialized
                
                await self.send_message(websocket, "stream", task_id, data)
        except Exception as e:
            logger.error(f"Error handling stream output for task {task_id}: {e}")
            await self.send_message(websocket, "stream_error", task_id, str(e))
        finally:
            if task_id in self.stream_queues:
                del self.stream_queues[task_id]

    async def handle_websocket_message(
        self,
        websocket: WebSocket,
        data_type: type,
        client_id: str,
        message_data: dict,
    ):
        task_id = uuid.uuid4()
        # self.result_queues[task_id] = asyncio.Queue()
        self.stream_queues[task_id] = asyncio.Queue()

        logger.info(f'user_id {getattr(websocket.state, "user_id", None)} token {getattr(websocket.state, "auth_token", None)}')

        if data_type is Any:
            converted_data = message_data
        else:
            try:
                # TODO: message_data is Message, need to convert to dict
                converted_data = data_type(**message_data)
            except Exception as e:
                error_msg = {"error": f"Failed to convert data: {str(e)}"}
                await websocket.send_text(json.dumps(error_msg))
                return

        # Always start background task to handle stream output
        asyncio.create_task(self.handle_stream_output(websocket, task_id))

        self.trigger_queue.put_nowait({
            "id": task_id,
            "user_id": getattr(websocket.state, "user_id", None),
            "token": getattr(websocket.state, "auth_token", None),
            "data": converted_data,
            "client_id": client_id,
        })

        # The stream handler will send all messages including stream_end when workflow completes

    def _setup_websocket(self, app: FastAPI, path: str, data_type: type) -> None:
        async def websocket_handler(websocket: WebSocket):
            websocket.state.user_id = websocket.headers.get("X-User-ID") or "0"
            websocket.state.auth_token = websocket.headers.get("X-User-Token") or ""
            logger.info(f'user_id {websocket.state.user_id} token {websocket.state.auth_token}')
            # Authenticate WebSocket connection before accepting
            # Get trusted_domain from app.state if available
            # trusted_domain = getattr(app.state, "trusted_domain", "ring.shiweinan.com")
            # enable_auth = getattr(app.state, "enable_auth_middleware", True)
            
            # if enable_auth:
            #     await authenticate_websocket(websocket, trusted_domain)
            # else:
            #     # If auth is disabled, set default values
            #     websocket.state.user_id = websocket.headers.get("X-User-ID", "0")
            #     websocket.state.auth_token = websocket.headers.get("X-User-Token")
            
            await websocket.accept()

            client_id = uuid.uuid4()
            
            try:
                while True:
                    data = await websocket.receive()
                    try:
                        # message = json.loads(data)
                        # Handle the message and trigger workflow
                        await self.handle_websocket_message(
                            websocket,
                            data_type,
                            client_id,
                            data
                        )
                    except json.JSONDecodeError:
                        error_msg = {"error": "Invalid JSON format"}
                        await websocket.send_text(json.dumps(error_msg))
                    except Exception as e:
                        logger.error(f"Error handling websocket message: {e}")
                        error_msg = {"error": str(e)}
                        await websocket.send_text(json.dumps(error_msg))
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")

            print("DISCONNECTED")

        app.websocket(path)(websocket_handler)

    async def _run(self, app: FastAPI, path: str, data_type: type) -> AsyncIterator[bool]:
        if not self.is_setup_websocket:
            self._setup_websocket(app, path, data_type)
            self.is_setup_websocket = True

        while True:
            try:
                trigger = await self.trigger_queue.get()
                self.prepare_output_edges(self.get_output_port_by_name('user_id'), trigger['user_id'])
                self.prepare_output_edges(self.get_output_port_by_name('token'), trigger['token'])
                self.prepare_output_edges(self.get_output_port_by_name('data'), trigger['data'])
                self.prepare_output_edges(self.get_output_port_by_name('client_id'), trigger['client_id'])
                event = TriggerEvent(self, trigger['id'], None, trigger['user_id'])
                self.trigger(event)
                yield event
            except Exception as e:
                logger.error(f"Error in WebSocketAPITrigger._run: {e}")
                continue

    async def _stop(self) -> AsyncIterator[bool]:
        pass