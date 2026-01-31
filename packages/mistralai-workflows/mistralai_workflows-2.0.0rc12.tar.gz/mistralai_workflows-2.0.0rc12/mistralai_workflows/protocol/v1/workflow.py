import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any, Dict, List, Self, Sequence

from pydantic import BaseModel, Field, model_validator
from temporalio.client import WorkflowExecutionStatus as TemporalWorkflowExecutionStatus

from mistralai_workflows.models import (
    EventProgressStatus,
    EventType,
    NetworkEncodedInput,
    ScheduleDefinition,
    Workflow,
    WorkflowSpecWithTaskQueue,
    WorkflowVersion,
)
from mistralai_workflows.protocol.v1.tempo import TempoGetTraceResponse


class WorkflowSpecsRegisterRequest(BaseModel):
    definitions: List[WorkflowSpecWithTaskQueue] = Field(description="List of workflow specs to register")


class WorkflowDefinitionsRegisterResponse(BaseModel):
    has_conflicts: bool = Field(description="Whether one of the provided workflows has already been registered")


class WorkflowSpecsRegisterResponse(BaseModel):
    workflow_version_ids: List[uuid.UUID] = Field(description="List of workflow IDs that were registered")
    has_conflicts: bool = Field(description="Whether one of the provided workflow specs has already been registered")


class WorkflowMetadata(BaseModel):
    shared_namespace: str | None = Field(default=None, description="Namespace for shared workflows, None if user-owned")


class WorkflowBasicDefinition(BaseModel):
    id: uuid.UUID
    name: str = Field(description="The name of the workflow")
    display_name: str = Field(description="The display name of the workflow")
    description: str | None = Field(default=None, description="A description of the workflow")
    metadata: WorkflowMetadata = Field(default_factory=WorkflowMetadata, description="Workflow metadata")


class WorkflowWithWorkerStatus(Workflow):
    active: bool = Field(description="Whether the workflow is active")


class WorkflowVersionWithWorkerStatus(WorkflowVersion):
    active: bool = Field(description="Whether the workflow version is active")


class WorkflowVersionListResponse(BaseModel):
    workflow_versions: List[WorkflowVersion] = Field(description="A list of workflow versions")
    next_cursor: uuid.UUID | None


class WorkflowGetResponse(BaseModel):
    workflow: WorkflowWithWorkerStatus = Field(description="The workflow spec")


class WorkflowVersionGetResponse(BaseModel):
    workflow_version: WorkflowVersionWithWorkerStatus = Field(description="The workflow version")


class WorkflowExecutionStatus(StrEnum):
    RUNNING = "RUNNING"
    """Workflow execution is running.
    """

    COMPLETED = "COMPLETED"
    """Workflow execution has completed successfully.
    """

    FAILED = "FAILED"
    """Workflow execution has failed.
    """

    CANCELED = "CANCELED"
    """Workflow execution has been canceled.
    """

    TERMINATED = "TERMINATED"
    """Workflow execution has been terminated.
    """

    CONTINUED_AS_NEW = "CONTINUED_AS_NEW"
    """Workflow execution has been continued as new.
    See https://docs.temporal.io/develop/python/continue-as-new#what for more details.
    """

    TIMED_OUT = "TIMED_OUT"
    """Workflow execution has timed out.
    """

    RETRYING_AFTER_ERROR = "RETRYING_AFTER_ERROR"
    """Workflow execution has encountered an error and is retrying.
    This is a custom status not present in Temporal.
    Temporal keeps the workflow in RUNNING state until it succeeds or fails.
    """

    @classmethod
    def from_temporal(cls, status: TemporalWorkflowExecutionStatus) -> "WorkflowExecutionStatus":
        mapping = {
            TemporalWorkflowExecutionStatus.RUNNING: cls.RUNNING,
            TemporalWorkflowExecutionStatus.COMPLETED: cls.COMPLETED,
            TemporalWorkflowExecutionStatus.FAILED: cls.FAILED,
            TemporalWorkflowExecutionStatus.CANCELED: cls.CANCELED,
            TemporalWorkflowExecutionStatus.TERMINATED: cls.TERMINATED,
            TemporalWorkflowExecutionStatus.CONTINUED_AS_NEW: cls.CONTINUED_AS_NEW,
            TemporalWorkflowExecutionStatus.TIMED_OUT: cls.TIMED_OUT,
        }
        return mapping[status]


