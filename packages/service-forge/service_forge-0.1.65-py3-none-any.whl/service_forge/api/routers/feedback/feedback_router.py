import os
import httpx
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Request
from loguru import logger
from typing import Optional
from datetime import datetime

from service_forge.model.feedback import FeedbackCreate, FeedbackResponse, FeedbackListResponse
from service_forge.storage.feedback_storage import feedback_storage
from service_forge.db.database import create_database_manager
from service_forge.current_service import get_service

router = APIRouter(prefix="/sdk/feedback", tags=["feedback"])

def _get_feedback_api_base():
    _service = get_service()
    if not _service:
        return None
    if not _service.config.feedback:
        return None
    return _service.config.feedback.api_url

def _get_feedback_api_timeout():
    _service = get_service()
    if not _service:
        return 10
    if not _service.config.feedback:
        return 10
    return _service.config.feedback.api_timeout

async def fetch_trace_info_from_trace(trace_id: str) -> dict:
    """
    从 trace API 获取 trace 的完整信息（service_name 和 workflow_name）

    Args:
        trace_id: trace ID

    Returns:
        包含 service_name 和 workflow_name 的字典
    """
    trace_service_url = _get_feedback_api_base()
    if not trace_service_url:
        logger.debug("未配置 trace service URL，跳过从 trace 获取信息")
        return {}

    # 使用新的 trace info API 端点，无需提供服务名
    trace_info_url = f"{trace_service_url}/sdk/trace/info"
    timeout = _get_feedback_api_timeout()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                trace_info_url,
                json={"trace_id": trace_id}
            )
            response.raise_for_status()
            data = response.json()

            result = {}
            if data.get("service_name"):
                result["service_name"] = data.get("service_name")
            if data.get("workflow_name"):
                result["workflow_name"] = data.get("workflow_name")

            if result:
                logger.info(f"从 trace API 获取信息成功: trace_id={trace_id}, service_name={result.get('service_name')}, workflow_name={result.get('workflow_name')}")
                return result
            else:
                logger.warning(f"trace API 返回中未找到有效信息: trace_id={trace_id}")
                return {}

    except httpx.TimeoutException:
        logger.warning(f"trace API 请求超时: {trace_info_url}")
        return {}
    except httpx.ConnectError as e:
        logger.warning(f"trace API 连接失败: {trace_info_url} - {e}")
        return {}
    except httpx.HTTPStatusError as e:
        logger.error(f"trace API 请求失败: status={e.response.status_code}")
        return {}
    except Exception as e:
        logger.error(f"从 trace API 获取信息异常: {type(e).__name__}: {e}")
        return {}

