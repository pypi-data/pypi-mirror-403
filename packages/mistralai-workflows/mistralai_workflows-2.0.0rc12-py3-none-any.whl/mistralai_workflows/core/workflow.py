import asyncio
import inspect
from datetime import timedelta
from functools import WRAPPER_ASSIGNMENTS, wraps
from typing import Any, Awaitable, Callable, List, Type, TypeVar

import structlog
import temporalio.workflow
from pydantic import BaseModel
from temporalio.common import VersioningBehavior

from mistralai_workflows.core.config.config import RESERVED_QUERY_NAMES, RESERVED_UPDATE_NAMES, config
from mistralai_workflows.core.definition.validation.parameter_conversion import (
    convert_params_dict_to_user_args,
    convert_query_update_result_to_temporal_format,
    convert_result_to_temporal_format,
)
from mistralai_workflows.core.definition.validation.schema_generator import (
    generate_pydantic_model_from_params,
    generate_pydantic_model_from_return_type,
)
from mistralai_workflows.core.definition.validation.validator import (
    get_function_signature_type_hints,
    raise_if_function_has_invalid_signature,
    validate_query_handler_signature,
    validate_signal_handler_signature,
    validate_update_handler_signature,
)
from mistralai_workflows.core.definition.workflow_definition import (
    _get_workflow_entrypoint_method,
    set_workflow_definition,
    set_workflow_entrypoint,
)
from mistralai_workflows.core.execution.workflow_execution import (  # noqa: F401 - used in static methods below
    execute_workflow,
)
from mistralai_workflows.core.tracing.utils import (
    set_otel_trace_id_in_current_workflow_execution,
)
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException
from mistralai_workflows.models import (
    QueryDefinition,
    ScheduleDefinition,
    SignalDefinition,
    UpdateDefinition,
    WorkflowSpec,
)

Schedule = ScheduleDefinition

logger = structlog.get_logger(__name__)

ClassType = TypeVar("ClassType", bound=Type)
T = TypeVar("T")


