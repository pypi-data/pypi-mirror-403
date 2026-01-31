import temporalio.workflow

from mistralai_workflows.core.execution.concurrency.executors.chain_executor import execute_chain_activities
from mistralai_workflows.core.execution.concurrency.executors.list_executor import execute_list_activities
from mistralai_workflows.core.execution.concurrency.executors.offset_pagination_executor import (
    execute_offset_pagination_activities,
)
from mistralai_workflows.core.execution.concurrency.types import (
    ChainExecutorParams,
    ListExecutorParams,
    OffsetPaginationExecutorParams,
    WorkflowParams,
    WorkflowResults,
)
from mistralai_workflows.core.workflow import workflow
from mistralai_workflows.exceptions import WorkflowError


@workflow.define(name="__internal_concurrency_workflow__")
class InternalConcurrencyWorkflow:
    """Workflow implementation for concurrent item processing."""

    @workflow.entrypoint
    async def run(self, params: WorkflowParams) -> WorkflowResults:
        """Workflow implementation for concurrent item processing.

        Args:
            params: Parameters for the workflow execution.
        """
        if isinstance(params.params, ListExecutorParams):
            task = execute_list_activities(params.params)
        elif isinstance(params.params, ChainExecutorParams):
            task = execute_chain_activities(params.params)
        elif isinstance(params.params, OffsetPaginationExecutorParams):
            task = execute_offset_pagination_activities(params.params)
        else:
            raise WorkflowError(f"Unknown workflow params type: {type(params.params)}")

        try:
            res = await task
        except Exception as e:
            raise WorkflowError(f"Error executing workflow: {e}") from e

        if isinstance(res, WorkflowResults):
            return res
        elif isinstance(res, WorkflowParams):
            temporalio.workflow.continue_as_new(res)
        else:
            raise WorkflowError(f"Unknown workflow result type: {type(res)}")