class WorkflowExecutionWithoutResultResponse(BaseModel):
    workflow_name: str = Field(description="The name of the workflow")
    execution_id: str = Field(description="The ID of the workflow execution")
    parent_execution_id: str | None = Field(None, description="The parent execution ID of the workflow execution")
    root_execution_id: str = Field(description="The root execution ID of the workflow execution")
    status: WorkflowExecutionStatus | None = Field(description="The status of the workflow execution")
    start_time: datetime = Field(description="The start time of the workflow execution")
    end_time: datetime | None = Field(description="The end time of the workflow execution, if available")
    total_duration_ms: int | None = Field(default=None, description="The total duration of the trace in milliseconds")


class WorkflowBasicDefinitionWithMetadata(WorkflowBasicDefinition):
    run_count: int | float = Field(description="The number of times the workflow has been run")
    last_run: WorkflowExecutionWithoutResultResponse | None = Field(
        default=None, description="The last run of the workflow"
    )
    is_active: bool = Field(description="Whether a worker is currently available to run the workflow")
    available_in_chat_assistant: bool = Field(description="Whether the workflow is available in the chat assistant")


class WorkflowListResponseInternal(BaseModel):
    workflows: Sequence[WorkflowBasicDefinitionWithMetadata] = Field(description="A list of workflows")
    next_cursor: uuid.UUID | None


class WorkflowGetResponseInternal(BaseModel):
    workflow: WorkflowBasicDefinitionWithMetadata = Field(description="The workflow")


class WorkflowListResponse(BaseModel):
    workflows: Sequence[WorkflowBasicDefinition] = Field(description="A list of workflows")
    next_cursor: uuid.UUID | None


class WorkflowSpecResponse(BaseModel):
    workflow: WorkflowSpecWithTaskQueue = Field(description="The workflow spec")


class WorkflowUpdateRequest(BaseModel):
    display_name: str | None = Field(None, description="New display name value", max_length=128)
    description: str | None = Field(None, description="New description value")
    available_in_chat_assistant: bool | None = Field(
        None, description="Whether to make the workflow available in the chat assistant"
    )

    @model_validator(mode="after")
    def validate_display_name_not_empty(self) -> Self:
        if self.display_name is not None and self.display_name.strip() == "":
            raise ValueError("display_name cannot be empty")
        return self


class WorkflowUpdateResponse(BaseModel):
    workflow: Workflow = Field(description="Updated workflow")


class WorkflowExecutionRequest(BaseModel):
    execution_id: str | None = Field(
        default=None,
        description="Allows you to specify a custom execution ID. If not provided, a random ID will be generated.",
    )
    input: Dict | NetworkEncodedInput | None = Field(
        description="The input to the workflow. This should be a dictionary that matches the workflow's input schema.",
        default=None,
        json_schema_extra={"additionalProperties": True},
    )
    wait_for_result: bool = Field(
        default=False, description="If true, wait for the workflow to complete and return the result directly."
    )
    timeout_seconds: float | None = Field(
        default=None,
        description="Maximum time to wait for completion when wait_for_result is true.",
    )
    custom_tracing_attributes: dict[str, str] | None = Field(default=None)
    # TODO: more options me be added here, see https://www.notion.so/mistralai/Workflows-API-design-1e06ba59a7fe80349518eaef9f8dbad4?pvs=4#1ec6ba59a7fe80a59052e79f777d3c89

    task_queue: str | None = Field(default=None, description="The name of the task queue to use for the workflow")


class WorkflowExecutionResponse(WorkflowExecutionWithoutResultResponse):
    result: Any | None = Field(description="The result of the workflow execution, if available")


