import asyncio
from types import NoneType

import temporalio
import temporalio.workflow
from pydantic import BaseModel

from mistralai_workflows.core.activity import get_wrapped_activity
from mistralai_workflows.core.definition.validation.validator import (
    check_is_valid_type,
    get_function_signature_type_hints,
)
from mistralai_workflows.core.execution.concurrency.types import (
    ExtraItemParams,
    ListExecutorParams,
    WorkflowParams,
    WorkflowResults,
)
from mistralai_workflows.core.execution.concurrency.utils import dict_to_workflow_results, workflow_results_to_dict


async def execute_list_activities(
    params: ListExecutorParams,
) -> WorkflowParams | WorkflowResults:
    """Execute activities in parallel for a list of known items.

    This executor processes a predefined list of items all at once.
    Use this when you have all items available upfront.

    Args:
        params: List executor parameters containing the items to process

    Returns:
        WorkflowResults if processing is complete, or WorkflowParams for continuation
    """
    activity = get_wrapped_activity(params.activity_name)

    assert activity is not None

    user_params_dict, return_type = get_function_signature_type_hints(activity, is_method=False)
    param_type = next(iter(user_params_dict.values())) if user_params_dict else None
    assert param_type is not None and check_is_valid_type(param_type, BaseModel)

    results_as_dict = workflow_results_to_dict(params.prev_results or WorkflowResults(values=[]))

    limit = asyncio.Semaphore(params.max_concurrent_scheduled_tasks)
    idx = params.prev_idx + 1

    async def run_activity(relative_idx: int) -> None:
        # this sleep allow us to limit the number of concurrent workflow tasks in order to avoid the following error:
        # `Error while completing workflow activation error=status: InvalidArgument, message: "PendingActivitiesLimitExceeded: the number of pending activities, 2000, has reached the per-workflow limit of 2000"`  # noqa: E501
        if temporalio.workflow.in_workflow():
            await temporalio.workflow.sleep(0)

        limit.release()
        current_item = params.items[relative_idx]
        current_item = param_type.model_validate(current_item)
        if issubclass(param_type, ExtraItemParams):
            current_item.extra_params = params.extra_params
        result = await activity(current_item)
        if return_type is not NoneType:
            results_as_dict[idx + relative_idx] = result

    relative_idx = 0
    async with asyncio.TaskGroup() as tg:
        while relative_idx < len(params.items):
            await limit.acquire()
            tg.create_task(run_activity(relative_idx))

            if temporalio.workflow.in_workflow() and temporalio.workflow.info().is_continue_as_new_suggested():
                break

            relative_idx += 1

    if relative_idx < len(params.items):
        # Need to continue processing remaining items
        return WorkflowParams(
            params=ListExecutorParams(
                activity_name=params.activity_name,
                items=params.items[relative_idx + 1 :],
                prev_idx=idx + relative_idx,
                max_concurrent_scheduled_tasks=params.max_concurrent_scheduled_tasks,
                prev_results=dict_to_workflow_results(results_as_dict),
                extra_params=params.extra_params,
            )
        )
    else:
        # All items processed
        return dict_to_workflow_results(results_as_dict)
