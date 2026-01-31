import importlib
import inspect
import pkgutil

from mistralai_workflows.core.definition.workflow_definition import get_workflow_definition
from mistralai_workflows.examples.all_workflows_worker import (
    SKIP_FILES,
    discover_all_workflows,
    is_workflow_class,
)


def test_discover_all_workflows() -> None:
    workflows = discover_all_workflows()

    assert len(workflows) > 0, "Should discover at least one workflow"

    workflow_names = []
    for workflow_class in workflows:
        assert hasattr(workflow_class, "__workflows_workflow_def"), (
            f"{workflow_class.__name__} should have workflow definition"
        )

        workflow_def = get_workflow_definition(workflow_class)
        assert workflow_def.name, f"{workflow_class.__name__} should have a name"
        workflow_names.append(workflow_def.name)

    assert len(workflow_names) == len(set(workflow_names)), (
        f"Duplicate workflow names detected: {[name for name in workflow_names if workflow_names.count(name) > 1]}"
    )


def test_discover_specific_workflows() -> None:
    workflows = discover_all_workflows()
    workflow_names = {get_workflow_definition(wf).name for wf in workflows}

    assert "example-hello-world-workflow" in workflow_names


def test_all_example_files_are_discovered() -> None:
    discovered_workflows = discover_all_workflows()
    discovered_modules = {wf.__module__ for wf in discovered_workflows}

    import mistralai_workflows.examples as examples_package

    missing_workflows: list[str] = []

    for _, modname, ispkg in pkgutil.iter_modules(examples_package.__path__, prefix="mistralai_workflows.examples."):
        if ispkg:
            continue

        base_name = modname.split(".")[-1]
        if base_name in SKIP_FILES:
            continue

        module = importlib.import_module(modname)
        has_workflow = any(is_workflow_class(obj) for _, obj in inspect.getmembers(module, inspect.isclass))

        if has_workflow and modname not in discovered_modules:
            missing_workflows.append(modname)

    assert not missing_workflows, (
        f"Example files with workflows not discovered by all_workflows_worker:\n"
        f"{', '.join(missing_workflows)}\n"
        f"Check discover_workflows_in_module() in all_workflows_worker.py"
    )
