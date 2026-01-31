import inspect
from datetime import timedelta
from types import NoneType
from typing import Any, Type

import structlog
import temporalio.workflow
from pydantic import BaseModel

from mistralai_workflows.core.definition.validation.validator import get_function_signature_type_hints
from mistralai_workflows.core.definition.workflow_definition import (
    _get_workflow_entrypoint_method,
    get_workflow_definition,
)
from mistralai_workflows.core.dependencies.dependency_injector import DependencyInjector
from mistralai_workflows.core.utils.contextvars import unwrap_contextual_result
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException

logger = structlog.get_logger(__name__)


def get_execution_id() -> str | None:
    if temporalio.workflow.in_workflow():
        return temporalio.workflow.info().workflow_id
    else:
        return None


async def execute_workflow(
    workflow: Type,
    params: BaseModel,
    execution_timeout: timedelta = timedelta(hours=6),
    execution_id: str | None = None,
) -> Any:
    """Execute a workflow. If called from within a workflow, it will execute the workflow as a child workflow.

    Args:
        workflow (Type): The workflow class to execute. (must be decorated with @define)
        params (BaseModel): The parameters to pass to the workflow. (must be a BaseModel)
        execution_timeout (timedelta, optional): The maximum time the workflow can run.
                                                 Defaults to timedelta(hours=6).
        execution_id (str | None, optional): The workflow id to use. If None, a random id will be generated.

    Returns:
        Any: The return value of the workflow.
    """
    workflow_definition = get_workflow_definition(workflow)
    if not workflow_definition:
        raise WorkflowsException(
            code=ErrorCode.WORKFLOW_DEFINITION_ERROR,
            message=f"{workflow} class must be decorated with @workflow.define",
        )

    entrypoint_method = _get_workflow_entrypoint_method(workflow)
    if not entrypoint_method:
        raise WorkflowsException(
            code=ErrorCode.WORKFLOW_DEFINITION_ERROR,
            message=f"{workflow} class must have an entrypoint method decorated with @workflow.entrypoint",
        )

    original_func = getattr(entrypoint_method, "__wrapped__", None)
    if original_func:
        _, return_type = get_function_signature_type_hints(original_func, is_method=True)
    else:
        return_type = None

    if temporalio.workflow.in_workflow():
        return_value = await temporalio.workflow.execute_child_workflow(
            workflow_definition.name,
            params.model_dump(),
            task_timeout=execution_timeout,
            result_type=dict,
            id=execution_id,
        )

        _, return_value = unwrap_contextual_result(return_value)
    else:
        workflow_instance = workflow()
        params_dict = params.model_dump()

        if DependencyInjector.is_inside_dependencies_context():
            return_value = await entrypoint_method(workflow_instance, params_dict)
        else:
            dependency_injector = DependencyInjector.get_singleton_instance()
            async with dependency_injector.with_dependencies():
                return_value = await entrypoint_method(workflow_instance, params_dict)

    if return_type and return_type != NoneType:
        try:
            is_base_model = inspect.isclass(return_type) and issubclass(return_type, BaseModel)
        except TypeError:
            is_base_model = False

        if is_base_model:
            return return_type.model_validate(return_value)
        elif isinstance(return_value, dict) and "result" in return_value:
            return return_value["result"]
        else:
            return return_value
    else:
        return return_value
