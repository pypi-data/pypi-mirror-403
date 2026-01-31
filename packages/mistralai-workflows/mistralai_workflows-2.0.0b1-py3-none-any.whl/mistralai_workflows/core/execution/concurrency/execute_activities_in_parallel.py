from types import NoneType
from typing import Any, Awaitable, Callable, Dict, List, TypeVar, cast, overload

import structlog
from pydantic import BaseModel

from mistralai_workflows.core.activity import check_is_activity
from mistralai_workflows.core.definition.validation.validator import (
    check_is_valid_type,
    get_function_signature_type_hints,
)
from mistralai_workflows.core.execution.concurrency.concurrency_workflow import InternalConcurrencyWorkflow
from mistralai_workflows.core.execution.concurrency.run_in_batches import run_in_batches
from mistralai_workflows.core.execution.concurrency.types import (
    DEFAULT_MAX_CONCURRENT_EXECUTIONS_PER_WORKER,
    DEFAULT_MAX_CONCURRENT_SCHEDULED_TASKS,
    ChainExecutorParams,
    GetItemFromIndexParams,
    ListExecutorParams,
    OffsetPaginationExecutorParams,
    WorkflowParams,
    WorkflowResults,
)
from mistralai_workflows.core.workflow import workflow

T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)


logger = structlog.get_logger(__name__)


# Batch Executor Overloads
@overload
async def execute_activities_in_parallel(
    activity: Callable[[T], Awaitable[None]],
    *,
    items: List[T],
    max_concurrent_scheduled_tasks: int = DEFAULT_MAX_CONCURRENT_SCHEDULED_TASKS,
) -> None: ...


@overload
async def execute_activities_in_parallel(
    activity: Callable[[T], Awaitable[U]],
    *,
    items: List[T],
    max_concurrent_scheduled_tasks: int = DEFAULT_MAX_CONCURRENT_SCHEDULED_TASKS,
) -> List[U]: ...


# Stream Executor Overloads
@overload
async def execute_activities_in_parallel(
    activity: Callable[[T], Awaitable[None]],
    *,
    get_item_from_prev_item_activity: Callable[[T | None], Awaitable[T | None]],
    extra_params: Dict[str, Any] | None = None,
) -> None: ...


@overload
async def execute_activities_in_parallel(
    activity: Callable[[T], Awaitable[U]],
    *,
    get_item_from_prev_item_activity: Callable[[T | None], Awaitable[T | None]],
    extra_params: Dict[str, Any] | None = None,
) -> List[U]: ...


# Paginated Executor Overloads
@overload
async def execute_activities_in_parallel(
    activity: Callable[[T], Awaitable[None]],
    *,
    get_item_from_index_activity: Callable[[GetItemFromIndexParams], Awaitable[T]],
    n_items: int,
    max_concurrent_executions_per_worker: int = DEFAULT_MAX_CONCURRENT_EXECUTIONS_PER_WORKER,
    max_concurrent_scheduled_tasks: int = DEFAULT_MAX_CONCURRENT_SCHEDULED_TASKS,
    extra_params: Dict[str, Any] | None = None,
) -> None: ...


@overload
async def execute_activities_in_parallel(
    activity: Callable[[T], Awaitable[U]],
    *,
    get_item_from_index_activity: Callable[[GetItemFromIndexParams], Awaitable[T]],
    n_items: int,
    max_concurrent_executions_per_worker: int = DEFAULT_MAX_CONCURRENT_EXECUTIONS_PER_WORKER,
    max_concurrent_scheduled_tasks: int = DEFAULT_MAX_CONCURRENT_SCHEDULED_TASKS,
    extra_params: Dict[str, Any] | None = None,
) -> List[U]: ...