class workflow:
    @staticmethod
    def define(
        name: str | None = None,
        workflow_description: str | None = None,
        schedules: List[Schedule] | None = None,
        workflow_name: str | None = None,
        workflow_display_name: str | None = None,
    ) -> Callable[[ClassType], ClassType]:
        """Decorator to define a workflow class.

        This decorator registers a class as a Mistral workflow. The class must have exactly one method
        decorated with @workflow.entrypoint to serve as the workflow's main execution logic.

        Args:
            name: The workflow name used for identification and execution. Required.
            workflow_description: Optional description of what the workflow does.
            schedules: Optional list of schedule definitions for automated workflow execution.
            workflow_name: DEPRECATED. Use 'name' instead.

        Returns:
            A decorator function that transforms the class into a Mistral workflow.

        Raises:
            WorkflowsException: If name is not provided or if the class is not valid.

        Example:
            @workflow.define(name="my_workflow")
            class MyWorkflow:
                @workflow.entrypoint
                async def run(self, input: str) -> str:
                    return f"Processed: {input}"
        """

        def decorator(cls_type: ClassType) -> ClassType:
            actual_name = name if name is not None else workflow_name

            if actual_name is None:
                raise WorkflowsException(
                    code=ErrorCode.WORKFLOW_DEFINITION_ERROR,
                    message="@workflow.define requires 'name' parameter",
                )

            if workflow_name is not None:
                logger.warning(
                    "'workflow_name' parameter is deprecated, use 'name' instead",
                    workflow_name=workflow_name,
                )
            if not inspect.isclass(cls_type):
                raise WorkflowsException(
                    code=ErrorCode.WORKFLOW_DEFINITION_ERROR,
                    message=f"@workflow.define only supports classes, got {type(cls_type)}",
                )

            original_run_method = _get_workflow_entrypoint_method(cls_type)

            if not original_run_method:
                raise WorkflowsException(
                    code=ErrorCode.WORKFLOW_DEFINITION_ERROR,
                    message=(
                        f"Workflow class {cls_type} must have an entrypoint method. "
                        f"Use @workflow.entrypoint on one method in the class {cls_type}"
                    ),
                )

            user_method_name = original_run_method.__name__
            user_params_dict, return_type = get_function_signature_type_hints(original_run_method, is_method=True)

            input_model = generate_pydantic_model_from_params(
                original_run_method.__name__, user_params_dict, "Input", original_run_method
            )
            output_model = generate_pydantic_model_from_return_type(original_run_method.__name__, return_type)

            # Exclude __annotations__ to prevent Temporal from seeing the original function's signature.
            @wraps(original_run_method, assigned=tuple(a for a in WRAPPER_ASSIGNMENTS if a != "__annotations__"))
            async def run(self: Any, params: dict | None = None) -> Any:
                otel_task = asyncio.create_task(set_otel_trace_id_in_current_workflow_execution())

                if user_params_dict:
                    actual_args = convert_params_dict_to_user_args(params or {}, user_params_dict, input_model)
                else:
                    actual_args = ()

                result = await original_run_method(self, *actual_args)

                try:
                    await otel_task
                except Exception as e:
                    logger.warn("Failed to set otel trace id in current workflow execution", exc_info=e)

                return convert_result_to_temporal_format(result, output_model)

            run.__qualname__ = f"{cls_type.__name__}.{user_method_name}"

            wrapped_run = temporalio.workflow.run(run)

            setattr(cls_type, user_method_name, wrapped_run)

            collected_signals: List[SignalDefinition] = []
            collected_queries: List[QueryDefinition] = []
            collected_updates: List[UpdateDefinition] = []

            for _, method_obj in inspect.getmembers(cls_type, predicate=inspect.isfunction):
                if hasattr(method_obj, "__wf_signal_def"):
                    collected_signals.append(getattr(method_obj, "__wf_signal_def"))
                elif hasattr(method_obj, "__wf_query_def"):
                    collected_queries.append(getattr(method_obj, "__wf_query_def"))
                elif hasattr(method_obj, "__wf_update_def"):
                    collected_updates.append(getattr(method_obj, "__wf_update_def"))

            # Sort for deterministic order to ensure consistent schema generation across runs
            collected_signals.sort(key=lambda s: s.name)
            collected_queries.sort(key=lambda q: q.name)
            collected_updates.sort(key=lambda u: u.name)

            workflow_definition_obj = WorkflowSpec(
                name=actual_name,
                display_name=workflow_display_name,
                description=workflow_description,
                input_schema=input_model.model_json_schema() if input_model else None,
                output_schema=output_model.model_json_schema() if output_model else None,
                signals=collected_signals,
                queries=collected_queries,
                updates=collected_updates,
                schedules=schedules or [],
            )
            set_workflow_definition(cls_type, workflow_definition_obj)

            versioning_cfg = config.worker.versioning

            if versioning_cfg.enabled and versioning_cfg.deployment_name and versioning_cfg.build_id:
                logger.info(
                    "Workflow registered with PINNED versioning behavior",
                    workflow_name=actual_name,
                    deployment_name=versioning_cfg.deployment_name,
                    build_id=versioning_cfg.build_id,
                )
                return temporalio.workflow.defn(
                    sandboxed=False,
                    name=actual_name,
                    versioning_behavior=VersioningBehavior.PINNED,
                )(cls_type)
            else:
                logger.info(
                    "Workflow registered WITHOUT versioning behavior",
                    workflow_name=actual_name,
                )
                return temporalio.workflow.defn(sandboxed=False, name=actual_name)(cls_type)

        return decorator

    @staticmethod
    def entrypoint(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """Decorator to mark the workflow entrypoint method.

        Marks a method as the main execution entry point for a workflow. Every workflow class
        must have exactly one method decorated with @workflow.entrypoint. This method will be
        called when the workflow is executed.

        The entrypoint method must be async and can accept parameters (as individual typed arguments)
        and return a value. All parameters and return types should be JSON-serializable or Pydantic models.

        Args:
            func: The async method to mark as the workflow entrypoint.

        Returns:
            The decorated method.

        Raises:
            WorkflowsException: If the method signature is invalid.

        Example:
            @workflow.entrypoint
            async def run(self, user_id: str, count: int) -> dict:
                # Workflow logic here
                return {"result": "success"}
        """
        raise_if_function_has_invalid_signature(func, is_method=True)

        set_workflow_entrypoint(func)
        return func

    @staticmethod
    def signal(
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[[Callable], Callable]:
        """Decorator for workflow signal handlers.

        Signals allow external systems to send data into a running workflow asynchronously.
        Signal handlers do not return values - they update workflow state or trigger actions.
        Multiple signals can be sent to a workflow while it's executing.

        Args:
            name: The signal name. If not provided, uses the method name.
            description: Optional description of what the signal does.

        Returns:
            A decorator function for the signal handler method.

        Example:
            @workflow.signal(name="approve")
            async def handle_approval(self, approved_by: str) -> None:
                self.approved = True
                self.approver = approved_by
        """

        def decorator(func: Callable) -> Callable:
            validate_signal_handler_signature(func, is_method=True)

            actual_signal_name = name or func.__name__
            user_params_dict, _ = get_function_signature_type_hints(func, is_method=True)
            input_model = generate_pydantic_model_from_params(func.__name__, user_params_dict, "Input", func)

            # Exclude __annotations__ to prevent Temporal from seeing the original function's signature.
            # The wrapper signature (params: dict | None) differs from the user's signature (e.g., amount: int),
            # and Temporal needs to see the wrapper's signature for correct payload deserialization.
            @wraps(func, assigned=tuple(a for a in WRAPPER_ASSIGNMENTS if a != "__annotations__"))
            async def async_wrapper(self: Any, params: dict | None = None) -> None:
                if user_params_dict:
                    actual_args = convert_params_dict_to_user_args(params or {}, user_params_dict, input_model)
                else:
                    actual_args = ()

                if asyncio.iscoroutinefunction(func):
                    await func(self, *actual_args)
                else:
                    func(self, *actual_args)

            @wraps(func, assigned=tuple(a for a in WRAPPER_ASSIGNMENTS if a != "__annotations__"))
            def sync_wrapper(self: Any, params: dict | None = None) -> None:
                if user_params_dict:
                    actual_args = convert_params_dict_to_user_args(params or {}, user_params_dict, input_model)
                else:
                    actual_args = ()
                func(self, *actual_args)

            wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

            signal_def = SignalDefinition(
                name=actual_signal_name,
                description=description,
                input_schema=input_model.model_json_schema() if input_model else None,
            )
            setattr(wrapper, "__wf_signal_def", signal_def)

            return temporalio.workflow.signal(name=actual_signal_name)(wrapper)

        return decorator

    @staticmethod
    def query(
        name: str | None = None,
        description: str | None = None,
        _internal: bool = False,
    ) -> Callable[[Callable], Callable]:
        """Decorator for workflow query handlers.

        Queries allow external systems to read the current state of a running workflow synchronously.
        Query handlers must not modify workflow state - they are read-only operations.
        They return values immediately based on the current workflow state.

        Args:
            name: The query name. If not provided, uses the method name.
            description: Optional description of what the query returns.
            _internal: Internal flag for framework-reserved handlers.

        Returns:
            A decorator function for the query handler method.

        Example:
            @workflow.query(name="get_status")
            def get_current_status(self) -> str:
                return self.current_status
        """

        def decorator(func: Callable) -> Callable:
            validate_query_handler_signature(func, is_method=True)

            actual_query_name = name or func.__name__

            if not _internal and actual_query_name in RESERVED_QUERY_NAMES:
                raise ValueError(
                    f"Query name '{actual_query_name}' is reserved by the framework. "
                    f"Reserved query names: {', '.join(sorted(RESERVED_QUERY_NAMES))}"
                )

            user_params_dict, return_type = get_function_signature_type_hints(func, is_method=True)
            input_model = generate_pydantic_model_from_params(func.__name__, user_params_dict, "Input", func)
            output_model = generate_pydantic_model_from_return_type(func.__name__, return_type)

            # Exclude __annotations__ to prevent Temporal from seeing the original function's signature.
            @wraps(func, assigned=tuple(a for a in WRAPPER_ASSIGNMENTS if a != "__annotations__"))
            def wrapper(self: Any, params: dict | None = None) -> Any:
                if user_params_dict:
                    actual_args = convert_params_dict_to_user_args(params or {}, user_params_dict, input_model)
                else:
                    actual_args = ()

                result = func(self, *actual_args)
                return convert_query_update_result_to_temporal_format(result, output_model)

            query_def = QueryDefinition(
                name=actual_query_name,
                description=description,
                input_schema=input_model.model_json_schema() if input_model else None,
                output_schema=output_model.model_json_schema() if output_model else None,
            )
            setattr(wrapper, "__wf_query_def", query_def)

            return temporalio.workflow.query(name=actual_query_name)(wrapper)

        return decorator

    @staticmethod
    def update(
        name: str | None = None,
        description: str | None = None,
        _internal: bool = False,
    ) -> Callable[[Callable], Callable]:
        """Decorator for workflow update handlers.

        Updates are similar to signals but they return a value and can be waited on.
        Unlike signals (fire-and-forget), updates provide synchronous feedback to the caller.
        They can modify workflow state and return the result of that modification.

        Args:
            name: The update name. If not provided, uses the method name.
            description: Optional description of what the update does.
            _internal: Internal flag for framework-reserved handlers.

        Returns:
            A decorator function for the update handler method.

        Example:
            @workflow.update(name="set_priority")
            async def update_priority(self, new_priority: int) -> dict:
                old = self.priority
                self.priority = new_priority
                return {"old": old, "new": new_priority}
        """

        def decorator(func: Callable) -> Callable:
            validate_update_handler_signature(func, is_method=True)

            actual_update_name = name or func.__name__

            if not _internal and actual_update_name in RESERVED_UPDATE_NAMES:
                raise ValueError(
                    f"Update name '{actual_update_name}' is reserved by the framework. "
                    f"Reserved update names: {', '.join(sorted(RESERVED_UPDATE_NAMES))}"
                )

            user_params_dict, return_type = get_function_signature_type_hints(func, is_method=True)
            input_model = generate_pydantic_model_from_params(func.__name__, user_params_dict, "Input", func)
            output_model = generate_pydantic_model_from_return_type(func.__name__, return_type)

            # Exclude __annotations__ to prevent Temporal from seeing the original function's signature.
            @wraps(func, assigned=tuple(a for a in WRAPPER_ASSIGNMENTS if a != "__annotations__"))
            async def async_wrapper(self: Any, params: dict | None = None) -> Any:
                if user_params_dict:
                    actual_args = convert_params_dict_to_user_args(params or {}, user_params_dict, input_model)
                else:
                    actual_args = ()

                result = await func(self, *actual_args)
                return convert_query_update_result_to_temporal_format(result, output_model)

            @wraps(func, assigned=tuple(a for a in WRAPPER_ASSIGNMENTS if a != "__annotations__"))
            def sync_wrapper(self: Any, params: dict | None = None) -> Any:
                if user_params_dict:
                    actual_args = convert_params_dict_to_user_args(params or {}, user_params_dict, input_model)
                else:
                    actual_args = ()

                result = func(self, *actual_args)
                return convert_query_update_result_to_temporal_format(result, output_model)

            wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

            update_def = UpdateDefinition(
                name=actual_update_name,
                description=description,
                input_schema=input_model.model_json_schema() if input_model else None,
                output_schema=output_model.model_json_schema() if output_model else None,
            )
            setattr(wrapper, "__wf_update_def", update_def)

            return temporalio.workflow.update(name=actual_update_name)(wrapper)

        return decorator

    @staticmethod
    async def execute_workflow(
        workflow: Type,
        params: BaseModel,
        execution_timeout: timedelta = timedelta(hours=6),
        execution_id: str | None = None,
    ) -> Any:
        """Execute a workflow. If called from within a workflow, it will execute as a child workflow.

        When called from within a workflow context, this starts a child workflow that inherits
        the parent's namespace and can be monitored as part of the parent's execution.
        When called outside a workflow context, it executes directly.

        Args:
            workflow: The workflow class to execute (must be decorated with @workflow.define).
            params: The parameters to pass to the workflow (must be a BaseModel).
            execution_timeout: The maximum time the workflow can run. Defaults to 6 hours.
            execution_id: Optional workflow ID. If None, a random ID will be generated.

        Returns:
            The return value of the workflow's entrypoint method.

        Raises:
            WorkflowsException: If the workflow is not properly decorated or configured.

        Example:
            result = await workflow.execute_workflow(
                workflow=DataProcessingWorkflow,
                params=ProcessingParams(data_id="123"),
                execution_timeout=timedelta(minutes=30)
            )
        """
        return await execute_workflow(
            workflow=workflow,
            params=params,
            execution_timeout=execution_timeout,
            execution_id=execution_id,
        )

    @staticmethod
    async def wait_condition(
        predicate: Callable[[], bool],
        timeout: timedelta | float | None = None,
        timeout_summary: str | None = None,
    ) -> None:
        """Pauses workflow execution until the given predicate function returns true.

        The predicate is re-evaluated whenever a new event (signal, activity completion, etc.)
        occurs for the workflow. This is an efficient, non-blocking wait that doesn't consume
        resources while waiting. This is a pass-through to temporalio.workflow.wait_condition.

        Args:
            predicate: Non-async callback that accepts no parameters and returns a boolean.
                It will be called repeatedly until it returns True.
            timeout: Optional timeout in seconds (or timedelta) before raising asyncio.TimeoutError.
            timeout_summary: Optional simple string identifying the timer that may be visible
                in Temporal UI/CLI. Best treated as a timer ID.

        Raises:
            asyncio.TimeoutError: If the timeout is reached before predicate returns True.

        Example:
            # Wait for approval signal
            await workflow.wait_condition(
                lambda: self.is_approved,
                timeout=timedelta(hours=24),
                timeout_summary="approval_wait"
            )
        """
        logger.debug("mistralai_workflows.workflow.wait_condition called")

        await temporalio.workflow.wait_condition(predicate, timeout=timeout, timeout_summary=timeout_summary)

    @staticmethod
    def continue_as_new(params: BaseModel) -> None:
        """Continue workflow execution with fresh history.

        Stops the current workflow and starts a new execution with the same workflow ID
        but a new run ID and empty event history. Use this to prevent history from growing
        too large in long-running or iterative workflows.

        Args:
            params: Parameters for the new execution (must be BaseModel)

        Raises:
            WorkflowsException: If called outside workflow context

        Example:
            @workflow.define(workflow_name="paginated-processor")
            class PaginatedProcessor:
                @workflow.entrypoint
                async def run(self, params: ProcessorParams):
                    # Process current batch
                    await process_batch(params.page)

                    # Check if we should continue
                    if workflow.should_continue_as_new():
                        next_params = ProcessorParams(page=params.page + 1)
                        workflow.continue_as_new(next_params)

                    # Continue with next page
                    ...
        """
        if not temporalio.workflow.in_workflow():
            raise WorkflowsException(
                code=ErrorCode.WORKFLOW_DEFINITION_ERROR,
                message="continue_as_new can only be called from within a workflow",
            )

        temporalio.workflow.continue_as_new(params.model_dump())

    @staticmethod
    def should_continue_as_new() -> bool:
        """Check if Temporal suggests continuing as new due to history size.

        Returns True when the workflow's event history is approaching size limits.
        Use this to decide when to call continue_as_new() in long-running workflows.

        Returns:
            bool: True if continue-as-new is suggested, False otherwise

        Example:
            while has_more_work():
                await process_batch()

                if workflow.should_continue_as_new():
                    workflow.continue_as_new(get_next_state())
                    return  # Never reached, but good practice
        """
        if not temporalio.workflow.in_workflow():
            return False
        return temporalio.workflow.info().is_continue_as_new_suggested()
