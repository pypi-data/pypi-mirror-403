import asyncio
from typing import AsyncIterator
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.http.test_sse_model import TestSSEModel
from a2a.server.agent_execution.context import RequestContext

class TestTraceBNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("input", str)
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("result", str)
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, input: str) -> None:
        print(f" + TestTraceBNode: {input} {self.get_trace_id()} {self.get_span_id()}")
        self.activate_output_edges('result', f"Input[{input}]")