async def execute_activities_in_parallel(
    activity: Callable[[T], Awaitable[None | U]],
    *,
    get_item_from_prev_item_activity: Callable[[T | None], Awaitable[T | None]] | None = None,
    get_item_from_index_activity: Callable[[GetItemFromIndexParams], Awaitable[T]] | None = None,
    items: List[T] | None = None,
    n_items: int | None = None,
    max_concurrent_scheduled_tasks: int = DEFAULT_MAX_CONCURRENT_SCHEDULED_TASKS,
    max_concurrent_executions_per_worker: int = DEFAULT_MAX_CONCURRENT_EXECUTIONS_PER_WORKER,
    extra_params: Dict[str, Any] | None = None,
) -> None | List[U]:
    """Execute activities in parallel using one of three execution patterns.

    **Batch Executor**: Process a known list of items
    ```python
    results = await execute_activities_in_parallel(
        my_activity,
        items=[item1, item2, item3]
    )
    ```

    **Stream Executor**: Process items from a stream/queue
    ```python
    results = await execute_activities_in_parallel(
        my_activity,
        get_item_from_prev_item_activity=get_next_item
    )
    ```

    **Paginated Executor**: Process items by fetching pages/chunks
    ```python
    results = await execute_activities_in_parallel(
        my_activity,
        get_item_from_index_activity=get_page,
        n_items=1000
    )
    ```

    Args:
        activity: The activity function to execute on each item
        items: List of items to process (Batch Executor)
        get_item_from_prev_item_activity: Function to get next item from previous (Stream Executor)
        get_item_from_index_activity: Function to get item by index (Paginated Executor)
        max_concurrent_scheduled_tasks: Maximum concurrent scheduled tasks
        max_concurrent_executions_per_worker: Maximum concurrent executions per worker
        extra_params: Extra parameters to pass to the activity

    Returns:
        None if activity returns None, otherwise List of results

    Raises:
        ValueError: If activity is not decorated with @workflows.activity
        ValueError: If invalid parameter types are provided
        ValueError: If no execution pattern is specified
    """
    # Validate activity
    if not check_is_activity(activity):
        raise ValueError("`activity` must be an activity, please decorate it with @workflows.activity")

    user_params_dict, activity_return_type = get_function_signature_type_hints(activity, is_method=False)
    activity_param_type = next(iter(user_params_dict.values())) if user_params_dict else None
    if not activity_param_type or not check_is_valid_type(activity_param_type, BaseModel):
        raise ValueError(
            f"`activity` must take a single parameter of type pydantic BaseModel, got {activity_param_type}"
        )
    if activity_return_type is not NoneType and not check_is_valid_type(activity_return_type, BaseModel):
        raise ValueError(f"`activity` must return a pydantic BaseModel or None, got {activity_return_type}")

    result: WorkflowResults

    # List Executor
    if items is not None:
        result = await workflow.execute_workflow(
            InternalConcurrencyWorkflow,
            WorkflowParams(
                params=ListExecutorParams(
                    activity_name=activity.__name__,
                    items=items,
                    max_concurrent_scheduled_tasks=max_concurrent_scheduled_tasks,
                    extra_params=extra_params,
                )
            ),
        )

    # Chain Executor
    elif get_item_from_prev_item_activity is not None:
        if not check_is_activity(get_item_from_prev_item_activity):
            raise ValueError(
                "`get_item_from_prev_item_activity` must be an activity, please decorate it with @workflows.activity"
            )

        user_params_dict, return_type = get_function_signature_type_hints(
            get_item_from_prev_item_activity, is_method=False
        )
        param_type = next(iter(user_params_dict.values())) if user_params_dict else None

        if param_type is None or not check_is_valid_type(param_type, activity_param_type, allow_optional=True):
            raise ValueError(
                f"`get_item_from_prev_item_activity` must take a single parameter of type "
                f"{activity_param_type}, got {param_type}"
            )

        if return_type is None or not check_is_valid_type(return_type, activity_param_type, allow_optional=True):
            raise ValueError(
                f"`get_item_from_prev_item_activity` must return a {activity_param_type}, got {return_type}"
            )

        result = await workflow.execute_workflow(
            InternalConcurrencyWorkflow,
            WorkflowParams(
                params=ChainExecutorParams(
                    activity_name=activity.__name__,
                    get_item_from_prev_item_activity_name=get_item_from_prev_item_activity.__name__,
                )
            ),
        )

    # Offset Pagination Executor
    elif get_item_from_index_activity is not None and n_items is not None:
        if not check_is_activity(get_item_from_index_activity):
            raise ValueError(
                "`get_item_from_index_activity` must be an activity, please decorate it with @workflows.activity"
            )

        user_params_dict, return_type = get_function_signature_type_hints(get_item_from_index_activity, is_method=False)
        param_type = next(iter(user_params_dict.values())) if user_params_dict else None

        if param_type is None or not check_is_valid_type(param_type, GetItemFromIndexParams):
            raise ValueError(
                f"`get_item_from_index_activity` must take a single parameter of type "
                f"{GetItemFromIndexParams}, got {param_type}"
            )

        if return_type is None or not check_is_valid_type(return_type, activity_param_type, allow_optional=True):
            raise ValueError(f"`get_item_from_index_activity` must return a {activity_param_type}, got {return_type}")

        logger.info("Starting offset pagination executor", n_items=n_items)

        default_params = OffsetPaginationExecutorParams(
            activity_name=activity.__name__,
            get_item_from_index_activity_name=get_item_from_index_activity.__name__,
            n_items=n_items,
            max_concurrent_scheduled_tasks=max_concurrent_scheduled_tasks,
            batch_size=max_concurrent_executions_per_worker,
            extra_params=extra_params,
        )
        dict_default_params = default_params.model_dump()

        results = await run_in_batches(
            fct=lambda params: workflow.execute_workflow(InternalConcurrencyWorkflow, params),
            get_params_for_batch=lambda idx, batch_size: WorkflowParams(
                # construct without validation to avoid temporal timeout
                params=OffsetPaginationExecutorParams.model_construct(
                    **{
                        **dict_default_params,
                        "n_items": idx + batch_size,
                        "prev_idx": idx - 1,
                    }
                )
            ),
            n_items=n_items,
        )

        # construct without validation to avoid temporal timeout
        result = WorkflowResults.model_construct(values=[item for batch in results for item in batch.values])

    else:
        raise ValueError(
            "Must specify one execution pattern: 'items' (list), "
            "'get_item_from_prev_item_activity' (chain), or 'get_item_from_index_activity' (offset pagination)"
        )

    # Return results
    if activity_return_type is NoneType:
        return None
    else:
        assert issubclass(activity_return_type, BaseModel)
        return cast(List[U], [activity_return_type.model_validate(value) for value in result.values])
