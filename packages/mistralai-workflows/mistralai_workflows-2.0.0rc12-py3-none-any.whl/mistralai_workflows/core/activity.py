import datetime
import inspect
from contextvars import ContextVar
from functools import partial, singledispatch, wraps
from typing import Any, Callable, Dict, List, TypeVar, cast

import structlog
import temporalio
import temporalio.activity
import temporalio.common
import temporalio.workflow
import tenacity

from mistralai_workflows.core.config.config import INTERNAL_ACTIVITY_PREFIX, config
from mistralai_workflows.core.definition.validation.validator import (
    get_function_signature_type_hints,
    raise_if_function_has_invalid_return_type,
    raise_if_function_has_invalid_signature,
    raise_if_function_has_invalid_usage,
)
from mistralai_workflows.core.dependencies.dependency_injector import DependencyInjector
from mistralai_workflows.core.events.event_context import (
    BackgroundEventPublisher,
    EventContext,
    _background_event_publisher,
)
from mistralai_workflows.core.execution.local_activity import is_local_activity_enabled
from mistralai_workflows.core.execution.sticky_session.sticky_worker_session import (
    set_activity_as_sticky_to_worker,
)
from mistralai_workflows.core.rate_limiting.rate_limit import (
    RateLimit,
    get_rate_limit,
    local_wait_rate_limit,
    set_rate_limit,
)
from mistralai_workflows.core.utils.contextvars import reset_contextvar, unwrap_contextual_result
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException

logger = structlog.get_logger(__name__)


_temporal_activities: List[Callable] = []
_activities_by_name: Dict[str, Callable] = {}

context_var_task_queue: ContextVar[str | None] = ContextVar("task_queue", default=None)
_context_var_is_inside_activity: ContextVar[bool] = ContextVar("is_inside_activity", default=False)

T = TypeVar("T", bound=Callable[..., Any] | type)


def activity(
    start_to_close_timeout: datetime.timedelta = datetime.timedelta(minutes=5),
    retry_policy_max_attempts: int | None = None,
    retry_policy_backoff_coefficient: float | None = None,
    display_name: str | None = None,
    name: str | None = None,
    sticky_to_worker: bool = False,
    rate_limit: RateLimit | None = None,
    _skip_registering: bool = False,
    activity_name: str | None = None,
    _extends: Callable | None = None,
    _allow_reserved_name: bool = False,
) -> Callable[[T], T]:
    """
    Decorator for defining activities with configuration options.

    This decorator transforms a regular Python function into an activity with
    various configuration options for timeouts, retries, and worker scoping.

    Args:
        start_to_close_timeout: Maximum time the activity is allowed to execute.
        retry_policy_max_attempts: Maximum number of retry attempts.
        retry_policy_backoff_coefficient: Backoff coefficient for retry delays.
        display_name: Optional display name for the activity when recording events.
        name: Optional name override for the activity. Defaults to function name.
        sticky_to_worker: Whether the activity should be sticky to a worker.
                          See `workflow_sdk.worker.sticky_worker_session` for more details.
        rate_limit: Set a rate limit for the activity across all workers.
                    See `workflow_sdk.worker.rate_limit.RateLimit` for more details.
        activity_name: DEPRECATED. Use 'name' instead.
        _extends: DEPRECATED. Optional activity to extend functionality from.
                  Extended activity must have 2 parameters (`config` and `params`).
                  The activity will be registered as a singledispatch function and be run
                  based on the type of the config parameter provided.
                  See `examples/activity_extends.py` for more details.

    Internal only args:
        _skip_registering: Whether to skip automatic registration of this activity.
                           When set to `True`, the activity will not be returned by `get_all_temporal_activities()`.

    Returns:
        A decorator function that transforms the target function into an activity.
    """
    actual_name = name if name is not None else activity_name

    if activity_name is not None:
        logger.warning(
            "'activity_name' parameter is deprecated, use 'name' instead",
            activity_name=activity_name,
        )

    if _extends is not None:
        logger.warning(
            "'_extends' parameter is deprecated and will be removed in a future version",
            _extends=_extends.__name__ if hasattr(_extends, "__name__") else str(_extends),
        )

    internal_event = display_name is None

    def decorator(target: T) -> T:
        # Only support module-level functions
        if not inspect.isfunction(target):
            raise WorkflowsException(
                code=ErrorCode.ACTIVITY_NOT_MODULE_LEVEL,
                message=f"@workflows.activity only supports module-level functions, got {type(target)}",
            )
        else:
            return cast(
                T,
                _decorate_activity(
                    target,
                    start_to_close_timeout,
                    retry_policy_max_attempts,
                    retry_policy_backoff_coefficient,
                    execution_name=display_name or target.__name__,
                    is_internal_activity=internal_event,
                    activity_name=actual_name,
                    extends=_extends,
                    sticky_to_worker=sticky_to_worker,
                    rate_limit=rate_limit,
                    _skip_registering=_skip_registering,
                    _allow_reserved_name=_allow_reserved_name,
                ),
            )

    return decorator


