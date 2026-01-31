import asyncio
import datetime
import functools
import uuid
import warnings
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    TypeVar,
    cast,
)

import structlog
import temporalio
import temporalio.activity
import temporalio.client
import temporalio.common
import temporalio.workflow
from opentelemetry import trace
from opentelemetry.trace import format_trace_id

from mistralai_workflows.core.config.config import config
from mistralai_workflows.core.tracing.otel_config import _get_calling_module_name
from mistralai_workflows.models import (
    EventAttributes,
    EventProgressStatus,
    EventSpanType,
    EventType,
    SearchAttributes,
)

logger = structlog.getLogger(__name__)
tracer = trace.get_tracer(_get_calling_module_name())


CUSTOM_TRACING_ATTRIBUTES = "custom_tracing_attributes"


def get_otel_trace_id(workflow_description: temporalio.client.WorkflowExecutionDescription) -> str | None:
    otel_trace_id_values = workflow_description.search_attributes.get(SearchAttributes.otel_trace_id)
    if otel_trace_id_values and len(otel_trace_id_values) > 0 and isinstance(otel_trace_id_values[0], str):
        otel_trace_id = otel_trace_id_values[0]
    else:
        otel_trace_id = None

    return otel_trace_id


async def set_otel_trace_id_in_current_workflow_execution() -> None:
    if not temporalio.workflow.in_workflow():
        return

    info = temporalio.workflow.info()
    span = trace.get_current_span()
    ctx = span.get_span_context()
    trace_id = format_trace_id(ctx.trace_id)

    temporalio.workflow.upsert_search_attributes(
        temporalio.common.TypedSearchAttributes(
            [
                temporalio.common.SearchAttributePair(
                    key=temporalio.common.SearchAttributeKey.for_keyword(SearchAttributes.otel_trace_id),
                    value=trace_id,
                )
            ]
        )  # type: ignore
    )

    logger.debug("Set OpenTelemetry trace ID in workflow execution", trace_id=trace_id, execution_id=info.run_id)


def _get_event_id() -> str:
    return uuid.uuid4().hex


def get_span_attributes(
    event_type: str,
    span_type: EventSpanType,
    internal: bool = False,
    event_id: str | None = None,
    custom_attributes: dict[str, Any] | None = None,
) -> dict:
    attributes: Dict[str, Any] = {
        EventAttributes.type: span_type,
        EventAttributes.event_type: event_type,
        EventAttributes.id: event_id or _get_event_id(),
        EventAttributes.internal: internal,
    }

    if temporalio.activity.in_activity():
        activity_info = temporalio.activity.info()
        attributes[EventAttributes.workflow_type] = activity_info.workflow_type
        attributes[EventAttributes.activity_execution_id] = activity_info.activity_id
        attributes[EventAttributes.activity_attempt] = activity_info.attempt
        attributes[EventAttributes.activity_max_attempts] = config.worker.retry_policy_max_attempts

    if temporalio.workflow.in_workflow():
        workflow_info = temporalio.workflow.info()
        attributes[EventAttributes.workflow_type] = workflow_info.workflow_type

    if custom_attributes:
        for key, value in custom_attributes.items():
            attributes[f"{EventAttributes.custom_prefix}.{key}"] = value

    return attributes


def _record_event(
    event_name: str,
    attributes: Dict[str, Any] | None = None,
    event_type: EventType = EventType.EVENT,
    event_id: str | None = None,
    internal: bool = False,
) -> None:
    """Records an event in the current span.

    Args:
        event_name (str): The name of the event.
        attributes (Dict[str, Any] | None, optional): Additional attributes to record with the event.
                                                         They are directly available in the event. Defaults to None.
        event_type (EventType, optional): The type of the event. Defaults to EventType.EVENT.
                                          This is used to categorize events.
                                          This is unlikely to be used by the user.
        event_id (str | None, optional): The ID of the event. Defaults to None.
                                            If not provided, a random UUID will be generated.
        internal (bool, optional): Whether the event is internal. Defaults to False.
                                   If True, the event will be recorded as an internal event.
                                   Internal events are supposed to be only used for debugging purposes.
    """
    if temporalio.workflow.in_workflow() and temporalio.workflow.unsafe.is_replaying():
        return

    if attributes is None:
        attributes = {}

    with tracer.start_as_current_span(f"CustomEvent:{event_name}") as span:
        logger.debug("Recording event", event_name=event_name, attributes=attributes)
        span.add_event(
            event_name,
            {
                **attributes,
                **get_span_attributes(
                    event_type=event_name, span_type=EventSpanType.event, event_id=event_id, internal=internal
                ),
                EventAttributes.type: event_type,
            },
        )


