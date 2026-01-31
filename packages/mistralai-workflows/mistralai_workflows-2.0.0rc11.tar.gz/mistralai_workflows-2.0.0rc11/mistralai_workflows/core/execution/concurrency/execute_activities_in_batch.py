import asyncio
from types import NoneType
from typing import Any, Dict

from mistralai_workflows.core.activity import activity, get_wrapped_activity
from mistralai_workflows.core.definition.validation.validator import get_function_signature_type_hints
from mistralai_workflows.core.execution.concurrency.types import (
    ExecuteActivityInBatchParams,
    ExecuteActivityInBatchResult,
    GetItemFromIndexParams,
)


@activity(name="__internal_execute_activity_in_batch")
async def execute_activity_in_batch(params: ExecuteActivityInBatchParams) -> ExecuteActivityInBatchResult:
    """Get the activity and run it."""

    activity = get_wrapped_activity(params.activity_name)
    get_item_from_index_activity = get_wrapped_activity(params.get_item_from_index_activity_name)

    assert activity is not None
    assert get_item_from_index_activity is not None

    _, return_type = get_function_signature_type_hints(activity, is_method=False)

    results_as_dict: Dict[int, Any] = {}

    async def get_and_run_activity(idx: int) -> None:
        current_item = await get_item_from_index_activity(
            GetItemFromIndexParams(idx=idx, extra_params=params.extra_params)
        )
        result = await activity(current_item)
        if return_type is not NoneType:
            results_as_dict[idx] = result

    await asyncio.gather(*[get_and_run_activity(idx) for idx in range(params.idx, params.idx + params.batch_size)])

    return ExecuteActivityInBatchResult(results=results_as_dict)
