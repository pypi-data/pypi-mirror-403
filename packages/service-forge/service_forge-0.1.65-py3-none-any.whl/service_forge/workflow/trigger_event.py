from __future__ import annotations
import uuid
from opentelemetry.context import Context
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from service_forge.workflow.trigger import Trigger

class TriggerEvent:
    def __init__(
        self,
        trigger_node: Trigger,
        task_id: uuid.UUID,
        trace_context: Context,
        user_id: str,
    ):
        self.trigger_node = trigger_node
        self.task_id = task_id
        self.trace_context = trace_context
        self.user_id = user_id