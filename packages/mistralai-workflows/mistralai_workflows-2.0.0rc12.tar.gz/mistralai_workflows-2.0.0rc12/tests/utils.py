import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, List, Type

import structlog
from temporalio.client import WorkflowHandle
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from mistralai_workflows.core.activity import activity
from mistralai_workflows.core.events.event_activities import (
    _emit_task_completed,
    _emit_task_failed,
    _emit_task_in_progress,
    _emit_task_started,
    _emit_waiting_for_input_completed,
    _emit_waiting_for_input_failed,
    _emit_waiting_for_input_started,
    _emit_workflow_canceled,
    _emit_workflow_completed,
    _emit_workflow_failed,
    _emit_workflow_started,
)
from mistralai_workflows.core.events.event_interceptor import EventInterceptor
from mistralai_workflows.core.execution.sticky_session.get_sticky_worker_session import (
    GET_STICKY_WORKER_SESSION_ACTIVITY_NAME,
)
from mistralai_workflows.core.execution.sticky_session.sticky_worker_session import StickyWorkerSession

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def create_test_worker(
    env: WorkflowEnvironment,
    workflows: List[Type],
    activities: List[Callable] | None = None,
    task_queue: str = "test-task-queue",
) -> AsyncGenerator[Worker, None]:
    # Create the get_sticky_worker_session activity that returns a fixed task queue
    # For tests, we just use the same task queue - no need to replicate production's multi-worker setup
    @activity(name=GET_STICKY_WORKER_SESSION_ACTIVITY_NAME, _skip_registering=True)
    async def get_sticky_worker_session() -> StickyWorkerSession:
        return StickyWorkerSession(task_queue=task_queue)

    all_activities = list(activities or [])
    all_activities.append(get_sticky_worker_session)
    all_activities.extend(
        [
            _emit_waiting_for_input_started,
            _emit_waiting_for_input_completed,
            _emit_waiting_for_input_failed,
            _emit_workflow_started,
            _emit_workflow_completed,
            _emit_workflow_canceled,
            _emit_workflow_failed,
        ]
    )

    worker = Worker(
        env.client,
        task_queue=task_queue,
        workflows=workflows,
        activities=all_activities,
    )

    async with worker:
        yield worker


@asynccontextmanager
async def create_test_worker_with_events(
    env: WorkflowEnvironment,
    workflows: List[Type],
    activities: List[Callable] | None = None,
    task_queue: str = "test-task-queue",
) -> AsyncGenerator[Worker, None]:
    @activity(name=GET_STICKY_WORKER_SESSION_ACTIVITY_NAME, _skip_registering=True)
    async def get_sticky_worker_session() -> StickyWorkerSession:
        return StickyWorkerSession(task_queue=task_queue)

    all_activities = list(activities or [])
    all_activities.append(get_sticky_worker_session)
    all_activities.extend(
        [
            _emit_waiting_for_input_started,
            _emit_waiting_for_input_completed,
            _emit_waiting_for_input_failed,
            _emit_workflow_started,
            _emit_workflow_completed,
            _emit_workflow_canceled,
            _emit_workflow_failed,
            _emit_task_started,
            _emit_task_in_progress,
            _emit_task_completed,
            _emit_task_failed,
        ]
    )

    worker = Worker(
        env.client,
        task_queue=task_queue,
        workflows=workflows,
        activities=all_activities,
        interceptors=[EventInterceptor()],
    )

    async with worker:
        yield worker


async def execute_workflow_in_test_env(
    env: WorkflowEnvironment,
    workflow_class: Type,
    workflow_input: Any,
    workflow_id: str | None = None,
    task_queue: str = "test-task-queue",
) -> Any:
    from mistralai_workflows.core.definition.workflow_definition import get_workflow_definition

    workflow_def: Any = get_workflow_definition(workflow_class)
    if not workflow_def:
        raise ValueError(f"Workflow {workflow_class} is not properly decorated")

    handle = await env.client.start_workflow(
        workflow_def.name,
        workflow_input,
        id=workflow_id or f"test-workflow-{asyncio.current_task().get_name()}",  # type: ignore
        task_queue=task_queue,
    )

    return await handle.result()


async def wait_for_pending_inputs(
    handle: WorkflowHandle, expected_count: int = 1, timeout: float = 5.0, label: str | None = None
) -> list[dict[str, Any]]:
    start_time = asyncio.get_event_loop().time()

    while True:
        try:
            pending_result = await handle.query("__get_pending_inputs")
            pending_inputs = pending_result["pending_inputs"]

            if label:
                pending_inputs = [inp for inp in pending_inputs if inp.get("label") == label]

            if len(pending_inputs) >= expected_count:
                return pending_inputs

        except Exception:
            pass

        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(
                f"Timeout waiting for {expected_count} pending inputs" + (f" with label '{label}'" if label else "")
            )

        await asyncio.sleep(0.05)
