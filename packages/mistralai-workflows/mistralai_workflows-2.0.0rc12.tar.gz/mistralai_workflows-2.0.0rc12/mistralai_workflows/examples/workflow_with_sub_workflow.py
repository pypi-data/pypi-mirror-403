import asyncio
from typing import List
from uuid import uuid4

import pydantic
import structlog

import mistralai_workflows as workflows
from mistralai_workflows.examples.workflow_example import Workflow as WorkflowExample

logger = structlog.getLogger(__name__)


class WorkflowParams(pydantic.BaseModel):
    document_title: str


class Result(pydantic.BaseModel):
    results: List[str] = pydantic.Field(description="List of results")
    execution_id: str = pydantic.Field(description="Execution ID of the sub-workflow")


@workflows.workflow.define(name="example-with-sub-workflow")
class WorkflowExampleWithSubWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, document_title: str) -> Result:
        uuid = uuid4().hex
        res: Result = await workflows.workflow.execute_workflow(
            WorkflowExample, params=WorkflowParams(document_title=document_title), execution_id=uuid
        )
        return Result(results=res.results, execution_id=uuid)


if __name__ == "__main__":
    asyncio.run(workflows.run_worker(workflows=[WorkflowExampleWithSubWorkflow, WorkflowExample]))

    # or for running it as a script
    # asyncio.run(
    #     workflows.workflow.execute_workflow(
    #         WorkflowExampleWithSubWorkflow,
    #         params=WorkflowParams(document_title="test"),
    #     )
    # )
