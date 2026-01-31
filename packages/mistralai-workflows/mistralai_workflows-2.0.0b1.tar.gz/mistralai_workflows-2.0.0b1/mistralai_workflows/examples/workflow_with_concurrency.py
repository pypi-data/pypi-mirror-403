"""
workflows concurrency examples showcasing three execution patterns:

1. **List Executor** - Process a known list of items
2. **Chain Executor** - Process items sequentially from a stream/queue (token-based pagination)
3. **Offset Pagination Executor** - Process items by fetching pages/chunks by index
"""

import asyncio
from typing import Any, List

import pydantic
import structlog

import mistralai_workflows as workflows

logger = structlog.getLogger(__name__)

NB_ITEMS = 10


class ItemData(pydantic.BaseModel):
    item_id: int
    value: str
    extra_data: Any | None = None


class ActivityResult(pydantic.BaseModel):
    processed_value: str
    item_id: int
    extra_data: Any | None = None


class Result(pydantic.BaseModel):
    results: List[ActivityResult]


@workflows.activity()
async def process_item_activity(item: ItemData) -> ActivityResult:
    """Activity that processes a single item."""
    await asyncio.sleep(0.1)  # Simulate processing
    processed_value = f"processed_{item.value}"
    logger.info("Processed item", item_id=item.item_id, value=processed_value)
    return ActivityResult(processed_value=processed_value, item_id=item.item_id, extra_data=item.extra_data)


# Chain Executor Activities
@workflows.activity()
async def get_next_item_from_chain(prev_item: ItemData | None) -> ItemData | None:
    """Chain executor: Get next item from previous item (like S3 ListObjects with continuation token)."""
    if prev_item is None:
        # First item
        return ItemData(item_id=0, value="item_0")

    next_id = prev_item.item_id + 1
    if next_id >= NB_ITEMS:
        return None  # No more items

    return ItemData(item_id=next_id, value=f"item_{next_id}")


# Offset Pagination Executor Activities
@workflows.activity()
async def get_item_by_index(params: workflows.GetItemFromIndexParams) -> ItemData:
    """Offset pagination executor: Get item by index/page number (like REST API with page numbers)."""
    return ItemData(item_id=params.idx, value=f"item_{params.idx}", extra_data=params.extra_params)


@workflows.workflow.define(name="list-executor-example")
class ListExecutorExample:
    """
    List Executor Example - Process a known list of items.

    Use this when you have all items upfront (e.g., from a database query,
    file contents, or API response that returns all items at once).
    """

    @workflows.workflow.entrypoint
    async def run(self, extra_params: Any | None = None) -> Result:
        # Create a known list of items to process
        items = [ItemData(item_id=i, value=f"item_{i}") for i in range(NB_ITEMS)]

        results = await workflows.execute_activities_in_parallel(
            activity=process_item_activity,
            items=items,
        )

        return Result(results=results)


@workflows.workflow.define(name="chain-executor-example")
class ChainExecutorExample:
    """
    Chain Executor Example - Process items from a stream/queue with token-based pagination.

    Use this for APIs like S3 ListObjects, DynamoDB Scan, or any pagination
    that uses continuation tokens rather than page numbers.
    """

    @workflows.workflow.entrypoint
    async def run(self, extra_params: Any | None = None) -> Result:
        results = await workflows.execute_activities_in_parallel(
            activity=process_item_activity,
            get_item_from_prev_item_activity=get_next_item_from_chain,
        )

        return Result(results=results)


@workflows.workflow.define(name="offset-pagination-executor-example")
class OffsetPaginationExecutorExample:
    """
    Offset Pagination Executor Example - Process items by fetching pages/chunks by index.

    Use this for traditional REST API pagination with page numbers,
    SQL database chunking with OFFSET/LIMIT, or any index-based fetching.
    """

    @workflows.workflow.entrypoint
    async def run(self, extra_params: Any | None = None) -> Result:
        results = await workflows.execute_activities_in_parallel(
            activity=process_item_activity,
            get_item_from_index_activity=get_item_by_index,
            n_items=NB_ITEMS,
            extra_params=extra_params,
        )

        return Result(results=results)


if __name__ == "__main__":
    """
    This example demonstrates three different concurrency execution patterns in workflows:

    1. LIST EXECUTOR - Process a known collection of items
       Use case: You have all items upfront (database query results, file contents, API response)
       Example: Process all users from a database query, resize a batch of uploaded images

    2. CHAIN EXECUTOR - Process items with token-based pagination
       Use case: APIs that use continuation tokens instead of page numbers
       Examples:
         - AWS S3 ListObjects (uses ContinuationToken)
         - DynamoDB Scan/Query (uses LastEvaluatedKey)
         - Azure Blob Storage (uses marker)

    3. OFFSET PAGINATION EXECUTOR - Process items with page-based pagination
       Use case: Traditional REST APIs with page numbers or SQL with OFFSET/LIMIT
       Examples:
         - REST API: GET /users?page=1&limit=20, GET /users?page=2&limit=20
         - Database: SELECT * FROM users LIMIT 20 OFFSET 0, SELECT * FROM users LIMIT 20 OFFSET 20
         - File processing: Read file in 1MB chunks by byte offset

    All patterns handle Temporal's continue-as-new automatically for large datasets.
    """

    # Run all three examples
    asyncio.run(workflows.run_worker([ListExecutorExample, ChainExecutorExample, OffsetPaginationExecutorExample]))
