import asyncio
from types import NoneType
from typing import Any

import temporalio
import temporalio.workflow
from pydantic import BaseModel

from mistralai_workflows.core.activity import get_wrapped_activity
from mistralai_workflows.core.definition.validation.validator import (
    check_is_valid_type,
    get_function_signature_type_hints,
)
from mistralai_workflows.core.execution.concurrency.types import ChainExecutorParams, WorkflowParams, WorkflowResults
from mistralai_workflows.core.execution.concurrency.utils import dict_to_workflow_results, workflow_results_to_dict


async def execute_chain_activities(
    params: ChainExecutorParams,
) -> WorkflowParams | WorkflowResults:
    """Execute activities in parallel for a chain of items.

    This executor processes items sequentially by fetching the next item
    from the previous one. Use this for token-based pagination (S3, DynamoDB)
    where each response contains the key to get the next batch.

    Args:
        params: Chain executor parameters containing the chain configuration

    Returns:
        WorkflowResults if processing is complete, or WorkflowParams for continuation
    """
    activity = get_wrapped_activity(params.activity_name)
    get_item_from_prev_item_activity = get_wrapped_activity(params.get_item_from_prev_item_activity_name)

    assert activity is not None
    assert get_item_from_prev_item_activity is not None

    user_params_dict, return_type = get_function_signature_type_hints(activity, is_method=False)
    param_type = next(iter(user_params_dict.values())) if user_params_dict else None
    assert param_type is not None and check_is_valid_type(param_type, BaseModel)

    current_item = params.prev_item
    if current_item and not isinstance(current_item, param_type):
        current_item = param_type.model_validate(current_item)

    results_as_dict = workflow_results_to_dict(params.prev_results or WorkflowResults(values=[]))
    idx = params.prev_idx + 1
    done = False

    async def run_activity(idx: int, item: Any) -> None:
        result = await activity(item)
        if return_type is not NoneType:
            results_as_dict[idx] = result

    async with asyncio.TaskGroup() as tg:
        while True:
            current_item = await get_item_from_prev_item_activity(current_item)

            if current_item is None:
                done = True
                break

            tg.create_task(run_activity(idx, current_item))

            if temporalio.workflow.in_workflow() and temporalio.workflow.info().is_continue_as_new_suggested():
                break

            idx += 1

    if done:
        # Stream is exhausted
        return dict_to_workflow_results(results_as_dict)
    else:
        # Need to continue streaming
        return WorkflowParams(
            params=ChainExecutorParams(
                activity_name=params.activity_name,
                get_item_from_prev_item_activity_name=params.get_item_from_prev_item_activity_name,
                prev_idx=idx,
                prev_item=current_item,
                prev_results=dict_to_workflow_results(results_as_dict),
            )
        )
