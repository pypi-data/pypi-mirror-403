from __future__ import annotations

import warnings

import structlog
from httpx import HTTPStatusError

from mistralai_workflows.client import WorkflowsClient
from mistralai_workflows.core.config.config import config
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException
from mistralai_workflows.protocol.v1.worker import WorkerInfo

logger = structlog.get_logger(__name__)


class WorkerRuntimeConfig(WorkerInfo):
    def apply(self) -> None:
        config.temporal.namespace = self.namespace
        config.temporal.server_url = self.scheduler_url
        config.temporal.tls = self.tls


async def _fetch_worker_runtime_config(_api_key: str | None = None) -> WorkerRuntimeConfig:
    api_key = config.common.mistral_api_key.get_secret_value() if config.common.mistral_api_key else None
    workflows_client = WorkflowsClient(
        base_url=config.worker.server_url,
        api_version=config.worker.api_version,
        api_key=api_key or None,
        headers=config.worker.mistral_api_headers,
    )
    response = await workflows_client.who_am_i()
    logger.info("Worker runtime config resolved", namespace=response.namespace, scheduler_url=response.scheduler_url)
    return WorkerRuntimeConfig.model_validate_json(response.model_dump_json())


async def apply_worker_runtime_config(api_key: str | None = None) -> WorkerRuntimeConfig | None:
    try:
        runtime_config = await _fetch_worker_runtime_config(api_key)
        runtime_config.apply()
        logger.info(
            "Applied worker runtime config",
            namespace=runtime_config.namespace,
            scheduler_url=runtime_config.scheduler_url,
            tls=runtime_config.tls,
        )
        return runtime_config
    except HTTPStatusError as exc:
        if exc.response.status_code == 404:
            warnings.warn("Could not fetch worker config from server. Is your server up to date?")
            return None
        raise WorkflowsException(
            code=ErrorCode.WORKER_RUNTIME_CONFIG_ERROR,
            message="Failed to fetch worker runtime configuration from server",
        )
