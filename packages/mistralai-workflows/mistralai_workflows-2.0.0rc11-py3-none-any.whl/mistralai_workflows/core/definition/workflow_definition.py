import inspect
from typing import Callable, Type, cast

from mistralai_workflows.models import WorkflowSpec


def _get_workflow_entrypoint_method(cls_type: Type) -> Callable | None:
    for _, method in inspect.getmembers(cls_type, predicate=inspect.isfunction):
        if hasattr(method, "__workflows_workflow_entrypoint"):
            return method
    return None


def get_workflow_definition(workflow: Type | Callable) -> WorkflowSpec:
    definition = getattr(workflow, "__workflows_workflow_def", None)
    if definition is None:
        raise ValueError(f"Cannot get definition from {workflow}. Make sure it was decorated with @define")
    return cast(WorkflowSpec, definition)


def set_workflow_definition(workflow: Type | Callable, definition: WorkflowSpec) -> None:
    setattr(workflow, "__workflows_workflow_def", definition)


def set_workflow_entrypoint(method: Callable) -> None:
    setattr(method, "__workflows_workflow_entrypoint", True)
