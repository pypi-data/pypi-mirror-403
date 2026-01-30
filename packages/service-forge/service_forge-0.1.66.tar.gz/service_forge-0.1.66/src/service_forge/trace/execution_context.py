from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field, replace
from typing import Any, Iterator, Mapping

from loguru import logger
from opentelemetry.context import Context as OtelContext
from opentelemetry.trace import Span

"""
ExecutionContext helper for tracing/logging/state propagation.

Usage constraints (async-aware):
- Entrypoints must call set_current_context/use_execution_context so spawned coroutines inherit the context; create tasks after setting it.
- ContextVar does not flow into run_in_executor/thread pools; set_current_context manually in threads if needed.
- Use with_state to copy + mutate state; instances are immutable to avoid concurrent writes.
- Logger/span are shared references; set a new ExecutionContext when switching spans to prevent cross-task leakage.
- State payload is masked for sensitive keys and capped at ~4KB after JSON serialization; oversize payload raises ValueError.
"""

STATE_SIZE_LIMIT_BYTES = 4096
SENSITIVE_KEYS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "credential",
    "cookie",
)


def _mask_sensitive_value(key: str, value: Any) -> Any:
    lower_key = key.lower()
    if any(sensitive in lower_key for sensitive in SENSITIVE_KEYS):
        return "***"
    return value


def _validate_state_payload(state: Mapping[str, Any]) -> None:
    try:
        payload = json.dumps(state, default=str)
    except Exception:
        payload = str(state)
    if len(payload.encode("utf-8")) > STATE_SIZE_LIMIT_BYTES:
        raise ValueError(
            f"ExecutionContext state exceeds {STATE_SIZE_LIMIT_BYTES} bytes after serialization; "
            "store a compact summary instead of raw payloads."
        )


@dataclass(frozen=True)
class ExecutionContext:
    """Shared execution-scoped data passed across API, workflow, and node layers."""

    trace_context: OtelContext | None = None
    span: Span | None = None
    logger = logger
    state: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def with_state(self, **updates: Any) -> ExecutionContext:
        merged_state = {
            key: _mask_sensitive_value(key, value)
            for key, value in {**self.state, **updates}.items()
        }
        _validate_state_payload(merged_state)
        return replace(self, state=merged_state)


current_context: ContextVar[ExecutionContext | None] = ContextVar(
    "current_execution_context",
    default=None,
)


def get_current_context(
    default: ExecutionContext | None = None,
) -> ExecutionContext | None:
    context = current_context.get()
    if context is None:
        return default
    return context


def set_current_context(context: ExecutionContext | None) -> Token:
    return current_context.set(context)


def reset_current_context(token: Token) -> None:
    current_context.reset(token)


@contextmanager
def use_execution_context(context: ExecutionContext) -> Iterator[ExecutionContext]:
    token = set_current_context(context)
    try:
        yield context
    finally:
        reset_current_context(token)
