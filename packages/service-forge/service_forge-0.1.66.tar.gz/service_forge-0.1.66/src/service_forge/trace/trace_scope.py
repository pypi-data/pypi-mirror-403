from __future__ import annotations

import json
from contextlib import asynccontextmanager
from opentelemetry.trace import SpanKind, Tracer
from opentelemetry.context import Context
from opentelemetry.trace import Span
from service_forge.workflow.trigger_event import TriggerEvent
from .execution_context import (
    ExecutionContext,
    get_current_context,
    reset_current_context,
    set_current_context,
)

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
if TYPE_CHECKING:
    from service_forge.workflow.workflow import Workflow
    from service_forge.workflow.node import Node

@asynccontextmanager
async def workflow_span(
    tracer: Tracer,
    *,
    workflow: Workflow,
    parent_context: Context,
    span_kind: SpanKind = SpanKind.INTERNAL,
    extra_attributes: dict | None = None,
):
    with tracer.start_as_current_span(
        name=f"Workflow {workflow.name}",
        context=parent_context,
        kind=span_kind,
    ) as span:
        span.set_attribute("workflow.name", workflow.name)
        span.set_attribute("workflow.task_id", str(workflow.trigger_event.task_id))
        if extra_attributes:
            for k, v in extra_attributes.items():
                span.set_attribute(k, v)
        yield span

def _serialize_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    
    if isinstance(value, BaseModel):
        if hasattr(value, 'model_dump'):
            try:
                return json.dumps(value.model_dump(), default=str, ensure_ascii=False)
            except (TypeError, ValueError):
                pass
        elif hasattr(value, 'dict'):
            try:
                return json.dumps(value.dict(), default=str, ensure_ascii=False)
            except (TypeError, ValueError):
                pass
    
    try:
        return json.dumps(value, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)

@asynccontextmanager
async def node_span(
    tracer: Tracer,
    *,
    node: Node,
    span_kind: SpanKind = SpanKind.INTERNAL,
    extra_attributes: dict | None = None,
):
    with tracer.start_as_current_span(
        name=f"Node {node.name}",
        kind=span_kind,
    ) as span:
        span.set_attribute("node.name", node.name)
        node_input_attributes(span, node)

        if extra_attributes:
            for k, v in extra_attributes.items():
                span.set_attribute(k, v)
        
        try:
            yield span
        finally:
            node_output_attributes(span, node)

def node_input_attributes(span: Span, node: Node):
    for input_port in node.input_ports:
        value = None
        if input_port in node.input_variables:
            value = node.input_variables[input_port]
        elif input_port.is_prepared and input_port.value is not None:
            value = input_port.value
        
        if value is not None:
            attr_name = f"node.input.{input_port.name}"
            span.set_attribute(attr_name, _serialize_value(value))

def node_output_attributes(span: Span, node: Node):
    for output_port in node.output_ports:
        if output_port.value is not None:
            attr_name = f"node.output.{output_port.name}"
            span.set_attribute(attr_name, _serialize_value(output_port.value))