class WorkflowExecutionListResponse(BaseModel):
    executions: List[WorkflowExecutionWithoutResultResponse] = Field(description="A list of workflow executions")
    next_page_token: str | None = Field(
        default=None, description="Token to use for fetching the next page of results. Null if this is the last page."
    )


type WorkflowExecutionTraceSummaryAttributesValues = str | int | float | bool | None
WorkflowExecutionTraceSummaryAttributes = Dict[str, WorkflowExecutionTraceSummaryAttributesValues]


class WorkflowExecutionTraceEvent(BaseModel):
    type: EventType = EventType.EVENT

    name: str = Field(description="Name of the event")
    id: str = Field(description="The ID of the event")
    timestamp_unix_nano: int = Field(description="The timestamp of the event in nanoseconds since the Unix epoch")
    attributes: WorkflowExecutionTraceSummaryAttributes = Field(description="The attributes of the event")
    internal: bool = Field(default=False, description="Whether the event is internal")


class WorkflowExecutionProgressTraceEvent(WorkflowExecutionTraceEvent):
    type: EventType = EventType.EVENT_PROGRESS

    status: EventProgressStatus = Field(default=EventProgressStatus.RUNNING, description="The progress message")
    start_time_unix_ms: int = Field(description="The start time of the event in milliseconds since the Unix epoch")
    end_time_unix_ms: int | None = Field(
        default=None, description="The end time of the event in milliseconds since the Unix epoch"
    )
    error: str | None = Field(default=None, description="The error message, if any")


class WorkflowExecutionTraceSummarySpan(BaseModel):
    span_id: str = Field(description="The ID of the span")
    name: str = Field(description="The name of the span")
    start_time_unix_nano: int = Field(description="The start time of the span in nanoseconds since the Unix epoch")
    end_time_unix_nano: int | None = Field(description="The end time of the span in nanoseconds since the Unix epoch")
    attributes: WorkflowExecutionTraceSummaryAttributes = Field(description="The attributes of the span")
    events: List[WorkflowExecutionTraceEvent] = Field(description="The events of the span")
    children: List["WorkflowExecutionTraceSummarySpan"] = Field(
        default_factory=list, description="The child spans of the span"
    )


class WorkflowExecutionTracOTelResponse(WorkflowExecutionResponse):
    data_source: str = Field(description="The data source of the trace")
    otel_trace_id: str | None = Field(default=None, description="The ID of the trace")
    otel_trace_data: TempoGetTraceResponse | None = Field(default=None, description="The raw OpenTelemetry trace data")


class WorkflowExecutionTraceSummaryResponse(WorkflowExecutionResponse):
    span_tree: WorkflowExecutionTraceSummarySpan | None = Field(default=None, description="The root span of the trace")


class WorkflowExecutionTraceEventsResponse(WorkflowExecutionResponse):
    events: List[WorkflowExecutionTraceEvent | WorkflowExecutionProgressTraceEvent] = Field(
        default_factory=list, description="The events of the workflow execution"
    )


class WorkflowExecutionSyncResponse(BaseModel):
    """Response model for synchronous workflow execution"""

    workflow_name: str = Field(description="Name of the workflow that was executed")
    execution_id: str = Field(description="ID of the workflow execution")
    result: Any = Field(description="The result of the workflow execution")


class SignalWorkflowRequest(BaseModel):
    execution_id: str = Field(description="The ID of the workflow execution")
    signal_name: str = Field(description="The name of the signal to send")
    input: NetworkEncodedInput | Dict[str, Any] | None = Field(
        default=None, description="Input data for the signal, matching its schema"
    )


class SignalWorkflowResponse(BaseModel):
    message: str = Field(default="Signal accepted")


class QueryWorkflowRequest(BaseModel):
    execution_id: str = Field(description="The ID of the workflow execution")
    query_name: str = Field(description="the name of the query to request")
    input: NetworkEncodedInput | Dict[str, Any] | None = Field(
        default=None, description="Input data for the query, matching its schema (Deprecated)"
    )


