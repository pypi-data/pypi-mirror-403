import pytest

from mistralai_workflows import workflow
from mistralai_workflows.exceptions import WorkflowsException

from .fixtures import ParamsModel, ResultModel


class TestWorkflowDefineDecorator:
    def test_workflow_define_on_function_raises_error(self) -> None:
        with pytest.raises(WorkflowsException, match="only supports classes"):

            @workflow.define(name="test-workflow-func")  # pyright: ignore[reportGeneralTypeIssues]
            async def test_workflow_func(params: ParamsModel) -> ResultModel:
                return ResultModel(message="test")

    def test_workflow_entrypoint_sync_function_raises_error(self) -> None:
        with pytest.raises(WorkflowsException, match="must be async"):

            @workflow.entrypoint  # pyright: ignore[reportArgumentType]
            def sync_run(self: object, params: ParamsModel) -> ResultModel:
                return ResultModel(message="test")
