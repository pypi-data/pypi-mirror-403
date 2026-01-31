import asyncio
import traceback
import warnings
from collections import defaultdict
from http import HTTPStatus
from typing import Any, Callable, DefaultDict, List, Type
from uuid import uuid4

import structlog
import temporalio.api.workflowservice.v1 as wsv1
import tenacity
from pydantic import BaseModel, SecretStr
from temporalio.client import Client as TemporalClient
from temporalio.client import Interceptor
from temporalio.common import VersioningBehavior, WorkerDeploymentVersion
from temporalio.converter import PayloadCodec, PayloadConverter
from temporalio.worker import Worker, WorkerDeploymentConfig

from mistralai_workflows.client import WorkflowsClient
from mistralai_workflows.core.activity import activity, get_all_temporal_activities
from mistralai_workflows.core.config import config_discovery
from mistralai_workflows.core.config.config import AppConfig, config
from mistralai_workflows.core.definition.workflow_definition import get_workflow_definition
from mistralai_workflows.core.dependencies.dependency_injector import DependencyInjector
from mistralai_workflows.core.encoding.fields_offloader import FieldsOffloader
from mistralai_workflows.core.events.event_context import EventContext
from mistralai_workflows.core.events.event_interceptor import EventInterceptor
from mistralai_workflows.core.execution.concurrency import InternalConcurrencyWorkflow
from mistralai_workflows.core.execution.sticky_session.get_sticky_worker_session import (
    GET_STICKY_WORKER_SESSION_ACTIVITY_NAME,
)
from mistralai_workflows.core.execution.sticky_session.sticky_worker_session import (
    StickyWorkerSession,
    check_activity_is_sticky_to_worker,
)
from mistralai_workflows.core.rate_limiting.rate_limit import get_rate_limit
from mistralai_workflows.core.temporal.activity_offloading_interceptor import (
    ActivityInOutOffloadingInterceptor,
)
from mistralai_workflows.core.temporal.context_handler_interceptor import (
    ContextHandlerInterceptor,
)
from mistralai_workflows.core.temporal.payload_codec import MistralWorkflowsPayloadCodec
from mistralai_workflows.core.temporal.payload_converter import MistralWorkflowsPayloadConverter
from mistralai_workflows.core.temporal.temporal_client import create_temporal_client
from mistralai_workflows.core.tracing.init_tracing import init_tracing
from mistralai_workflows.core.workflow import ClassType
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException
from mistralai_workflows.models import WorkflowSpecWithTaskQueue
from mistralai_workflows.plugins._discovery import list_plugins
from mistralai_workflows.protocol.v1.workflow import WorkflowSpecsRegisterResponse

logger = structlog.get_logger(__name__)


class WorkerConfig(BaseModel):
    task_queue: str
    max_task_queue_activities_per_second: float | None = None

    def __hash__(self) -> int:
        return hash((self.task_queue, self.max_task_queue_activities_per_second))


@tenacity.retry(
    # Retry only on transient error
    retry=tenacity.retry_if_exception(
        lambda exc: (
            isinstance(exc, WorkflowsException)
            and exc.status
            in [
                HTTPStatus.BAD_GATEWAY,
                HTTPStatus.GATEWAY_TIMEOUT,
                HTTPStatus.SERVICE_UNAVAILABLE,
            ]
        )
    ),
    before_sleep=lambda retry_state: logger.warning(
        "Retrying register workflow specs",
        attempt=retry_state.attempt_number,
    ),
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=0.5, min=0.5, max=2),
    reraise=True,
)
async def _register_workflow_specs(
    workflows_client: WorkflowsClient,
    workflow_definitions: list[WorkflowSpecWithTaskQueue],
) -> WorkflowSpecsRegisterResponse:
    return await workflows_client.register_workflow_specs(workflow_definitions)


async def _worker_register(
    workflows_client: WorkflowsClient,
    workflow_definitions: list[WorkflowSpecWithTaskQueue],
    interval: int,
) -> None:
    try:
        while True:
            await _register_workflow_specs(workflows_client, workflow_definitions)
            await asyncio.sleep(interval)
    except Exception:
        logger.error("Error in periodic task", error=traceback.format_exc())
        raise WorkflowsException(code=ErrorCode.WORKER_REGISTRATION_ERROR, message="Fail to register worker")