async def fetch_workflow_name_from_trace(trace_id: str) -> Optional[str]:
    """
    从 trace info API 获取 workflow_name

    Args:
        trace_id: 追踪ID

    Returns:
        workflow_name 或 None
    """
    trace_service_url = _get_feedback_api_base()
    if not trace_service_url:
        logger.debug("未配置 trace service URL，跳过从 trace 获取 workflow_name")
        return None

    # 使用新的 trace info API 端点，无需提供服务名
    trace_info_url = f"{trace_service_url}/sdk/trace/info"
    timeout = _get_feedback_api_timeout()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                trace_info_url,
                json={"trace_id": trace_id}
            )
            response.raise_for_status()
            data = response.json()

            # 从响应中提取 workflow_name
            workflow_name = data.get("workflow_name")
            if workflow_name:
                logger.info(f"从 trace API 获取 workflow_name 成功: trace_id={trace_id}, workflow_name={workflow_name}")
                return workflow_name
            else:
                logger.warning(f"trace API 返回中未找到 workflow_name: trace_id={trace_id}")
                return None

    except httpx.TimeoutException:
        logger.warning(f"从 trace API 获取 workflow_name 超时: {trace_info_url}")
        return None
    except httpx.ConnectError as e:
        logger.warning(f"从 trace API 获取 workflow_name 连接失败: {trace_info_url} - {e}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"从 trace API 获取 workflow_name 请求失败: status={e.response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"从 trace API 获取 workflow_name 异常: {type(e).__name__}: {e}")
        return None

async def forward_feedback_to_api(feedback_data: dict, user_id: Optional[str] = None, auth_token: Optional[str] = None, is_forwarded: bool = False):
    """
    将反馈数据转发到外部 API

    Args:
        feedback_data: 反馈数据字典
        user_id: 用户ID（从 request.state 获取）
        auth_token: 认证 token（从 request.state 获取）
        is_forwarded: 是否已经被转发过（用于防止递归转发）
    """
    # 如果已经被转发过，不再转发（防止递归转发）
    if is_forwarded:
        logger.debug(f"反馈已被转发过，跳过重复转发: feedback_id={feedback_data.get('feedback_id')}")
        return

    feedback_service_base_url = _get_feedback_api_base()
    if not feedback_service_base_url:
        logger.debug("未配置转发 API URL，跳过转发")
        return

    auto_send_url = f"{feedback_service_base_url}/sdk/feedback"
    timeout = _get_feedback_api_timeout()
    headers = {
        "Content-Type": "application/json",
        # 添加标记表示这是转发的反馈，防止递归转发
        "X-Feedback-Forwarded": "true",
    }

    # 从 request state 中添加用户认证信息
    if user_id:
        headers["X-User-ID"] = user_id
    if auth_token:
        headers["X-User-Token"] = auth_token

    try:
        # 处理 datetime 对象，转换为 ISO 格式字符串
        serializable_data = feedback_data.copy()
        if 'created_at' in serializable_data and serializable_data['created_at']:
            serializable_data['created_at'] = serializable_data['created_at'].isoformat()

        logger.info(f"\n{'='*60}")
        logger.info(f"转发反馈到外部 API")
        logger.info(f"URL: {auto_send_url}")
        logger.info(f"Method: POST")
        logger.info(f"Headers: {headers}")
        logger.info(f"Payload: {serializable_data}")
        logger.info(f"{'='*60}\n")

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.post(
                auto_send_url,
                json=serializable_data,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"✓ 反馈转发成功: feedback_id={feedback_data.get('feedback_id')}, URL={auto_send_url}, status={response.status_code}")
    except httpx.TimeoutException:
        logger.warning(f"✗ 反馈转发超时: {auto_send_url}")
    except httpx.ConnectError as e:
        logger.warning(f"✗ 反馈转发连接失败: {auto_send_url} - {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"✗ 反馈转发失败: URL={auto_send_url}, status={e.response.status_code}, detail={e.response.text}")
    except Exception as e:
        logger.error(f"✗ 反馈转发异常: URL={auto_send_url}, {type(e).__name__}: {e}")

async def fetch_feedbacks_from_external_api(trace_id: str) -> list[dict]:
    """
    从外部反馈服务 API 获取反馈数据

    Args:
        trace_id: 追踪ID

    Returns:
        反馈数据列表
    """
    feedback_service_base_url = _get_feedback_api_base()
    if not feedback_service_base_url:
        logger.debug("未配置外部反馈 API URL，跳过从外部 API 获取反馈")
        return []

    external_api_url = f"{feedback_service_base_url}/feedback/trace"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer readonly-admin-token"
    }
    timeout = _get_feedback_api_timeout()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                external_api_url,
                params={"trace_id": trace_id},
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            # 假设响应格式为 {"feedbacks": [...]} 或直接是列表
            if isinstance(data, dict) and "feedbacks" in data:
                feedbacks = data["feedbacks"]
            elif isinstance(data, list):
                feedbacks = data
            else:
                logger.warning(f"外部 API 返回格式未知: {data}")
                return []

            logger.info(f"从外部 API 获取反馈成功: trace_id={trace_id}, 条数={len(feedbacks)}")
            return feedbacks

    except httpx.TimeoutException:
        logger.warning(f"外部 API 请求超时: {external_api_url}")
        return []
    except httpx.ConnectError as e:
        logger.warning(f"外部 API 连接失败: {external_api_url} - {e}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"外部 API 请求失败: status={e.response.status_code}, detail={e.response.text}")
        return []
    except Exception as e:
        logger.error(f"外部 API 请求异常: {type(e).__name__}: {e}")
        return []

async def fetch_feedbacks_by_workflow_from_external_api(workflow_name: str) -> list[dict]:
    """
    从外部反馈服务 API 获取反馈数据 (按 workflow_name)

    Args:
        workflow_name: 工作流名称

    Returns:
        反馈数据列表
    """
    feedback_service_base_url = _get_feedback_api_base()
    if not feedback_service_base_url:
        logger.debug("未配置外部反馈 API URL，跳过从外部 API 获取反馈")
        return []

    external_api_url = f"{feedback_service_base_url}/feedback/workflow"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer readonly-admin-token"
    }
    timeout = _get_feedback_api_timeout()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                external_api_url,
                params={"workflow_name": workflow_name},
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "feedbacks" in data:
                feedbacks = data["feedbacks"]
            elif isinstance(data, list):
                feedbacks = data
            else:
                logger.warning(f"外部 API 返回格式未知: {data}")
                return []

            logger.info(f"从外部 API 获取反馈成功: workflow_name={workflow_name}, 条数={len(feedbacks)}")
            return feedbacks

    except httpx.TimeoutException:
        logger.warning(f"外部 API 请求超时: {external_api_url}")
        return []
    except httpx.ConnectError as e:
        logger.warning(f"外部 API 连接失败: {external_api_url} - {e}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"外部 API 请求失败: status={e.response.status_code}, detail={e.response.text}")
        return []
    except Exception as e:
        logger.error(f"外部 API 请求异常: {type(e).__name__}: {e}")
        return []

async def fetch_all_feedbacks_from_external_api() -> list[dict]:
    """
    从外部反馈服务 API 获取所有反馈数据

    Returns:
        反馈数据列表
    """
    feedback_service_base_url = _get_feedback_api_base()
    if not feedback_service_base_url:
        logger.debug("未配置外部反馈 API URL，跳过从外部 API 获取反馈")
        return []

    external_api_url = f"{feedback_service_base_url}/feedback/all"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer readonly-admin-token"
    }
    timeout = _get_feedback_api_timeout()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                external_api_url,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "feedbacks" in data:
                feedbacks = data["feedbacks"]
            elif isinstance(data, list):
                feedbacks = data
            else:
                logger.warning(f"外部 API 返回格式未知: {data}")
                return []

            logger.info(f"从外部 API 获取所有反馈成功: 条数={len(feedbacks)}")
            return feedbacks

    except httpx.TimeoutException:
        logger.warning(f"外部 API 请求超时: {external_api_url}")
        return []
    except httpx.ConnectError as e:
        logger.warning(f"外部 API 连接失败: {external_api_url} - {e}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"外部 API 请求失败: status={e.response.status_code}, detail={e.response.text}")
        return []
    except Exception as e:
        logger.error(f"外部 API 请求异常: {type(e).__name__}: {e}")
        return []

def merge_feedbacks(local_feedbacks: list[dict], external_feedbacks: list[dict]) -> list[dict]:
    """
    合并本地反馈和外部 API 反馈，去除重复

    Args:
        local_feedbacks: 本地数据库反馈列表
        external_feedbacks: 外部 API 反馈列表

    Returns:
        合并后的反馈列表（去重，按创建时间倒序）
    """
    # 使用 feedback_id 作为去重键
    seen_ids = set()
    merged = []

    # 先添加本地反馈
    for feedback in local_feedbacks:
        feedback_id = feedback.get("feedback_id")
        if feedback_id and feedback_id not in seen_ids:
            seen_ids.add(feedback_id)
            merged.append(feedback)

    # 再添加外部反馈（避免重复）
    for feedback in external_feedbacks:
        feedback_id = feedback.get("feedback_id")
        if feedback_id and feedback_id not in seen_ids:
            seen_ids.add(feedback_id)
            merged.append(feedback)

    # 按 created_at 倒序排列
    def sort_key(x):
        created_at = x.get("created_at")
        # 如果是 datetime 对象，直接返回
        if isinstance(created_at, datetime):
            return created_at
        # 如果是字符串，尝试转换为 datetime
        if isinstance(created_at, str):
            try:
                return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return datetime.min
        # 其他情况返回最小时间
        return datetime.min

    try:
        merged.sort(key=sort_key, reverse=True)
    except Exception as e:
        logger.warning(f"排序反馈失败: {e}")

    return merged

@router.post("/", response_model=FeedbackResponse, summary="创建工作流反馈")
async def create_feedback(feedback: FeedbackCreate, background_tasks: BackgroundTasks, request: Request):
    """
    创建工作流执行完成后的用户反馈
    - **trace_id**: trace_id
    - **service_name**: 服务名称（可选，如果未提供会从 trace API 获取）
    - **workflow_name**: 工作流名称（可选，如果未提供会从 trace API 获取）
    - **rating**: 可选的评分 (1-5)
    - **comment**: 可选的用户评论
    - **metadata**: 可选的额外元数据
    """
    try:
        service_name = feedback.service_name
        workflow_name = feedback.workflow_name

        # 如果 service_name 或 workflow_name 缺失，从 trace API 获取
        if not service_name or not workflow_name:
            logger.info(f"service_name 或 workflow_name 缺失，尝试从 trace API 获取: trace_id={feedback.trace_id}")
            trace_info = await fetch_trace_info_from_trace(feedback.trace_id)

            if not service_name and trace_info.get("service_name"):
                service_name = trace_info.get("service_name")
            if not workflow_name and trace_info.get("workflow_name"):
                workflow_name = trace_info.get("workflow_name")

        # 使用空字符串作为默认值
        if not service_name:
            logger.warning(f"无法获取 service_name: trace_id={feedback.trace_id}，使用空字符串")
            service_name = ""
        if not workflow_name:
            logger.warning(f"无法获取 workflow_name: trace_id={feedback.trace_id}，使用空字符串")
            workflow_name = ""

        # 保存到数据库
        feedback_data = await feedback_storage.create_feedback(
            trace_id=feedback.trace_id,
            service_name=service_name,
            workflow_name=workflow_name,
            rating=feedback.rating,
            comment=feedback.comment,
            metadata=feedback.metadata,
        )

        # 从 request.state 获取用户认证信息
        user_id = getattr(request.state, "user_id", None)
        auth_token = getattr(request.state, "auth_token", None)

        # 检查是否已经被转发过（从请求头中获取转发标记）
        is_forwarded = request.headers.get("X-Feedback-Forwarded") == "true"

        # 后台任务转发到外部 API (不阻塞响应)
        background_tasks.add_task(forward_feedback_to_api, feedback_data, user_id, auth_token, is_forwarded)

        return FeedbackResponse(**feedback_data)
    except Exception as e:
        logger.error(f"创建反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建反馈失败: {str(e)}")

@router.get("/{feedback_id}", response_model=FeedbackResponse, summary="获取单个反馈")
async def get_feedback(feedback_id: str):
    """
    根据反馈ID获取反馈详情

    - **feedback_id**: 反馈ID
    """
    feedback = await feedback_storage.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return FeedbackResponse(**feedback)

@router.get("/", response_model=FeedbackListResponse, summary="获取反馈列表")
async def list_feedbacks(
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=100, description="每页条目数（1-100）"),
    trace_id: Optional[str] = Query(None, description="按trace_id筛选"),
    workflow_name: Optional[str] = Query(None, description="按工作流名称筛选"),
):
    """
    获取反馈列表,支持按trace_id或工作流名称筛选，同时会从外部 API 合并数据

    - **page**: 页码，从1开始（默认1）
    - **page_size**: 每页条目数，1-100（默认20）
    - **trace_id**: 可选,按trace_id筛选（会同时查询外部 API）
    - **workflow_name**: 可选,按工作流名称筛选
    """
    try:
        # 获取本地反馈
        if trace_id:
            local_feedbacks = await feedback_storage.get_feedbacks_by_trace(trace_id)
            # 如果指定了 trace_id，同时从外部 API 获取反馈
            external_feedbacks = await fetch_feedbacks_from_external_api(trace_id)
            # 合并本地和外部反馈
            feedbacks = merge_feedbacks(local_feedbacks, external_feedbacks)
        elif workflow_name:
            local_feedbacks = await feedback_storage.get_feedbacks_by_workflow(workflow_name)
            # 如果指定了 workflow_name，同时从外部 API 获取反馈
            external_feedbacks = await fetch_feedbacks_by_workflow_from_external_api(workflow_name)
            # 合并本地和外部反馈
            feedbacks = merge_feedbacks(local_feedbacks, external_feedbacks)
        else:
            local_feedbacks = await feedback_storage.get_all_feedbacks()
            # 获取所有反馈时，同时从外部 API 获取反馈
            external_feedbacks = await fetch_all_feedbacks_from_external_api()
            # 合并本地和外部反馈
            feedbacks = merge_feedbacks(local_feedbacks, external_feedbacks)

        # 计算分页
        total = len(feedbacks)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_feedbacks = feedbacks[start_idx:end_idx]

        return FeedbackListResponse(
            total=total,
            feedbacks=[FeedbackResponse(**f) for f in paginated_feedbacks]
        )
    except Exception as e:
        logger.error(f"获取反馈列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取反馈列表失败: {str(e)}")

@router.delete("/{feedback_id}", summary="删除反馈")
async def delete_feedback(feedback_id: str):
    """
    删除指定的反馈

    - **feedback_id**: 反馈ID
    """
    success = await feedback_storage.delete_feedback(feedback_id)
    if not success:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return {"message": "反馈删除成功", "feedback_id": feedback_id}
