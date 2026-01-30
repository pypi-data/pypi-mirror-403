from __future__ import annotations
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from service_forge.workflow.trigger import Trigger
from service_forge.workflow.trigger_event import TriggerEvent
from typing import AsyncIterator
import uuid

class OnceTrigger(Trigger):
    DEFAULT_INPUT_PORTS = [
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("trigger", bool),
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self) -> AsyncIterator[bool]:
        event = TriggerEvent(self, uuid.uuid4(), None, "")
        self.trigger(event)
        yield event

    async def _stop(self) -> AsyncIterator[bool]:
        pass