from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from httpx import AsyncClient, HTTPStatusError
from loguru import logger

from service_forge.current_service import get_service
from service_forge.model.trace import (
    GetTraceListParams, GetTraceListResponse,
    GetTraceDetailParams, GetTraceDetailResponse, TraceListItem, TraceDetail, Span, StatusCode, SpanKind,
    TraceInfoResponse
)

trace_router = APIRouter(prefix="/sdk/trace", tags=["trace"])


def _get_signoz_api_base():
    _service = get_service()
    if not _service:
        return None
    if not _service.config.signoz:
        return None
    return _service.config.signoz.api_url

def _get_signoz_api_key():
    _service = get_service()
    if not _service:
        return None
    if not _service.config.signoz:
        return None
    return _service.config.signoz.api_key

@trace_router.post("/list", response_model=GetTraceListResponse)
async def get_trace_list(params: GetTraceListParams):
    """
    获取跟踪列表，调用外部SigNoz API
    """
    _service = get_service()
    internal_service_name = _service.name if _service else ""

    # 构建SQL查询语句
    where_clauses = []

    # 添加服务名过滤
    if params.service_name:
        where_clauses.append(f"resource_string_service$$name = '{params.service_name}'")
    elif internal_service_name:
        where_clauses.append(f"resource_string_service$$name = '{internal_service_name}'")

    # 添加工作流名过滤
    if params.workflow_name:
        where_clauses.append(f"attributes_string['workflow.name'] = '{params.workflow_name}'")

    # 添加工作流任务ID过滤
    if params.workflow_task_id:
        where_clauses.append(f"attributes_string['workflow.task_id'] = '{params.workflow_task_id}'")

    # 添加错误状态过滤
    if params.has_error is not None:
        where_clauses.append(f"has_error = {1 if params.has_error else 0}")

    # 组合WHERE子句
    where_part = ""
    if where_clauses:
        where_part = "WHERE " + " AND ".join(where_clauses)

    # 构建完整的查询
    # 注意：我们需要按trace_id分组，并计算每个trace的span_count
    # 同时获取最新的span信息（最大timestamp）
    query = f"""
    SELECT 
        trace_id,
        anyIf(resource_string_service$$name, resource_string_service$$name != '' AND resource_string_service$$name IS NOT NULL) as service_name,
        anyIf(attributes_string['workflow.name'], attributes_string['workflow.name'] != '' AND attributes_string['workflow.name'] IS NOT NULL) as workflow_name,
        anyIf(attributes_string['workflow.task_id'], attributes_string['workflow.task_id'] != '' AND attributes_string['workflow.task_id'] IS NOT NULL) as workflow_task_id,
        max(timestamp) as timestamp,
        sum(duration_nano) as duration_nano,
        count() as span_count,
        max(has_error) as has_error,
        max(status_code) as status_code
    FROM signoz_traces.distributed_signoz_index_v3
    {where_part}
    GROUP BY trace_id
    ORDER BY timestamp DESC
    LIMIT {params.limit or 100}
    OFFSET {params.offset or 0}
    """

    # 同时计算总数
    count_query = f"""
    SELECT COUNT(DISTINCT trace_id) as total
    FROM signoz_traces.distributed_signoz_index_v3
    {where_part}
    """

    async with AsyncClient() as client:
        try:
            current_time = datetime.now(timezone.utc)
            # 调用外部API
            response = await client.post(
                f"{_get_signoz_api_base()}/api/v5/query_range",
                headers={
                    "SIGNOZ-API-KEY": _get_signoz_api_key()
                },
                json={
                    "start": int(params.start_time or 0),
                    "end": int(params.end_time or (current_time.timestamp() * 1000)),
                    "requestType": "raw",
                    "compositeQuery": {
                        "queries": [
                            {
                                "type": "clickhouse_sql",
                                "spec": {
                                    "name": "query_1",
                                    "query": query,
                                    "disabled": False
                                }
                            },
                            {
                                "type": "clickhouse_sql",
                                "spec": {
                                    "name": "query_2",
                                    "query": count_query,
                                    "disabled": False
                                }
                            }
                        ]
                    }

                }
            )

            response.raise_for_status()  # 检查HTTP状态码

            # 假设外部API返回的数据格式与我们的响应模型一致
            # 如果不一致，需要在这里进行数据转换
            data = response.json()

            query_results = data["data"]["data"]["results"]
            query_1_result = None
            query_2_result = None
            for result in query_results:
                if result["queryName"] == "query_1":
                    query_1_result = result
                elif result["queryName"] == "query_2":
                    query_2_result = result

            traces = [
                TraceListItem(
                    trace_id=item["data"].get("trace_id", ""),
                    service_name=item["data"].get("service_name", params.service_name or internal_service_name),
                    workflow_name=item["data"].get("workflow_name", params.workflow_name or ""),
                    workflow_task_id=item["data"].get("workflow_task_id", params.workflow_task_id or ""),
                    timestamp=item["data"].get("timestamp", current_time.isoformat().replace("+00:00", "Z")),
                    duration_nano=item["data"].get("duration_nano", 0),
                    span_count=item["data"].get("span_count", 0),
                    has_error=item["data"].get("has_error", False),
                    status_code=item["data"].get("status_code", StatusCode.OK),
                )
                for item in query_1_result["rows"] or []
            ]

            # 转换为内部响应模型并返回
            return GetTraceListResponse(
                traces=traces,
                total=query_2_result["rows"][0]["data"].get("total", len(traces)),
                limit=params.limit or 100,
                offset=params.offset or 0,
            )

        except HTTPStatusError as e:
            # 处理HTTP错误
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            # 处理其他错误
            logger.error(e)
            raise HTTPException(status_code=500, detail=f"API处理失败: {str(e)}")


