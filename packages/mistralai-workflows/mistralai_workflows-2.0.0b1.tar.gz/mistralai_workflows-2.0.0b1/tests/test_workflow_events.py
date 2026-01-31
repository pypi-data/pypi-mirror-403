import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest
from temporalio.client import WorkflowFailureError
from temporalio.common import RetryPolicy
from temporalio.exceptions import CancelledError
from temporalio.testing import WorkflowEnvironment

from mistralai_workflows.client import WorkflowsClient
from mistralai_workflows.core.events.event_context import EventContext
from mistralai_workflows.testing import (
    activity_completed,
    activity_started,
    compare_itemwise,
    custom_task_completed,
    custom_task_failed,
    custom_task_started,
    workflow_canceled,
    workflow_completed,
    workflow_failed,
    workflow_started,
)

from .fixtures import FailingWorkflow, PureWorkflow
from .fixtures_interactive_workflow import SimpleApprovalWorkflow, WorkflowWithValidationFailure
from .utils import create_test_worker_with_events, wait_for_pending_inputs


@pytest.mark.asyncio
async def test_basic_workflow_emits_lifecycle_events(temporal_env: WorkflowEnvironment) -> None:
    captured_events: list[Any] = []

    mock_client = AsyncMock(spec=WorkflowsClient)

    async def capture_event(event: Any) -> None:
        captured_events.append(event)

    mock_client.send_event = AsyncMock(side_effect=capture_event)

    async with EventContext(mock_client):
        async with create_test_worker_with_events(
            temporal_env,
            workflows=[PureWorkflow],
        ):
            handle = await temporal_env.client.start_workflow(
                "pure_workflow",
                {"name": "test-value"},
                id="test-basic-workflow-events",
                task_queue="test-task-queue",
            )

            result = await handle.result()
            assert result["result"] == "Workflow says: test-value"

            expected_events = [
                activity_started("__internal__emit_workflow_started", workflow_name="pure_workflow"),
                workflow_started("pure_workflow"),
                activity_completed("__internal__emit_workflow_started", workflow_name="pure_workflow"),
                activity_started("__internal__emit_workflow_completed", workflow_name="pure_workflow"),
                workflow_completed("pure_workflow"),
                activity_completed("__internal__emit_workflow_completed", workflow_name="pure_workflow"),
            ]

            errors = compare_itemwise(
                expected_events,
                captured_events,
                exclude_paths={
                    "event_id",
                    "event_timestamp",
                    "root_workflow_exec_id",
                    "parent_workflow_exec_id",
                    "workflow_exec_id",
                    "workflow_run_id",
                    "attributes.task_id",
                    "attributes.input",
                    "attributes.result",
                },
            )
            assert len(errors) == 0, "Event sequence mismatch:\n" + "\n".join(errors)


@pytest.mark.asyncio
async def test_wait_for_input_emits_lifecycle_events(temporal_env: WorkflowEnvironment) -> None:
    captured_events: list[Any] = []

    mock_client = AsyncMock(spec=WorkflowsClient)

    async def capture_event(event: Any) -> None:
        captured_events.append(event)

    mock_client.send_event = AsyncMock(side_effect=capture_event)

    async with EventContext(mock_client):
        async with create_test_worker_with_events(
            temporal_env,
            workflows=[SimpleApprovalWorkflow],
        ):
            handle = await temporal_env.client.start_workflow(
                "simple_approval_workflow",
                {"request_id": "req-event-test", "description": "Test event emission"},
                id="test-wait-for-input-events",
                task_queue="test-task-queue",
            )

            pending_inputs = await wait_for_pending_inputs(handle, expected_count=1)
            pending_task_id = pending_inputs[0]["task_id"]

            await handle.execute_update(
                "__submit_input",
                {"task_id": pending_task_id, "input": {"approved": True, "reason": "Test"}},
            )

            result = await handle.result()
            assert result["status"] == "approved"

            expected_events = [
                activity_started("__internal__emit_workflow_started", workflow_name="simple_approval_workflow"),
                workflow_started("simple_approval_workflow"),
                activity_completed("__internal__emit_workflow_started", workflow_name="simple_approval_workflow"),
                activity_started("__emit_waiting_for_input_started", workflow_name="simple_approval_workflow"),
                custom_task_started("wait_for_input", {}, workflow_name="simple_approval_workflow"),
                activity_completed("__emit_waiting_for_input_started", workflow_name="simple_approval_workflow"),
                activity_started("__emit_waiting_for_input_completed", workflow_name="simple_approval_workflow"),
                custom_task_completed("wait_for_input", {}, workflow_name="simple_approval_workflow"),
                activity_completed("__emit_waiting_for_input_completed", workflow_name="simple_approval_workflow"),
                activity_started("__internal__emit_workflow_completed", workflow_name="simple_approval_workflow"),
                workflow_completed("simple_approval_workflow"),
                activity_completed("__internal__emit_workflow_completed", workflow_name="simple_approval_workflow"),
            ]

            errors = compare_itemwise(
                expected_events,
                captured_events,
                exclude_paths={
                    "event_id",
                    "event_timestamp",
                    "root_workflow_exec_id",
                    "parent_workflow_exec_id",
                    "workflow_exec_id",
                    "workflow_run_id",
                    "attributes.task_id",
                    "attributes.custom_task_id",
                    "attributes.input",
                    "attributes.result",
                    "attributes.payload",
                },
            )
            assert len(errors) == 0, "Event sequence mismatch:\n" + "\n".join(errors)


