import uuid
from enum import StrEnum
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .handlers import QueryDefinition, SignalDefinition, UpdateDefinition
from .schedule import ScheduleDefinition


class WorkflowCodeDefinition(BaseModel):
    input_schema: Dict[str, Any] | None = Field(
        default=None,
        description="Input schema of the workflow's run method",
        json_schema_extra={"additionalProperties": True},
    )  # note change to Dict[str, Any] which is closer to real Json type.
    output_schema: Dict[str, Any] | None = Field(
        default=None,
        description="Output schema of the workflow's run method",
        json_schema_extra={"additionalProperties": True},
    )
    signals: List[SignalDefinition] = Field(default_factory=list, description="Signal handlers defined by the workflow")
    queries: List[QueryDefinition] = Field(default_factory=list, description="Query handlers defined by the workflow")
    updates: List[UpdateDefinition] = Field(default_factory=list, description="Update handlers defined by the workflow")


class WorkflowSpec(WorkflowCodeDefinition):
    name: str = Field(description="Name of the workflow")
    display_name: str | None = Field(default=None, description="Display name of the workflow")
    description: str | None = Field(default=None, description="Description of the workflow")
    schedules: List[ScheduleDefinition] = Field(default_factory=list, description="Schedules defined by the workflow")


class WorkflowSpecWithTaskQueue(WorkflowSpec):
    task_queue: str = Field(description="Task queue name for the workflow")


class WorkflowType(StrEnum):
    CODE = "code"
    # DSL = "dsl"


class Workflow(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier of the workflow")
    name: str = Field(description="Name of the workflow")
    display_name: str = Field(description="Display name of the workflow")
    type: WorkflowType = Field(description="Type of the workflow")
    description: str | None = Field(default=None, description="Description of the workflow")
    customer_id: uuid.UUID = Field(description="Customer ID of the workflow")
    workspace_id: uuid.UUID = Field(description="Workspace ID of the workflow")
    shared_namespace: str | None = Field(
        default=None, description="Reserved namespace for shared workflows (e.g., 'shared:my-shared-workflow')"
    )
    available_in_chat_assistant: bool = Field(description="Whether the workflow is available in chat assistant")


class WorkflowVersion(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier of the workflow version")
    task_queue: str = Field(description="Project name of the workflow")
    definition: WorkflowCodeDefinition
    workflow_id: uuid.UUID = Field(description="Workflow ID of the workflow")
    workflow: Workflow | None = Field(default=None, description="Workflow of the workflow version")
    compatible_with_chat_assistant: bool = Field(
        default=False, description="Whether the workflow is compatible with chat assistant"
    )