async def _auto_register_as_current_version(
    temporal_client: TemporalClient,
    namespace: str,
    deployment_name: str,
    build_id: str,
) -> None:
    """
    Auto-register worker as current version for manual/local deployments.

    Retries until successful, as the Worker Deployment may not exist yet when the worker first starts.
    Once registered successfully, the task completes.

    Args:
        temporal_client: Temporal client instance
        namespace: Temporal namespace
        deployment_name: Worker deployment name
        build_id: Build ID to set as current
    """

    retry_count = 0
    max_retries = 48  # 2 minutes worth of retries (2.5s intervals)

    while retry_count < max_retries:
        try:
            await asyncio.sleep(2.5)  # Wait 2.5s before each attempt

            set_request = wsv1.SetWorkerDeploymentCurrentVersionRequest(
                namespace=namespace,
                deployment_name=deployment_name,
                build_id=build_id,
            )
            await temporal_client.workflow_service.set_worker_deployment_current_version(set_request)

            logger.info(
                "Successfully auto-registered worker as current version",
                deployment_name=deployment_name,
                build_id=build_id,
                retry_count=retry_count,
            )
            return  # Success - exit the function

        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(
                    "Failed to auto-register worker as current version after max retries",
                    error=str(e),
                    deployment_name=deployment_name,
                    build_id=build_id,
                    max_retries=max_retries,
                )
                return

            logger.debug(
                "Waiting for worker deployment to be available",
                deployment_name=deployment_name,
                build_id=build_id,
                retry_count=retry_count,
                max_retries=max_retries,
                error=str(e),
            )


def _get_workflow_definitions(workflows: list[ClassType], task_queue: str) -> List[WorkflowSpecWithTaskQueue]:
    workflow_definitions: List[WorkflowSpecWithTaskQueue] = []
    for workflow in workflows:
        workflow_def = get_workflow_definition(workflow)
        if workflow_def is None:
            continue
        workflow_def_with_task_queue = WorkflowSpecWithTaskQueue.model_validate(
            {
                **workflow_def.model_dump(),
                "task_queue": task_queue,
            }
        )
        workflow_definitions.append(workflow_def_with_task_queue)
    return workflow_definitions