@pytest.mark.asyncio
async def test_wait_for_input_emits_failed_event_on_validation_error(temporal_env: WorkflowEnvironment) -> None:
    captured_events: list[Any] = []

    mock_client = AsyncMock(spec=WorkflowsClient)

    async def capture_event(event: Any) -> None:
        captured_events.append(event)

    mock_client.send_event = AsyncMock(side_effect=capture_event)

    async with EventContext(mock_client):
        async with create_test_worker_with_events(
            temporal_env,
            workflows=[WorkflowWithValidationFailure],
        ):
            handle = await temporal_env.client.start_workflow(
                "workflow_with_validation_failure",
                {"request_id": "req-validation-test"},
                id="test-validation-failure",
                task_queue="test-task-queue",
            )

            result = await handle.result()
            assert result["status"] == "error"

            expected_events = [
                activity_started(
                    "__internal__emit_workflow_started",
                    workflow_name="workflow_with_validation_failure",
                ),
                workflow_started("workflow_with_validation_failure"),
                activity_completed(
                    "__internal__emit_workflow_started",
                    workflow_name="workflow_with_validation_failure",
                ),
                activity_started(
                    "__emit_waiting_for_input_started",
                    workflow_name="workflow_with_validation_failure",
                ),
                custom_task_started(
                    "wait_for_input",
                    {},
                    workflow_name="workflow_with_validation_failure",
                ),
                activity_completed(
                    "__emit_waiting_for_input_started",
                    workflow_name="workflow_with_validation_failure",
                ),
                activity_started(
                    "__emit_waiting_for_input_failed",
                    workflow_name="workflow_with_validation_failure",
                ),
                custom_task_failed(
                    "wait_for_input",
                    "",
                    workflow_name="workflow_with_validation_failure",
                ),
                activity_completed(
                    "__emit_waiting_for_input_failed",
                    workflow_name="workflow_with_validation_failure",
                ),
                activity_started(
                    "__internal__emit_workflow_completed",
                    workflow_name="workflow_with_validation_failure",
                ),
                workflow_completed("workflow_with_validation_failure"),
                activity_completed(
                    "__internal__emit_workflow_completed",
                    workflow_name="workflow_with_validation_failure",
                ),
            ]

            errors = compare_itemwise(
                expected_events,
                captured_events,
                exclude_paths={
                    "event_id",
                    "event_timestamp",
                    "root_workflow_exec_id",
                    "parent_workflow_exec_id",
                    "workflow_exec_id",
                    "workflow_run_id",
                    "attributes.task_id",
                    "attributes.custom_task_id",
                    "attributes.input",
                    "attributes.result",
                    "attributes.payload",
                    "attributes.failure.message",
                },
            )
            assert len(errors) == 0, "Event sequence mismatch:\n" + "\n".join(errors)


