from typing import (
    Literal,
    Tuple,
)

import structlog
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider

from mistralai_workflows.core.config.config import config
from mistralai_workflows.core.tracing.otel_config import config_otel, config_otel_local

logger = structlog.getLogger(__name__)


def init_tracing(component: Literal["api", "worker"]) -> Tuple[MeterProvider | None, TracerProvider | None]:
    """
    Initialize OpenTelemetry tracing for either the API or worker component.

    Args:
        component: Either "api" or "worker"

    Returns:
        A tuple of (meter_provider, tracer_provider), both of which may be None if tracing is not enabled
    """
    if not config.common.otel_enabled:
        logger.debug("OpenTelemetry tracing is disabled")
        return None, None

    service_name = f"{config.common.app_name}-{component}"

    if config.common.otel_endpoint:
        logger.info(
            "Initializing OpenTelemetry tracing",
            endpoint=config.common.otel_endpoint,
            service=service_name,
            sample_rate=config.common.otel_sample_rate,
        )
        meter_provider, tracer_provider = config_otel(
            endpoint=config.common.otel_endpoint,
            service_name=service_name,
            service_version=config.common.app_version,
            sample_rate=config.common.otel_sample_rate,
            export_otlp_interval_ms=config.common.otel_export_interval_ms,
            tail_sampling=config.common.otel_tail_sampling,
        )
    elif config.common.otel_local:
        logger.info(
            "Initializing local OpenTelemetry tracing",
            service=service_name,
            sample_rate=config.common.otel_sample_rate,
        )
        meter_provider, tracer_provider = config_otel_local(
            service_name=service_name,
            service_version=config.common.app_version,
            sample_rate=config.common.otel_sample_rate,
            tail_sampling=config.common.otel_tail_sampling,
        )
    else:
        logger.debug("OpenTelemetry endpoint or local mode not configured")
        return None, None

    # Instrument common libraries
    AsyncioInstrumentor().instrument(meter_provider=meter_provider, tracer_provider=tracer_provider)
    HTTPXClientInstrumentor().instrument(meter_provider=meter_provider, tracer_provider=tracer_provider)
    AioHttpClientInstrumentor().instrument(meter_provider=meter_provider, tracer_provider=tracer_provider)

    return meter_provider, tracer_provider
