from typing import List, Type

import structlog
from temporalio.client import Client as TemporalClient
from temporalio.client import Interceptor
from temporalio.contrib.pydantic import PydanticPayloadConverter
from temporalio.converter import DataConverter, PayloadCodec, PayloadConverter
from temporalio.runtime import OpenTelemetryConfig, Runtime, TelemetryConfig
from temporalio.service import ConnectConfig
from temporalio.service import ServiceClient as TemporalServiceClient

from mistralai_workflows.core.config.config import config
from mistralai_workflows.core.tracing.temporal_tracing_interceptor import get_temporal_tracing_interceptors
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException

logger = structlog.get_logger(__name__)

DEFAULT_NAMESPACE = "default"


async def create_temporal_service_client() -> TemporalServiceClient:
    runtime = Runtime(telemetry=TelemetryConfig())
    if config.common.otel_enabled:
        runtime = Runtime(
            telemetry=TelemetryConfig(
                metrics=OpenTelemetryConfig(url=f"{config.common.otel_endpoint}/v1/metrics", http=True)
            )
        )
    logger.info(
        "creating temporal service client",
        url=config.temporal.server_url,
        k=config.temporal.api_key,
        tls=config.temporal.tls,
        runtime=runtime,
    )
    api_key = config.temporal.api_key.get_secret_value() if config.temporal.api_key else None
    try:
        service_client = await TemporalServiceClient.connect(
            ConnectConfig(
                target_host=config.temporal.server_url,
                api_key=api_key or None,
                runtime=runtime,
                tls=config.temporal.tls,
            )
        )
    except Exception:
        raise WorkflowsException(
            code=ErrorCode.TEMPORAL_CONNECTION_ERROR, message="Fail to connect to Temporal Service Client"
        )
    logger.info("connected to temporal service client", url=config.temporal.server_url)
    return service_client


async def create_temporal_client(
    namespace: str | None = None,
    temporal_service_client: TemporalServiceClient | None = None,
    payload_converter: Type[PayloadConverter] = PydanticPayloadConverter,
    payload_codec: PayloadCodec | None = None,
    extra_interceptors: List[Interceptor] | None = None,
) -> TemporalClient:
    """
    Create and connect to a Temporal client with appropriate configuration.

    Args:
        namespace: Optional namespace to connect to
        temporal_sevice: Optional Temporal service client to use for namespace lookup

    Returns:
        Connected Temporal client instance

    Raises:
        ValueError: If connection fails
    """
    if not namespace:
        namespace = config.temporal.namespace

    # Get optional tracing interceptor
    interceptors: List[Interceptor] = []
    tracing_interceptors = get_temporal_tracing_interceptors()

    if extra_interceptors:
        for interceptor in extra_interceptors:
            interceptors.append(interceptor)

    if tracing_interceptors:
        interceptors.extend(tracing_interceptors)
        logger.debug("adding OpenTelemetry tracing interceptor to Temporal client")

    if temporal_service_client is None:
        temporal_service_client = await create_temporal_service_client()

    try:
        # Connect to Temporal
        client = TemporalClient(
            temporal_service_client,
            namespace=namespace,
            data_converter=DataConverter(
                payload_converter_class=payload_converter or PydanticPayloadConverter,
                payload_codec=payload_codec,
            ),
            interceptors=interceptors,
        )

        logger.info(
            "connected to temporal frontend",
            url=config.temporal.server_url,
            namespace=namespace,
            payload_converter=payload_converter,
            payload_codec=payload_codec,
        )
    except Exception as e:
        raise WorkflowsException(
            code=ErrorCode.TEMPORAL_CONNECTION_ERROR,
            message=f"failed to connect to temporal frontend at {config.temporal.server_url}",
        ) from e

    return client
