from typing import Any, Dict

from mistralai_workflows.core.execution.concurrency.types import (
    WorkflowResults,
)


def dict_to_workflow_results(results: Dict[int, Any]) -> WorkflowResults:
    """Convert a dictionary of results to WorkflowResults."""
    return WorkflowResults(values=[results[i] for i in sorted(results)])


def workflow_results_to_dict(results: WorkflowResults) -> Dict[int, Any]:
    """Convert WorkflowResults to a dictionary."""
    return {i: result for i, result in enumerate(results.values)}


def is_internal_workflow(workflow_name: str) -> bool:
    """Check if a workflow is internal."""
    return workflow_name.startswith("__internal_")
