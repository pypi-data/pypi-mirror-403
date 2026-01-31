import uuid
from datetime import timedelta
from importlib import import_module
from typing import Any, Type

import structlog
import temporalio.activity
import temporalio.workflow
from pydantic import BaseModel, TypeAdapter
from pydantic_core import PydanticSerializationError

from mistralai_workflows.core.events.event_activities import (
    _emit_task_completed,
    _emit_task_failed,
    _emit_task_in_progress,
    _emit_task_started,
)
from mistralai_workflows.core.events.event_context import BackgroundEventPublisher
from mistralai_workflows.core.events.event_utils import create_base_event_fields
from mistralai_workflows.core.events.json_patch import make_json_patch
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
    JSONPatchPayload,
    JSONPayload,
    WorkflowEvent,
)

logger = structlog.get_logger(__name__)

adapter: TypeAdapter[Any] = TypeAdapter(Any)


def _to_json(obj: Any) -> Any:
    return adapter.dump_python(obj, mode="json")


def _should_publish_event() -> bool:
    event_utils_module = import_module("mistralai_workflows.core.events.event_utils")
    return bool(event_utils_module.should_publish_event())


def _publish_task_event(event: WorkflowEvent) -> None:
    if not _should_publish_event():
        return

    publisher = BackgroundEventPublisher.get_current()
    if publisher is None:
        raise RuntimeError("BackgroundEventPublisher not available - ensure activity interceptor is configured")

    publisher.publish_event_background(event)


class Task[T]:
    """
    Observable task context manager that emits lifecycle events to the Workflows API.

    Lifecycle: Started → InProgress* → Completed|Failed

    Use for operations that need real-time observability (LLM streaming, file processing, etc).

    Usage:
        ```python
        # In activities
        @workflows.activity
        async def process_file():
            async with task("file_processing", state={"progress": 0}) as t:
                await t.set_state({"progress": 50})
                await t.set_state({"progress": 100})

        # In workflows - can span multiple activities!
        @workflows.workflow.define()
        class MyWorkflow:
            @workflows.workflow.entrypoint
            async def run(self):
                async with task("llm_generation", state={"tokens": 0}) as t:
                    result1 = await call_activity_1()
                    await t.set_state({"tokens": 100})

                    result2 = await call_activity_2()
                    await t.set_state({"tokens": 200})
        ```
    """

    _id: str
    _type: str
    _state: T | None
    _started: bool

    def __init__(self, type: str, state: T | None = None, id: str | None = None) -> None:
        self._id = (
            id
            if id is not None
            else str(temporalio.workflow.uuid4() if temporalio.workflow.in_workflow() else uuid.uuid4())
        )
        self._type = type
        self._state = state
        self._started = False

    @property
    def id(self) -> str:
        return self._id

    @property
    def type(self) -> str:
        return self._type

    @property
    def state(self) -> T | None:
        return self._state

    async def __aenter__(self) -> "Task[T]":
        if not _should_publish_event():
            return self

        if temporalio.workflow.in_workflow():
            await temporalio.workflow.execute_local_activity(
                _emit_task_started,
                args=[self._id, self._type, _to_json(self._state)],
                start_to_close_timeout=timedelta(seconds=10),
            )
        else:
            _publish_task_event(
                CustomTaskStarted(
                    **create_base_event_fields(),
                    attributes=CustomTaskStartedAttributes(
                        custom_task_id=self._id,
                        custom_task_type=self._type,
                        payload=JSONPayload(value=_to_json(self._state)),
                    ),
                )
            )

        return self

    async def __aexit__(self, exc_type: Type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        if not _should_publish_event():
            return

        if temporalio.workflow.in_workflow():
            if exc_type is None:
                await temporalio.workflow.execute_local_activity(
                    _emit_task_completed,
                    args=[self._id, self._type, _to_json(self._state)],
                    start_to_close_timeout=timedelta(seconds=10),
                )
            else:
                await temporalio.workflow.execute_local_activity(
                    _emit_task_failed,
                    args=[self._id, self._type, str(exc_val)],
                    start_to_close_timeout=timedelta(seconds=10),
                )
        else:
            if exc_type is None:
                _publish_task_event(
                    CustomTaskCompleted(
                        **create_base_event_fields(),
                        attributes=CustomTaskCompletedAttributes(
                            custom_task_id=self._id,
                            custom_task_type=self._type,
                            payload=JSONPayload(value=_to_json(self._state)),
                        ),
                    )
                )
            else:
                _publish_task_event(
                    CustomTaskFailed(
                        **create_base_event_fields(),
                        attributes=CustomTaskFailedAttributes(
                            custom_task_id=self._id,
                            custom_task_type=self._type,
                            failure=Failure(message=str(exc_val)),
                        ),
                    )
                )

    async def set_state(self, state: T) -> None:
        """
        Update state, emitting InProgress with JSON patch or full payload.

        Events are published in the background for observability.
        """
        if self._state is None:
            raise RuntimeError("Cannot set_state() on task created without state")

        previous = self._state
        self._state = state

        if not _should_publish_event():
            return

        try:
            patches = make_json_patch(previous, state)

            if temporalio.workflow.in_workflow():
                await temporalio.workflow.execute_local_activity(
                    _emit_task_in_progress,
                    args=[self._id, self._type, patches],
                    start_to_close_timeout=timedelta(seconds=10),
                )
            else:
                _publish_task_event(
                    CustomTaskInProgress(
                        **create_base_event_fields(),
                        attributes=CustomTaskInProgressAttributes(
                            custom_task_id=self._id,
                            custom_task_type=self._type,
                            payload=JSONPatchPayload(value=patches),
                        ),
                    )
                )
        except PydanticSerializationError:
            logger.error(
                "Failed JSON patch - state updated locally but not published",
                previous=previous,
                new=state,
                task_id=self._id,
            )

    async def update_state(self, updates: dict[str, Any]) -> None:
        """
        Partial state update (only for BaseModel or dict).

        Events are published in the background for observability.
        """
        if self._state is None:
            raise RuntimeError("Cannot update_state() on task created without state")

        if isinstance(self._state, BaseModel):
            await self.set_state(self._state.model_copy(update=updates))
        elif isinstance(self._state, dict):
            new_dict: dict[str, Any] = self._state.copy()
            new_dict.update(updates)
            await self.set_state(new_dict)  # type: ignore
        else:
            raise TypeError(f"update_state() requires BaseModel or dict, got {type(self._state).__name__}")
