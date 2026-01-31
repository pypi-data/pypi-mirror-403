from typing import Any

import pytest
from pydantic import BaseModel, Field

from mistralai_workflows import activity, workflow
from mistralai_workflows.core.definition.workflow_definition import get_workflow_definition

from .utils import create_test_worker


class PageParams(BaseModel):
    offset: int = Field(default=0)
    limit: int = Field(default=100)
    total_processed: int = Field(default=0)


class ProcessingResult(BaseModel):
    total_processed: int
    status: str = Field(default="completed")


@activity()
async def fetch_items(offset: int, limit: int) -> list[str]:
    if offset >= 500:
        return []
    items = [f"item_{i}" for i in range(offset, min(offset + limit, 500))]
    return items


@activity()
async def process_items(items: list[str]) -> int:
    return len(items)


@workflow.define(name="test-continue-as-new-basic")
class BasicContinueAsNewWorkflow:
    @workflow.entrypoint
    async def run(self, params: PageParams) -> ProcessingResult:
        items = await fetch_items(params.offset, params.limit)
        if not items:
            return ProcessingResult(total_processed=params.total_processed)
        processed_count = await process_items(items)
        next_params = PageParams(
            offset=params.offset + params.limit,
            limit=params.limit,
            total_processed=params.total_processed + processed_count,
        )
        return await self.run(next_params)


@workflow.define(name="test-continue-as-new-small-batches")
class SmallBatchContinueAsNewWorkflow:
    @workflow.entrypoint
    async def run(self, params: PageParams) -> ProcessingResult:
        items = await fetch_items(params.offset, params.limit)
        if not items:
            return ProcessingResult(total_processed=params.total_processed)
        processed_count = await process_items(items)
        next_params = PageParams(
            offset=params.offset + params.limit,
            limit=params.limit,
            total_processed=params.total_processed + processed_count,
        )
        return await self.run(next_params)


class TestContinueAsNew:
    @pytest.mark.asyncio
    async def test_completes_with_no_items(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env,
            workflows=[BasicContinueAsNewWorkflow],
            activities=[fetch_items, process_items],
        ):
            workflow_def = get_workflow_definition(BasicContinueAsNewWorkflow)
            assert workflow_def is not None
            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                PageParams(offset=500, limit=100, total_processed=0).model_dump(),
                id="test-continue-as-new-no-items",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert isinstance(result, dict)
            assert result["total_processed"] == 0
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_processes_multiple_pages(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env,
            workflows=[SmallBatchContinueAsNewWorkflow],
            activities=[fetch_items, process_items],
        ):
            workflow_def = get_workflow_definition(SmallBatchContinueAsNewWorkflow)
            assert workflow_def is not None
            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                PageParams(offset=0, limit=50, total_processed=0).model_dump(),
                id="test-continue-as-new-multiple-pages",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert isinstance(result, dict)
            assert result["total_processed"] == 500
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_accumulates_state(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env,
            workflows=[BasicContinueAsNewWorkflow],
            activities=[fetch_items, process_items],
        ):
            workflow_def = get_workflow_definition(BasicContinueAsNewWorkflow)
            assert workflow_def is not None
            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                PageParams(offset=200, limit=100, total_processed=200).model_dump(),
                id="test-continue-as-new-state",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert isinstance(result, dict)
            assert result["total_processed"] == 500
            assert result["status"] == "completed"