class QueryWorkflowResponse(BaseModel):
    query_name: str
    result: Any = Field(description="The result of the Query workflow call")


class UpdateWorkflowRequest(BaseModel):
    execution_id: str = Field(description="The ID of the workflow execution")
    update_name: str = Field(description="the name of the update to request")
    input: NetworkEncodedInput | Dict[str, Any] | None = Field(
        default=None, description="Input data for the update, matching its schema (Deprecated)"
    )


class UpdateWorkflowResponse(BaseModel):
    update_name: str
    result: Any = Field(description="The result of the Update workflow call")


class TerminateWorkflowRequest(BaseModel):
    execution_id: str = Field(description="The ID of the workflow execution")


class ResetWorkflowRequest(BaseModel):
    execution_id: str = Field(description="The ID of the workflow execution")
    event_id: int = Field(description="The event ID to reset the workflow execution to")
    reason: str | None = Field(default=None, description="Reason for resetting the workflow execution")
    exclude_signals: bool = Field(
        default=False, description="Whether to exclude signals that happened after the reset point"
    )
    exclude_updates: bool = Field(
        default=False, description="Whether to exclude updates that happened after the reset point"
    )


class SignalInvocationBody(BaseModel):
    name: str = Field(description="The name of the signal to send")
    input: NetworkEncodedInput | Dict[str, Any] | None = Field(
        default=None,
        description="Input data for the signal, matching its schema",
        json_schema_extra={"additionalProperties": True},
    )


class QueryInvocationBody(BaseModel):
    name: str = Field(description="The name of the query to request")
    input: NetworkEncodedInput | Dict[str, Any] | None = Field(
        default=None, description="Input data for the query, matching its schema"
    )


class UpdateInvocationBody(BaseModel):
    name: str = Field(description="The name of the update to request")
    input: NetworkEncodedInput | Dict[str, Any] | None = Field(
        default=None, description="Input data for the update, matching its schema"
    )


class ResetInvocationBody(BaseModel):
    event_id: int = Field(description="The event ID to reset the workflow execution to")
    reason: str | None = Field(default=None, description="Reason for resetting the workflow execution")
    exclude_signals: bool = Field(
        default=False, description="Whether to exclude signals that happened after the reset point"
    )
    exclude_updates: bool = Field(
        default=False, description="Whether to exclude updates that happened after the reset point"
    )


class WorkflowScheduleRequest(BaseModel):
    schedule: ScheduleDefinition = Field(description="The schedule definition")
    workflow_version_id: uuid.UUID | None = Field(
        default=None, description="The ID of the workflow version to schedule"
    )

    workflow_identifier: str | None = Field(default=None, description="The name or ID of the workflow to schedule")
    workflow_task_queue: str | None = Field(default=None, description="The task queue of the workflow to schedule")

    schedule_id: str | None = Field(
        default=None,
        description="Allows you to specify a custom schedule ID. If not provided, a random ID will be generated.",
    )

    @model_validator(mode="after")
    def check_workflow_version_identifiers(self) -> Self:
        has_version_identifier = self.workflow_identifier is not None and self.workflow_task_queue is not None
        if not self.workflow_version_id and not has_version_identifier:
            raise ValueError(
                "Either workflow_version_id or both workflow_name and workflow_task_queue must be provided"
            )
        if self.workflow_version_id and has_version_identifier:
            raise ValueError(
                "Only one of workflow_version_id or workflow_name/workflow_task_queue pair can be provided"
            )
        return self


class WorkflowScheduleResponse(BaseModel):
    schedule_id: str = Field(description="The ID of the schedule")


class WorkflowScheduleListResponse(BaseModel):
    schedules: List[ScheduleDefinition] = Field(description="A list of workflow schedules")


class WorkflowChatAssistantPublishRequest(BaseModel):
    available_in_chat_assistant: bool = Field(description="Whether to publish the workflow to the chat assistant")


class WorkflowChatAssistantPublishResponse(BaseModel):
    workflow: Workflow = Field()