@trace_router.post("/detail", response_model=GetTraceDetailResponse)
async def get_trace_detail(params: GetTraceDetailParams):
    # 构建SQL查询语句
    where_clauses = [f"trace_id = '{params.trace_id}'"]

    # 添加服务名过滤
    if params.service_name:
        where_clauses.append(f"resource_string_service$$name = '{params.service_name}'")

    # 组合WHERE子句
    where_part = "WHERE " + " AND ".join(where_clauses)

    # 构建完整的查询获取所有span信息
    span_query = f"""
    SELECT 
        trace_id,
        span_id,
        parent_span_id,
        name,
        kind,
        timestamp,
        duration_nano,
        status_code,
        has_error,
        resource_string_service$$name as service_name,
        attributes_string as attributes_string
    FROM signoz_traces.distributed_signoz_index_v3
    {where_part}
    ORDER BY timestamp ASC
    """

    count_query = f"""
    SELECT 
        count(DISTINCT span_id) as total
    FROM signoz_traces.distributed_signoz_index_v3
    {where_part}
    """

    async with AsyncClient() as client:
        try:
            current_time = datetime.now(timezone.utc)
            # 调用外部API获取span数据
            response = await client.post(
                f"{_get_signoz_api_base()}/api/v5/query_range",
                headers={
                    "SIGNOZ-API-KEY": _get_signoz_api_key()
                },
                json={
                    "start": 0,  # 获取完整trace，不限制时间范围
                    "end": int(current_time.timestamp() * 1000),
                    "requestType": "raw",
                    "compositeQuery": {
                        "queries": [
                            {
                                "type": "clickhouse_sql",
                                "spec": {
                                    "name": "query_1",
                                    "query": span_query,
                                    "disabled": False
                                }
                            },
                            {
                                "type": "clickhouse_sql",
                                "spec": {
                                    "name": "query_2",
                                    "query": count_query,
                                    "disabled": False
                                }
                            },
                        ]
                    }
                }
            )
            response.raise_for_status()  # 检查HTTP状态码

            # 解析响应数据
            data = response.json()

            query_results = data["data"]["data"]["results"]
            query_1_result = None
            query_2_result = None
            for result in query_results:
                if result["queryName"] == "query_1":
                    query_1_result = result
                elif result["queryName"] == "query_2":
                    query_2_result = result

            _service = get_service()
            internal_service_name = _service.name if _service else ""

            spans = [
                Span(
                    span_id=item["data"].get("span_id", ""),
                    parent_span_id=item["data"].get("parent_span_id", ""),
                    name=item["data"].get("name", ""),
                    kind=item["data"].get("kind", SpanKind.UNKNOWN),
                    timestamp=item["data"].get("timestamp", current_time.isoformat().replace("+00:00", "Z")),
                    duration_nano=item["data"].get("duration_nano", 0),
                    status_code=item["data"].get("status_code", StatusCode.OK),
                    service_name=item["data"].get("service_name", params.service_name or internal_service_name),
                    workflow_name=item["data"].get("attributes_string", {}).get("workflow.name", ""),
                    workflow_task_id=item["data"].get("attributes_string", {}).get("workflow.task_id", ""),
                    node_name=item["data"].get("attributes_string", {}).get("node.name", ""),
                    attributes=item["data"].get("attributes_string", {}),
                )
                for item in query_1_result["rows"] or []
            ]

            has_error = False
            for row in (query_1_result["rows"] or []):
                if row["data"].get("has_error", False):
                    has_error = True
                    break

            service_name = ""
            for span in spans:
                if span.service_name:
                    service_name = span.service_name
                    if not span.parent_span_id:
                        break

            service_version = ""
            for span in spans:
                if span.attributes.get("service.version", ""):
                    service_version = span.attributes.get("service.version", "")
                    if not span.parent_span_id:
                        break

            workflow_name = ""
            for span in spans:
                if span.workflow_name:
                    workflow_name = span.workflow_name
                    if not span.parent_span_id:
                        break

            workflow_task_id = ""
            for span in spans:
                if span.workflow_task_id:
                    workflow_task_id = span.workflow_task_id
                    if not span.parent_span_id:
                        break

            device_platform = ""
            for span in spans:
                if span.attributes.get("device.platform", ""):
                    device_platform = span.attributes.get("device.platform", "")
                    if not span.parent_span_id:
                        break

            user_id = ""
            for span in spans:
                if span.attributes.get("user.id", ""):
                    user_id = span.attributes.get("user.id", "")
                    if not span.parent_span_id:
                        break

            user_nickname = ""
            for span in spans:
                if span.attributes.get("user.nickname", ""):
                    user_nickname = span.attributes.get("user.nickname", "")
                    if not span.parent_span_id:
                        break


            return GetTraceDetailResponse(
                trace=TraceDetail(
                    trace_id=params.trace_id,
                    service_name=service_name or params.service_name or internal_service_name, # 注入当前服务名
                    service_version=service_version,
                    device_platform=device_platform,
                    user_id=user_id,
                    user_nickname=user_nickname,
                    spans=spans,
                    start_time=spans[0].timestamp if spans else None,
                    end_time=spans[-1].timestamp if spans else None,
                    span_count=query_2_result["rows"][0]["data"].get("total", len(spans)),
                    has_error=has_error,
                    workflow_name=workflow_name,
                    workflow_task_id=workflow_task_id,
                )
            )



        except HTTPStatusError as e:
            # 处理HTTP错误
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            # 处理其他错误
            raise HTTPException(status_code=500, detail=f"API处理失败: {str(e)}")


