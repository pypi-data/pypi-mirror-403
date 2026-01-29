from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import IntEnum

# Type aliases
TraceId = str
SpanId = str
ParentSpanId = str

# Enums
class SpanKind(IntEnum):
    INTERNAL = 0
    SERVER = 1
    CLIENT = 2
    PRODUCER = 3
    CONSUMER = 4
    UNKNOWN = 5

class StatusCode(IntEnum):
    UNSET = 0
    OK = 1
    ERROR = 2

# Models
class Span(BaseModel):
    span_id: SpanId
    parent_span_id: ParentSpanId
    name: str
    kind: SpanKind
    timestamp: str
    duration_nano: int
    status_code: StatusCode
    service_name: str
    workflow_name: Optional[str] = None
    workflow_task_id: Optional[str] = None
    node_name: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class TraceListItem(BaseModel):
    trace_id: TraceId
    service_name: str
    workflow_name: Optional[str] = None
    workflow_task_id: Optional[str] = None
    timestamp: str
    duration_nano: int
    span_count: int
    has_error: bool
    status_code: StatusCode

class TraceDetail(BaseModel):
    trace_id: TraceId
    service_name: str
    service_version: Optional[str] = None
    device_platform: Optional[str] = None
    user_id: Optional[str] = None
    user_nickname: Optional[str] = None
    workflow_name: Optional[str] = None
    workflow_task_id: Optional[str] = None
    spans: List[Span]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    span_count: int
    has_error: bool

class GetTraceListParams(BaseModel):
    service_name: Optional[str] = None
    workflow_name: Optional[str] = None
    workflow_task_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    has_error: Optional[bool] = None

class GetTraceListResponse(BaseModel):
    traces: List[TraceListItem]
    total: int
    limit: int
    offset: int

class GetTraceDetailParams(BaseModel):
    trace_id: TraceId
    service_name: Optional[str] = None

class GetTraceDetailResponse(BaseModel):
    trace: TraceDetail

class TraceInfoResponse(BaseModel):
    """通过 trace_id 获取 trace 的服务名和工作流名"""
    trace_id: TraceId
    service_name: str
    workflow_name: Optional[str] = None
    workflow_task_id: Optional[str] = None