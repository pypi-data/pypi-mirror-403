from __future__ import annotations

from typing import Optional

from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from service_forge.service_config import TraceConfig

_initialized = False

def _parse_headers(raw: Optional[str]) -> dict[str, str]:
    if not raw:
        return {}
    headers: dict[str, str] = {}
    for part in raw.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            headers[key.strip()] = value.strip()
    return headers


def setup_tracing(service_name: Optional[str] = None, config: TraceConfig = None) -> None:
    """Initialize a global tracer provider with OTLP exporter if not already configured."""
    if config is None or not config.enable:
        return

    global _initialized
    if _initialized:
        return

    try:
        service_name = service_name or "service_forge_service"
        endpoint = config.url
        headers = _parse_headers(config.headers)

        sampler_arg = config.arg or 1.0
        ratio = float(sampler_arg)
        sampler = ParentBased(TraceIdRatioBased(ratio))

        resource = Resource.create(
            {
                "service.name": service_name,
                "service.namespace": config.namespace or "secondbrain",
                "service.instance.id": config.hostname or "",
            }
        )
        provider = TracerProvider(resource=resource, sampler=sampler)
        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _initialized = True
        logger.info(
            f"Tracing initialized: endpoint={endpoint}, service={service_name}, ratio={ratio}"
        )
    except Exception as exc:
        logger.warning(f"Tracing initialization failed: {exc}")
