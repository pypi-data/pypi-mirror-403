from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from uuid import UUID


class FeedbackCreate(BaseModel):
    """创建反馈的请求模型"""
    trace_id: str = Field(..., description="trace_id")
    service_name: Optional[str] = Field(None, description="服务名称（可选，如果未提供会从 trace API 获取）")
    workflow_name: Optional[str] = Field(None, description="工作流名称（可选，如果未提供会从 trace API 获取）")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分 (1-5)")
    comment: Optional[str] = Field(None, description="用户评论")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict, description="额外的元数据")


class FeedbackResponse(BaseModel):
    """反馈响应模型"""
    feedback_id: str = Field(..., description="反馈ID")
    service_name: Optional[str] = Field(None, description="服务名称")
    workflow_name: str = Field(..., description="工作流名称")
    trace_id: Optional[str] = Field(None, description="trace_id")
    rating: Optional[int] = Field(None, description="评分")
    comment: Optional[str] = Field(None, description="用户评论")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(..., description="创建时间")


class FeedbackListResponse(BaseModel):
    """反馈列表响应模型"""
    total: int = Field(..., description="总数")
    feedbacks: list[FeedbackResponse] = Field(..., description="反馈列表")