def _create_temporal_workers(
    temporal_client: TemporalClient,
    workflows: List[ClassType],
    config: AppConfig,
) -> List[Worker]:
    # Get all activities (based on the imports made before running the workers)
    all_activities = get_all_temporal_activities()
    logger.info("Registered activities", activities=[act.__name__ for act in all_activities])
    all_workflows: List[Type] = [*workflows, InternalConcurrencyWorkflow]

    # Sticky Worker Session
    random_id = uuid4().hex.replace("-", "")
    sticky_worker_session_task_queue = f"{config.temporal.task_queue}-sticky-worker-session-{random_id}"

    @activity(name=GET_STICKY_WORKER_SESSION_ACTIVITY_NAME, _skip_registering=True)
    async def get_sticky_worker_session() -> StickyWorkerSession:
        return StickyWorkerSession(task_queue=sticky_worker_session_task_queue)

    all_activities.append(get_sticky_worker_session)

    # Split activities into workers based on their needs
    # 1. Sticky activities go to a dedicated task queue
    # 2. Rate limited activities go to a dedicated task queue (one task queue per rate limit)
    activities_per_worker_config: DefaultDict[WorkerConfig, list[Callable]] = defaultdict(list)

    for act in all_activities:
        if check_activity_is_sticky_to_worker(act):  # 1.
            worker_config = WorkerConfig(task_queue=sticky_worker_session_task_queue)
        elif rate_limit := get_rate_limit(act):  # 2.
            max_task_queue_activities_per_second = (
                rate_limit.max_execution / rate_limit.time_window_in_sec
                # * config.temporal.temporal_frontend_num_task_queue_partitions
            )
            worker_config = WorkerConfig(
                task_queue=rate_limit.task_queue,
                max_task_queue_activities_per_second=max_task_queue_activities_per_second,
            )
        else:
            continue

        activities_per_worker_config[worker_config].append(act)

    # 3. We also register all acitvities on the main worker
    #    in order to be able to execute them as local activities
    #    see `run_activities_locally`.
    main_worker_config = WorkerConfig(task_queue=config.temporal.task_queue)
    activities_per_worker_config[main_worker_config] = all_activities

    versioning_cfg = config.worker.versioning
    main_task_queue = config.temporal.task_queue
    deployment_config: WorkerDeploymentConfig | None = None

    if versioning_cfg.enabled and versioning_cfg.deployment_name and versioning_cfg.build_id:
        default_behavior = VersioningBehavior.PINNED
        deployment_config = WorkerDeploymentConfig(
            use_worker_versioning=True,
            version=WorkerDeploymentVersion(
                deployment_name=versioning_cfg.deployment_name,
                build_id=versioning_cfg.build_id,
            ),
            default_versioning_behavior=default_behavior,
        )
        logger.info(
            "Worker deployment config created",
            deployment_name=versioning_cfg.deployment_name,
            build_id=versioning_cfg.build_id,
        )
    elif versioning_cfg.enabled:
        logger.warning("Worker versioning enabled but deployment name or build ID missing; running without versioning")

    workers: List[Worker] = []
    for worker_config_obj, activities in activities_per_worker_config.items():
        is_main_worker = worker_config_obj.task_queue == main_task_queue
        worker_kwargs: dict[str, Any] = {
            "client": temporal_client,
            "task_queue": worker_config_obj.task_queue,
            "workflows": all_workflows if is_main_worker else [],
            "activities": activities,
            "max_task_queue_activities_per_second": worker_config_obj.max_task_queue_activities_per_second,
            "workflow_failure_exception_types": [Exception]
            if config.worker.dangerously_force_fail_workflow_on_error
            else [],
        }
        if is_main_worker and deployment_config is not None:
            worker_kwargs["deployment_config"] = deployment_config
        workers.append(Worker(**worker_kwargs))
    return workers