def _decorate_activity(
    func: Callable,
    start_to_close_timeout: datetime.timedelta,
    retry_policy_max_attempts: int | None,
    retry_policy_backoff_coefficient: float | None,
    execution_name: str,
    is_internal_activity: bool,
    activity_name: str | None,
    extends: Callable | None,
    sticky_to_worker: bool,
    rate_limit: RateLimit | None,
    _skip_registering: bool,
    _allow_reserved_name: bool,
) -> Callable:
    """
    See `activity` decorator for documentation.
    """

    if activity_name is not None:
        func.__name__ = activity_name

    name_to_check = activity_name or func.__name__
    if not _allow_reserved_name and name_to_check.startswith(INTERNAL_ACTIVITY_PREFIX):
        raise WorkflowsException(
            code=ErrorCode.ACTIVITY_RESERVED_NAME,
            message=f"Activity name '{name_to_check}' uses reserved prefix '{INTERNAL_ACTIVITY_PREFIX}'. "
            f"This prefix is reserved for internal framework activities.",
        )
    if retry_policy_max_attempts is None:
        retry_policy_max_attempts = config.worker.retry_policy_max_attempts
    if retry_policy_backoff_coefficient is None:
        retry_policy_backoff_coefficient = config.worker.retry_policy_backoff_coefficient

    # Validate signature BEFORE dependency injection modifies it
    raise_if_function_has_invalid_signature(func, is_method=False)

    user_params_dict, _ = get_function_signature_type_hints(func, is_method=False)

    original_func = func

    dependency_injector = DependencyInjector.get_singleton_instance()
    func = dependency_injector.auto_resolve_dependencies(func)
    # TODO: remove when remove workflow_sdk/workflows/worker/streaming/streaming_context.py
    # func = auto_stream_activity_status(
    #     func, activity_name=execution_name, retry_policy_max_attempts=retry_policy_max_attempts
    # )
    func = temporalio.activity.defn(func)

    if sticky_to_worker:
        set_activity_as_sticky_to_worker(func)

    if rate_limit is not None:
        set_rate_limit(func, rate_limit)
    elif get_rate_limit(func) is not None:
        raise ValueError(
            "Cannot use `@rate_limit` with `@activity`, please use the parameter `rate_limit` instead in `@activity`."  # noqa: E501
        )

    if not _skip_registering:
        # Register activity for temporal worker
        _temporal_activities.append(func)

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        """This wrapper is used to execute an activity from a Workflow."""
        is_inside_activity = _context_var_is_inside_activity.get(False)
        token = _context_var_is_inside_activity.set(True)
        publisher = None
        publisher_token = None

        try:
            raise_if_function_has_invalid_usage(original_func, args, kwargs, is_method=False)

            if not temporalio.activity.in_activity():
                # Only set up publisher for local execution
                context = EventContext.get_singleton()
                if context:
                    publisher = BackgroundEventPublisher(context)
                    publisher_token = BackgroundEventPublisher.set_current(publisher)
                else:
                    logger.warning(
                        "EventContext not initialized - event publishing disabled for this activity execution",
                        activity_name=func.__name__,
                    )

            if temporalio.workflow.in_workflow():
                # Determine task queue for activity scheduling
                if sticky_to_worker:
                    task_queue = context_var_task_queue.get()
                    if task_queue is None:
                        raise WorkflowsException(
                            code=ErrorCode.STICKY_WORKER_SESSION_MISSING,
                            message=f"Activity '{func.__name__}' is sticky to worker but no task queue is set. "
                            "Please call this activity inside `run_sticky_worker_session` context manager.",
                        )
                elif rate_limit is not None:
                    rate_limit_config = get_rate_limit(func)
                    if rate_limit_config is None:
                        raise ValueError(f"Activity '{func.__name__}' has rate limit but no rate limit config is set.")
                    task_queue = rate_limit_config.task_queue
                else:
                    task_queue = config.temporal.task_queue
                logger.debug(
                    "Executing activity inside workflow",
                    activity_name=func.__name__,
                    task_queue=task_queue,
                )
                if is_local_activity_enabled():
                    if rate_limit is not None:
                        logger.warning(
                            "Rate limiting is not supported for local activities",
                            activity_name=func.__name__,
                            rate_limit_config=rate_limit.model_dump()
                            if hasattr(rate_limit, "model_dump")
                            else str(rate_limit),
                        )
                    temporal_execute_activity = temporalio.workflow.execute_local_activity
                else:
                    temporal_execute_activity = partial(temporalio.workflow.execute_activity, task_queue=task_queue)

                result = await temporal_execute_activity(
                    func,
                    args=args,
                    start_to_close_timeout=start_to_close_timeout,
                    retry_policy=temporalio.common.RetryPolicy(
                        maximum_attempts=retry_policy_max_attempts,
                        backoff_coefficient=retry_policy_backoff_coefficient,
                    ),
                )
            else:
                if rate_limit is not None:
                    rate_limit_config = get_rate_limit(func)
                    if rate_limit_config is None:
                        raise ValueError(f"Activity '{func.__name__}' has rate limit but no rate limit config is set.")
                    await local_wait_rate_limit(rate_limit_config)

                local_func = (
                    func
                    if temporalio.activity.in_activity() or is_inside_activity
                    else tenacity.retry(
                        retry=tenacity.retry_if_exception_type(Exception),
                        stop=tenacity.stop_after_attempt(retry_policy_max_attempts),
                        wait=tenacity.wait_exponential(multiplier=retry_policy_backoff_coefficient),
                        reraise=True,
                    )(func)
                )

                if DependencyInjector.is_inside_dependencies_context():
                    logger.debug(
                        "Executing activity outside workflow (inside dependencies context)",
                        activity_name=func.__name__,
                    )
                    result = await local_func(*args, **kwargs)
                else:
                    logger.debug(
                        "Executing activity outside workflow (outside dependencies context)",
                        activity_name=func.__name__,
                    )
                    dependency_injector = DependencyInjector.get_singleton_instance()
                    async with dependency_injector.with_dependencies():
                        result = await local_func(*args, **kwargs)

            _, result = unwrap_contextual_result(result)
            raise_if_function_has_invalid_return_type(original_func, result, is_method=False)

            if publisher:
                await publisher.drain(timeout=10.0)

        except Exception:
            # Wait for pending events even on failure
            if publisher:
                await publisher.drain(timeout=10.0)
            raise
        finally:
            if publisher:
                await publisher.shutdown()
            if publisher_token is not None:
                reset_contextvar(_background_event_publisher, publisher_token)
            reset_contextvar(_context_var_is_inside_activity, token)

        return result

    if hasattr(func, "__temporal_activity_definition"):
        wrapper.__temporal_activity_definition = func.__temporal_activity_definition  # type: ignore[attr-defined]

    if extends is not None:
        if not hasattr(extends, "register"):
            raise ValueError(
                f"activity '{extends.__name__}' must be decorated with @workflows.activity and contains 2 parameters (`config` and `params`) to be used inside extends."  # noqa: E501
            )

        wrapper = extends.register(wrapper)  # type: ignore[attr-defined]
    elif len(user_params_dict) == 2:
        param_names = list(user_params_dict.keys())
        if param_names == ["config", "params"]:
            wrapper = singledispatch(wrapper)  # type: ignore[assignment]

    if not _skip_registering:
        # Register activity for internal usage
        _activities_by_name[wrapper.__name__] = wrapper

    return cast(Callable, wrapper)


def get_all_temporal_activities() -> List[Callable]:
    """
    Get a list of all registered Temporal activities.

    Returns:
        List[Callable]: A list of all activity functions registered with Temporal.
    """
    return _temporal_activities.copy()  # return a copy to avoid modifying the original list


def get_wrapped_activity(activity_name: str) -> Callable | None:
    """
    Get a wrapped activity function by name.

    Args:
        activity_name: The name of the activity to retrieve.

    Returns:
        Callable | None: The wrapped activity function if found, None otherwise.
    """
    return _activities_by_name.get(activity_name)


def check_is_activity(func: Callable) -> bool:
    """
    Check if a function is a registered Temporal activity.

    Args:
        func: The function to check.

    Returns:
        bool: True if the function is a registered activity, False otherwise.
    """
    return func in _activities_by_name.values()
