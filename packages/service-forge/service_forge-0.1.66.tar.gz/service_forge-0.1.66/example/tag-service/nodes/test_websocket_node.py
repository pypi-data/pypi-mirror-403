import asyncio
from typing import AsyncIterator
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.http.test_sse_model import TestSSEModel
import uuid
from typing import Any

class TestWebSocketNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("message", Any),
        Port("client_id", uuid.UUID),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("result", str)
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, message: Any, client_id: uuid.UUID) -> AsyncIterator[str]:
        print("client_id", client_id, 'data', message)
        self.activate_output_edges('result', "Done!")