async def _run_worker(workflows: List[ClassType]) -> None:
    try:
        api_key = config.common.mistral_api_key.get_secret_value() if config.common.mistral_api_key else None
        workflows_client = WorkflowsClient(
            base_url=config.worker.server_url,
            api_version=config.worker.api_version,
            api_key=api_key or None,
            headers=config.worker.mistral_api_headers,
        )

        # Initialize OpenTelemetry tracing for the worker component
        meter_provider, tracer_provider = init_tracing("worker")
        if meter_provider and tracer_provider:
            logger.info("OpenTelemetry tracing initialized for worker")

        # Always use custom payload converter and codec for context propagation
        # Offloading and encryption are controlled by their respective configs
        payload_converter: Type[PayloadConverter] = MistralWorkflowsPayloadConverter
        payload_codec: PayloadCodec = MistralWorkflowsPayloadCodec(
            payload_offloading_config=config.worker.temporal_payload_offloading,
            payload_encryption_config=config.worker.temporal_payload_encryption,
        )
        extra_interceptors: List[Interceptor] = [
            ContextHandlerInterceptor(),
            EventInterceptor(),
        ]

        extra_interceptors.append(
            ActivityInOutOffloadingInterceptor(
                offloader=FieldsOffloader(offloading_config=config.worker.activity_attributes_offloading)
            )
        )

        # Create Temporal client (with tracing interceptor if enabled)
        temporal_client = await create_temporal_client(
            namespace=config.temporal.namespace,
            payload_codec=payload_codec,
            payload_converter=payload_converter,
            extra_interceptors=extra_interceptors,
        )

        # Log installed contributions
        plugins = list_plugins()
        logger.info(
            f"Discovered {len(plugins)} package(s) at mistral_workflows.plugins",
            plugins=plugins,
        )

        # Initialize dependency injector
        dependency_injector = DependencyInjector.get_singleton_instance()

        # Get workflow definitions for custom workflows
        workflow_definitions = _get_workflow_definitions(workflows, config.temporal.task_queue)

        # Create Temporal workers
        workers = _create_temporal_workers(
            temporal_client=temporal_client,
            workflows=workflows,
            config=config,
        )

        # Register workflows to Workflows API
        response = await _register_workflow_specs(
            workflows_client,
            workflow_definitions,
        )
        if response.has_conflicts and not config.worker.allow_override_namespace:
            raise ValueError(
                f"Namespace '{config.temporal.namespace}' is already used by another worker. "
                "Please use a custom namespace "
                "or set `ALLOW_OVERRIDE_NAMESPACE` to True IF AND ONLY IF you own this namespace."
            )

        async with (
            workflows_client,
            asyncio.TaskGroup() as tg,
            dependency_injector.with_dependencies(),
            EventContext(workflows_client),
        ):
            register_task = tg.create_task(
                _worker_register(
                    interval=10,
                    workflows_client=workflows_client,
                    workflow_definitions=workflow_definitions,
                )
            )

            # Auto-register as current version if enabled (for manual/local deployments)
            auto_register_task = None
            if (
                config.worker.versioning.auto_register_as_current
                and config.worker.versioning.enabled
                and config.worker.versioning.deployment_name
                and config.worker.versioning.build_id
            ):
                auto_register_task = tg.create_task(
                    _auto_register_as_current_version(
                        temporal_client=temporal_client,
                        namespace=config.temporal.namespace,
                        deployment_name=config.worker.versioning.deployment_name,
                        build_id=config.worker.versioning.build_id,
                    )
                )

            logger.info(
                "Starting Temporal worker",
                task_queue=config.temporal.task_queue,
                namespace=config.temporal.namespace,
            )
            try:
                await asyncio.gather(*[worker.run() for worker in workers])
            except Exception:
                logger.error("Error running worker", error=traceback.format_exc())
                raise
            finally:
                logger.info("Worker shutting down, cleaning up resources")
                register_task.cancel()
                if auto_register_task:
                    auto_register_task.cancel()
                try:
                    await register_task
                except asyncio.CancelledError:
                    pass
                if auto_register_task:
                    try:
                        await auto_register_task
                    except asyncio.CancelledError:
                        pass
                await asyncio.gather(*[worker.shutdown() for worker in workers])
                logger.info("Worker shutdown complete")

    except Exception:
        logger.error("Error in worker", error=traceback.format_exc())
        raise


async def run_worker(
    workflows: List[ClassType],
    detach: bool = False,
    api_key: str | None = None,
    namespace: str | None = None,
    enable_config_discovery: bool | None = None,
) -> asyncio.Task | None:
    """
    Initialize and run a Temporal worker with the specified workflows.

    Args:
        workflows: List of workflow classes to register with the worker
        detach: If True, run the worker in a detached thread
        api_key: Optional API key for the Mistral API authentication (sent as Bearer token)
        namespace: Optional namespace to use for the worker
    """
    original_config = config.model_copy(deep=True)

    def _revert_config() -> None:
        config.__dict__.update(original_config.__dict__)

    enable_config_discovery = (
        enable_config_discovery if enable_config_discovery is not None else config.worker.enable_config_discovery
    )
    if not enable_config_discovery:
        warnings.warn("Disabling automatic config discovery")
        if namespace is not None:
            config.temporal.namespace = namespace
        if api_key is not None:
            config.common.mistral_api_key = SecretStr(api_key)
    else:
        if namespace is not None:
            warnings.warn("Namespace provided but config discovery is enabled. Ignoring namespace.")
        await config_discovery.apply_worker_runtime_config(api_key)
    logger.info("Worker config", config=config.common.model_dump())
    if detach:
        task = asyncio.create_task(_run_worker(workflows))

        def _on_worker_done(_: asyncio.Task) -> None:
            _revert_config()

        task.add_done_callback(_on_worker_done)
        return task
    else:
        try:
            await _run_worker(workflows)
        finally:
            _revert_config()
        return None
