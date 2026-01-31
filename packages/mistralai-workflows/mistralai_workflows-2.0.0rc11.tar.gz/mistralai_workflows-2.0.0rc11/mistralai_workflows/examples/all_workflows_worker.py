import asyncio
import importlib
import inspect
import pkgutil
import sys
from typing import Type

import structlog

import mistralai_workflows as workflows
from mistralai_workflows.core.definition.workflow_definition import get_workflow_definition

logger = structlog.get_logger(__name__)

SKIP_FILES = {
    "__init__",
    "worker_example",
    "all_workflows_worker",
    "old_workflow_insurance_claims",
    "old_workflow_multi_turn_chat",
}


def is_workflow_class(obj: object) -> bool:
    return hasattr(obj, "__workflows_workflow_def")


def discover_workflows_in_module(module_name: str) -> list[Type]:
    workflow_classes = []

    try:
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if is_workflow_class(obj):
                try:
                    workflow_def = get_workflow_definition(obj)
                    logger.info(
                        "Discovered workflow",
                        workflow_class=name,
                        workflow_name=workflow_def.name,
                        module=module_name,
                    )
                    workflow_classes.append(obj)
                except Exception as e:
                    logger.warning(
                        "Failed to get workflow definition",
                        workflow_class=name,
                        module=module_name,
                        error=str(e),
                    )
    except Exception as e:
        logger.warning("Failed to import module", module=module_name, error=str(e))

    return workflow_classes


def discover_all_workflows() -> list[Type]:
    all_workflows: list[Type] = []
    seen_workflow_names: set[str] = set()
    examples_package = "mistralai_workflows.examples"

    def scan_package(package_name: str) -> None:
        try:
            package_module = importlib.import_module(package_name)
        except ImportError as e:
            logger.error("Failed to import package", package=package_name, error=str(e))
            return

        if not hasattr(package_module, "__path__"):
            logger.error("Package has no __path__ attribute", package=package_name)
            return

        for _, modname, ispkg in pkgutil.iter_modules(package_module.__path__, prefix=f"{package_name}."):
            base_name = modname.split(".")[-1]
            if base_name in SKIP_FILES:
                continue

            if ispkg:
                scan_package(modname)
                continue

            logger.debug("Scanning module for workflows", module=modname)
            workflows_in_module = discover_workflows_in_module(modname)

            for workflow_class in workflows_in_module:
                workflow_def = get_workflow_definition(workflow_class)
                if workflow_def.name in seen_workflow_names:
                    logger.warning(
                        "Skipping duplicate workflow",
                        workflow_name=workflow_def.name,
                        workflow_class=workflow_class.__name__,
                        module=modname,
                    )
                    continue

                seen_workflow_names.add(workflow_def.name)
                all_workflows.append(workflow_class)

    scan_package(examples_package)
    return all_workflows


async def main() -> None:
    logger.info("Starting workflow discovery...")

    discovered_workflows = discover_all_workflows()

    if not discovered_workflows:
        logger.error("No workflows discovered")
        sys.exit(1)

    logger.info(
        "Workflow discovery complete",
        total_workflows=len(discovered_workflows),
        workflows=[get_workflow_definition(wf).name for wf in discovered_workflows],
    )

    logger.info("Starting worker...")
    await workflows.run_worker(discovered_workflows)


if __name__ == "__main__":
    asyncio.run(main())
