from fastapi import FastAPI
import uvicorn
from fastapi import APIRouter
from loguru import logger
from typing import Optional
from urllib.parse import urlparse
from fastapi import HTTPException, Request, WebSocket, WebSocketException
from fastapi.middleware.cors import CORSMiddleware

from opentelemetry import context as otel_context_api
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from service_forge.sft.config.sf_metadata import load_metadata
from service_forge.sft.util.name_util import get_service_url_name
from service_forge.api.routers.meta_api.meta_api_router import meta_api_router
from service_forge.api.routers.trace.trace_router import trace_router
from service_forge.api.service_studio import studio_static_files
from service_forge.api.routers.websocket.websocket_router import websocket_router
from service_forge.api.routers.service.service_router import service_router
from service_forge.api.routers.feedback.feedback_router import router as feedback_router

def create_app(
    app: FastAPI | None = None,
    routers: list[APIRouter] | None = None,
    cors_origins: list[str] | None = None,
    root_path: str | None = None,
) -> FastAPI:
    if app is None:
        app = FastAPI(root_path=root_path)
        FastAPIInstrumentor.instrument_app(app)
    
    # Configure CORS middleware
    if cors_origins is None:
        cors_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers if provided
    if routers:
        for router in routers:
            app.include_router(router)
    
    # Always include WebSocket router
    app.include_router(websocket_router)

    # Include Feedback router
    app.include_router(feedback_router)
    
    # Always include Service router, Meta API Router, Trace Router, and Static Files
    app.include_router(service_router)
    app.include_router(meta_api_router)
    app.include_router(trace_router)

    app.mount('/sdk/studio', studio_static_files)

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        request.state.user_id = request.headers.get("X-User-ID") or "0"
        request.state.auth_token = request.headers.get("X-User-Token") or ""
        return await call_next(request)

    return app


async def start_fastapi_server(host: str, port: int):
    try:
        config = uvicorn.Config(
            fastapi_app,
            host=host,
            port=int(port),
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

try:
    metadata = load_metadata("sf-meta.yaml")
    if metadata.mode == "debug":
        fastapi_app = create_app(root_path=None)
    else:
        fastapi_app = create_app(root_path=f"/api/v1/{get_service_url_name(metadata.name, metadata.version)}")
except Exception as e:
    logger.warning(f"Failed to load metadata, using default configuration: {e}")
    fastapi_app = create_app(root_path=None)