@trace_router.post("/info", response_model=TraceInfoResponse)
async def get_trace_info(params: GetTraceDetailParams):
    """
    通过 trace_id 获取 trace 的服务名和工作流名
    无需提供服务名，系统会自动查询所有服务的 trace 信息
    """
    base_url = _get_signoz_api_base()
    api_key = _get_signoz_api_key()

    # base_url = "http://signoz.vps.shiweinan.com:37919"
    # api_key = "JlxvqRtNFu5yc4o1bRcJyzeolA96iWzAyQnBePRRJd0="

    if not base_url or not api_key:
        raise HTTPException(status_code=500, detail="SigNoz API 未配置")

    # 构建SQL查询语句，先查询所有信息，再在代码中处理
    where_clause = f"WHERE trace_id = '{params.trace_id}'"

    # 构建查询所有 span 的 SQL，获取所有信息
    span_query = f"""
    SELECT
        trace_id,
        span_id,
        resource_string_service$$name as service_name,
        attributes_string as attributes_string
    FROM signoz_traces.distributed_signoz_index_v3
    {where_clause}
    ORDER BY timestamp ASC
    LIMIT 100
    """

    async with AsyncClient() as client:
        try:
            current_time = datetime.now(timezone.utc)
            # 调用外部API获取span数据
            response = await client.post(
                f"{base_url}/api/v5/query_range",
                headers={
                    "SIGNOZ-API-KEY": api_key
                },
                json={
                    "start": 0,
                    "end": int(current_time.timestamp() * 1000),
                    "requestType": "raw",
                    "compositeQuery": {
                        "queries": [
                            {
                                "type": "clickhouse_sql",
                                "spec": {
                                    "name": "query_1",
                                    "query": span_query,
                                    "disabled": False
                                }
                            }
                        ]
                    }
                }
            )

            response.raise_for_status()
            data = response.json()

            query_results = data["data"]["data"]["results"]
            if not query_results or not query_results[0]["rows"]:
                raise HTTPException(status_code=404, detail=f"未找到 trace_id={params.trace_id} 的信息")

            # 从所有 span 中提取 trace 信息
            rows = query_results[0]["rows"]
            service_name = None
            workflow_name = None
            workflow_task_id = None
            service_counts = {}  # 统计非排除服务出现的次数
            first_excluded_service = None  # 记录返回结果中出现的第一个排除服务

            # 需要排除的服务（网关、前端等）
            excluded_services = {"entry", "secondbrain-frontend", "gateway"}

            # 第一遍：收集所有信息和服务统计
            for row in rows:
                row_data = row["data"]
                svc = row_data.get("service_name")
                if svc:
                    if svc in excluded_services:
                        # 记录返回结果中出现的第一个排除服务
                        if first_excluded_service is None:
                            first_excluded_service = svc
                    else:
                        service_counts[svc] = service_counts.get(svc, 0) + 1

                # 从 attributes_string 中提取 workflow 信息
                attributes = row_data.get("attributes_string", {})
                if not workflow_name and attributes.get("workflow.name"):
                    workflow_name = attributes.get("workflow.name")
                if not workflow_task_id and attributes.get("workflow.task_id"):
                    workflow_task_id = attributes.get("workflow.task_id")

                # 优先获取有 workflow.name 属性且不在排除列表中的 service_name
                if not service_name and workflow_name and svc and svc not in excluded_services:
                    service_name = svc

            # 如果还没有找到 service_name，按优先级选择：
            # 1. 非排除服务中出现次数最多的
            if not service_name and service_counts:
                service_name = max(service_counts.items(), key=lambda x: x[1])[0]

            # 2. 如果只有排除列表中的服务，用返回结果中出现的第一个
            if not service_name and first_excluded_service:
                service_name = first_excluded_service

            if not service_name:
                raise HTTPException(status_code=404, detail=f"未找到 trace_id={params.trace_id} 的服务信息")

            return TraceInfoResponse(
                trace_id=params.trace_id,
                service_name=service_name,
                workflow_name=workflow_name,
                workflow_task_id=workflow_task_id,
            )

        except HTTPStatusError as e:
            logger.error(f"调用 SigNoz API 失败: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"获取 trace 信息失败: {e}")
            raise HTTPException(status_code=500, detail=f"API处理失败: {str(e)}")
