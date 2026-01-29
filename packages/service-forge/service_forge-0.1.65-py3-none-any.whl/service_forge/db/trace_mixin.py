from __future__ import annotations

from sqlalchemy import Column, String, event
from opentelemetry import trace
from typing import Optional, Any

def get_current_trace_ids() -> tuple[Optional[str], Optional[str]]:
    span = trace.get_current_span()
    if span:
        span_context = span.get_span_context()
        if span_context.is_valid:
            trace_id = format(span_context.trace_id, '032x')
            span_id = format(span_context.span_id, '016x')
            return trace_id, span_id
    return None, None


class TraceMixin:
    trace_id = Column(String(32), nullable=True, comment="OpenTelemetry trace_id")
    span_id = Column(String(16), nullable=True, comment="OpenTelemetry span_id")


def register_trace_events(base: Any) -> None:
    @event.listens_for(base, "before_insert", propagate=True)
    def receive_before_insert(mapper, connection, target):
        if hasattr(target, 'trace_id') and hasattr(target, 'span_id'):
            trace_id, span_id = get_current_trace_ids()
            if trace_id:
                target.trace_id = trace_id
            if span_id:
                target.span_id = span_id

    @event.listens_for(base, "before_update", propagate=True)
    def receive_before_update(mapper, connection, target):
        if hasattr(target, 'trace_id') and hasattr(target, 'span_id'):
            trace_id, span_id = get_current_trace_ids()
            if trace_id:
                target.trace_id = trace_id
            if span_id:
                target.span_id = span_id