@pytest.mark.asyncio
async def test_wait_for_input_emits_failed_event_on_cancellation(temporal_env: WorkflowEnvironment) -> None:
    captured_events: list[Any] = []

    mock_client = AsyncMock(spec=WorkflowsClient)

    async def capture_event(event: Any) -> None:
        captured_events.append(event)

    mock_client.send_event = AsyncMock(side_effect=capture_event)

    async with EventContext(mock_client):
        async with create_test_worker_with_events(
            temporal_env,
            workflows=[SimpleApprovalWorkflow],
        ):
            handle = await temporal_env.client.start_workflow(
                "simple_approval_workflow",
                {"request_id": "req-cancel-test", "description": "Test cancellation"},
                id="test-wait-for-input-cancel",
                task_queue="test-task-queue",
            )

            await wait_for_pending_inputs(handle, expected_count=1)

            await handle.cancel()

            # Wait for workflow to complete with cancellation
            with pytest.raises(WorkflowFailureError) as exc_info:
                await handle.result()

            assert isinstance(exc_info.value.cause, CancelledError)

            expected_events = [
                activity_started("__internal__emit_workflow_started", workflow_name="simple_approval_workflow"),
                workflow_started("simple_approval_workflow"),
                activity_completed("__internal__emit_workflow_started", workflow_name="simple_approval_workflow"),
                activity_started("__emit_waiting_for_input_started", workflow_name="simple_approval_workflow"),
                custom_task_started("wait_for_input", {}, workflow_name="simple_approval_workflow"),
                activity_completed("__emit_waiting_for_input_started", workflow_name="simple_approval_workflow"),
                activity_started("__emit_waiting_for_input_failed", workflow_name="simple_approval_workflow"),
                custom_task_failed(
                    "wait_for_input",
                    "",
                    workflow_name="simple_approval_workflow",
                ),
                activity_completed("__emit_waiting_for_input_failed", workflow_name="simple_approval_workflow"),
                activity_started("__internal__emit_workflow_canceled", workflow_name="simple_approval_workflow"),
                workflow_canceled("simple_approval_workflow"),
                activity_completed("__internal__emit_workflow_canceled", workflow_name="simple_approval_workflow"),
            ]

            errors = compare_itemwise(
                expected_events,
                captured_events,
                exclude_paths={
                    "event_id",
                    "event_timestamp",
                    "root_workflow_exec_id",
                    "parent_workflow_exec_id",
                    "workflow_exec_id",
                    "workflow_run_id",
                    "attributes.task_id",
                    "attributes.custom_task_id",
                    "attributes.input",
                    "attributes.result",
                    "attributes.payload",
                    "attributes.failure.message",
                    "attributes.reason",
                },
            )
            assert len(errors) == 0, "Event sequence mismatch:\n" + "\n".join(errors)


@pytest.mark.asyncio
async def test_workflow_failure_emits_failed_event(temporal_env: WorkflowEnvironment) -> None:
    captured_events: list[Any] = []

    mock_client = AsyncMock(spec=WorkflowsClient)

    async def capture_event(event: Any) -> None:
        captured_events.append(event)

    mock_client.send_event = AsyncMock(side_effect=capture_event)

    async with EventContext(mock_client):
        async with create_test_worker_with_events(
            temporal_env,
            workflows=[FailingWorkflow],
        ):
            handle = await temporal_env.client.start_workflow(
                "failing_workflow",
                {"message": "test-error"},
                id="test-workflow-failure-events",
                retry_policy=RetryPolicy(maximum_attempts=1),
                task_queue="test-task-queue",
            )

            async def wait_for_events(expected_count: int, timeout_seconds: float = 5.0) -> None:
                loop = asyncio.get_running_loop()
                deadline = loop.time() + timeout_seconds
                while loop.time() < deadline:
                    if len(captured_events) >= expected_count:
                        return
                    await asyncio.sleep(0.1)
                raise TimeoutError("Did not receive expected workflow events in time")

            await wait_for_events(expected_count=6)

            with pytest.raises(WorkflowFailureError) as exc_info:
                await handle.result()
            assert "Intentional failure: test-error" in str(exc_info.value.cause)

            expected_events = [
                activity_started("__internal__emit_workflow_started", workflow_name="failing_workflow"),
                workflow_started("failing_workflow"),
                activity_completed("__internal__emit_workflow_started", workflow_name="failing_workflow"),
                activity_started("__internal__emit_workflow_failed", workflow_name="failing_workflow"),
                workflow_failed("failing_workflow"),
                activity_completed("__internal__emit_workflow_failed", workflow_name="failing_workflow"),
            ]

            errors = compare_itemwise(
                expected_events,
                captured_events,
                exclude_paths={
                    "event_id",
                    "event_timestamp",
                    "root_workflow_exec_id",
                    "parent_workflow_exec_id",
                    "workflow_exec_id",
                    "workflow_run_id",
                    "attributes.task_id",
                    "attributes.input",
                    "attributes.result",
                    "attributes.failure.message",
                },
            )
            assert len(errors) == 0, "Event sequence mismatch:\n" + "\n".join(errors)
