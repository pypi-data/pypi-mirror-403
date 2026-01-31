import logging
from typing import Any

from mistralai_workflows.core.activity import activity
from mistralai_workflows.core.config.config import INTERNAL_ACTIVITY_PREFIX
from mistralai_workflows.core.events.event_context import EventContext
from mistralai_workflows.core.events.event_utils import create_base_event_fields
from mistralai_workflows.protocol.v1.events import (
    CustomTaskCompleted,
    CustomTaskCompletedAttributes,
    CustomTaskFailed,
    CustomTaskFailedAttributes,
    CustomTaskInProgress,
    CustomTaskInProgressAttributes,
    CustomTaskStarted,
    CustomTaskStartedAttributes,
    Failure,
    JSONPayload,
    WorkflowExecutionCanceled,
    WorkflowExecutionCanceledAttributes,
    WorkflowExecutionCompleted,
    WorkflowExecutionCompletedAttributes,
    WorkflowExecutionFailed,
    WorkflowExecutionFailedAttributes,
    WorkflowExecutionStarted,
    WorkflowExecutionStartedAttributes,
)

logger = logging.getLogger(__name__)


@activity(name=f"{INTERNAL_ACTIVITY_PREFIX}emit_workflow_started", _allow_reserved_name=True)
async def _emit_workflow_started(task_id: str, workflow_name: str, input_args: list) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                WorkflowExecutionStarted(
                    **create_base_event_fields(),
                    attributes=WorkflowExecutionStartedAttributes(
                        task_id=task_id,
                        workflow_name=workflow_name,
                        input=JSONPayload(value=input_args),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit workflow started event: {e}")


@activity(name=f"{INTERNAL_ACTIVITY_PREFIX}emit_workflow_completed", _allow_reserved_name=True)
async def _emit_workflow_completed(task_id: str, result: Any) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                WorkflowExecutionCompleted(
                    **create_base_event_fields(),
                    attributes=WorkflowExecutionCompletedAttributes(
                        task_id=task_id,
                        result=JSONPayload(value=result),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit workflow completed event: {e}")


@activity(name=f"{INTERNAL_ACTIVITY_PREFIX}emit_workflow_canceled", _allow_reserved_name=True)
async def _emit_workflow_canceled(task_id: str, reason: str | None) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                WorkflowExecutionCanceled(
                    **create_base_event_fields(),
                    attributes=WorkflowExecutionCanceledAttributes(
                        task_id=task_id,
                        reason=reason,
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit workflow canceled event: {e}")


@activity(name=f"{INTERNAL_ACTIVITY_PREFIX}emit_workflow_failed", _allow_reserved_name=True)
async def _emit_workflow_failed(task_id: str, error_message: str) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                WorkflowExecutionFailed(
                    **create_base_event_fields(),
                    attributes=WorkflowExecutionFailedAttributes(
                        task_id=task_id,
                        failure=Failure(message=error_message),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit workflow failed event: {e}")


@activity(name="__emit_waiting_for_input_started")
async def _emit_waiting_for_input_started(task_id: str, input_schema: dict, label: str | None) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                CustomTaskStarted(
                    **create_base_event_fields(),
                    attributes=CustomTaskStartedAttributes(
                        custom_task_id=task_id,
                        custom_task_type="wait_for_input",
                        payload=JSONPayload(value={"input_schema": input_schema, "label": label}),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit wait_for_input started event: {e}")


@activity(name="__emit_waiting_for_input_completed")
async def _emit_waiting_for_input_completed(task_id: str, input_schema: dict, label: str | None) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                CustomTaskCompleted(
                    **create_base_event_fields(),
                    attributes=CustomTaskCompletedAttributes(
                        custom_task_id=task_id,
                        custom_task_type="wait_for_input",
                        payload=JSONPayload(value={"input_schema": input_schema, "label": label}),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit wait_for_input completed event: {e}")


@activity(name="__emit_waiting_for_input_failed")
async def _emit_waiting_for_input_failed(task_id: str, input_schema: dict, label: str | None, error: str) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                CustomTaskFailed(
                    **create_base_event_fields(),
                    attributes=CustomTaskFailedAttributes(
                        custom_task_id=task_id,
                        custom_task_type="wait_for_input",
                        failure=Failure(message=error),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit wait_for_input failed event: {e}")


@activity(name=f"{INTERNAL_ACTIVITY_PREFIX}emit_task_started", _allow_reserved_name=True)
async def _emit_task_started(task_id: str, task_type: str, state: Any) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                CustomTaskStarted(
                    **create_base_event_fields(),
                    attributes=CustomTaskStartedAttributes(
                        custom_task_id=task_id,
                        custom_task_type=task_type,
                        payload=JSONPayload(value=state),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit task started event: {e}")


@activity(name=f"{INTERNAL_ACTIVITY_PREFIX}emit_task_in_progress", _allow_reserved_name=True)
async def _emit_task_in_progress(task_id: str, task_type: str, patches: Any) -> None:
    from mistralai_workflows.protocol.v1.events import JSONPatchPayload

    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                CustomTaskInProgress(
                    **create_base_event_fields(),
                    attributes=CustomTaskInProgressAttributes(
                        custom_task_id=task_id,
                        custom_task_type=task_type,
                        payload=JSONPatchPayload(value=patches),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit task in progress event: {e}")


@activity(name=f"{INTERNAL_ACTIVITY_PREFIX}emit_task_completed", _allow_reserved_name=True)
async def _emit_task_completed(task_id: str, task_type: str, state: Any) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                CustomTaskCompleted(
                    **create_base_event_fields(),
                    attributes=CustomTaskCompletedAttributes(
                        custom_task_id=task_id,
                        custom_task_type=task_type,
                        payload=JSONPayload(value=state),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit task completed event: {e}")


@activity(name=f"{INTERNAL_ACTIVITY_PREFIX}emit_task_failed", _allow_reserved_name=True)
async def _emit_task_failed(task_id: str, task_type: str, error: str) -> None:
    context = EventContext.get_singleton()
    if context:
        try:
            await context.publish_event(
                CustomTaskFailed(
                    **create_base_event_fields(),
                    attributes=CustomTaskFailedAttributes(
                        custom_task_id=task_id,
                        custom_task_type=task_type,
                        failure=Failure(message=error),
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to emit task failed event: {e}")