def record_event(event_name: str, attributes: Dict[str, Any] | None = None, internal: bool = False) -> None:
    """Records an event in the current span.

    .. deprecated::
        This function is deprecated and will be removed in a future version.
        For business events, use the Task system from mistralai_workflows.task instead.

    Args:
        event_name (str): The name of the event.
        attributes (Dict[str, Any] | None, optional): Additional attributes to record with the event.
                                                         They are directly available in the event. Defaults to None.
        internal (bool, optional): Whether the event is internal. Defaults to False.
    """
    warnings.warn(
        "record_event is deprecated and will be removed in a future version. "
        "For business events, use the Task system from mistralai_workflows.task instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if attributes is None:
        attributes = {}

    _record_event(event_name, attributes, event_type=EventType.EVENT, internal=internal)


@contextmanager
def record_event_progress(
    execution_name: str, attributes: Dict[str, Any] | None = None, internal: bool = False
) -> Generator[None, None, None]:
    """Records an event progress. Event progress is a special type of event that is used to track the progress of a
    long-running operation.

    .. deprecated::
        This function is deprecated and will be removed in a future version.
        For business events, use the Task system from mistralai_workflows.task instead.

    Example:
    ```
    with record_event_progress("my_long_running_operation"):
        # do something
        pass
    ```
    Will record two events:
    - `my_long_running_operation` with status `RUNNING` at the start of the block
    - `my_long_running_operation` with status `COMPLETED` at the end of the block
    If an exception is raised, the second event will have status `FAILED` and the exception will be recorded.

    Args:
        execution_name (str): The name of the execution. This will be used as the event name.
        attributes (Dict[str, Any] | None, optional): Additional attributes to record with the event.
                                                         They are directly available in the event. Defaults to None.
        internal (bool, optional): Whether the event is internal. Defaults to False.
                                   If True, the event will be recorded as an internal event.
                                   Internal events are supposed to be only used for debugging purposes.
    """
    warnings.warn(
        "record_event_progress is deprecated and will be removed in a future version. "
        "For business events, use the Task system from mistralai_workflows.task instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if attributes is None:
        attributes = {}

    event_id = _get_event_id()

    attributes = {
        **attributes,
        EventAttributes.progress_status: EventProgressStatus.RUNNING,
        EventAttributes.progress_start_time_unix_ms: int(
            datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000
        ),
    }

    _record_event(execution_name, attributes, event_type=EventType.EVENT_PROGRESS, event_id=event_id, internal=internal)

    try:
        logger.debug(f"[{EventType.EVENT_PROGRESS}] {execution_name} execution started...")
        yield

        attributes[EventAttributes.progress_status] = EventProgressStatus.COMPLETED
        attributes[EventAttributes.progress_end_time_unix_ms] = int(
            datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000
        )

        _record_event(
            execution_name, attributes, event_type=EventType.EVENT_PROGRESS, event_id=event_id, internal=internal
        )
        logger.debug(f"[{EventType.EVENT_PROGRESS}] {execution_name} execution completed.")
    except Exception as e:
        attributes[EventAttributes.progress_status] = EventProgressStatus.FAILED
        attributes[EventAttributes.progress_end_time_unix_ms] = int(
            datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000
        )
        attributes[EventAttributes.progress_error] = str(e)

        _record_event(
            execution_name, attributes, event_type=EventType.EVENT_PROGRESS, event_id=event_id, internal=internal
        )
        logger.error(f"[{EventType.EVENT_PROGRESS}] {execution_name} execution failed.")
        raise e


CallableType = TypeVar("CallableType", bound=Callable[..., Any])


def record_event_progress_function(
    func: CallableType, execution_name: str, attributes: Dict[str, Any] | None = None, internal: bool = False
) -> CallableType:
    """Decorator to record event progress for a function. Similar to do `record_event_progress` inside the function. See
    `record_event_progress` for more details.
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with record_event_progress(execution_name, attributes, internal):
                return await func(*args, **kwargs)

        return cast(CallableType, async_wrapper)
    else:

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with record_event_progress(execution_name, attributes, internal):
                return func(*args, **kwargs)

        return cast(CallableType, sync_wrapper)
