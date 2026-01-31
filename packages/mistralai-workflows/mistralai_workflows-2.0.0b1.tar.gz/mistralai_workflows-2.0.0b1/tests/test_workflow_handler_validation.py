import pytest

from mistralai_workflows import workflow
from mistralai_workflows.exceptions import WorkflowsException


class TestSignalHandlerValidation:
    def test_signal_with_invalid_param_schema_raises_error(self) -> None:
        class InvalidType:
            value: str

        with pytest.raises(WorkflowsException, match="has invalid parameters for schema generation"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

                @workflow.signal()
                async def invalid_signal(self, data: InvalidType) -> None:
                    pass


class TestQueryHandlerValidation:
    def test_async_query_handler_raises_error(self) -> None:
        with pytest.raises(WorkflowsException, match="Query.*must be a synchronous function"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

                @workflow.query()
                async def async_query(self) -> str:
                    return "test"

    def test_query_with_none_return_raises_error(self) -> None:
        with pytest.raises(WorkflowsException, match="must have a return type annotation other than None"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

                @workflow.query()
                def none_query(self) -> None:
                    pass


class TestUpdateHandlerValidation:
    def test_update_with_invalid_param_schema_raises_error(self) -> None:
        class InvalidType:
            value: str

        with pytest.raises(WorkflowsException, match="has invalid parameters for schema generation"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

                @workflow.update()
                async def invalid_update(self, data: InvalidType) -> str:
                    return "test"

    def test_update_with_none_return_raises_error(self) -> None:
        with pytest.raises(WorkflowsException, match="must have a return type annotation other than None"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

                @workflow.update()
                async def none_update(self) -> None:
                    pass


class TestWorkflowEntrypointValidation:
    def test_missing_entrypoint_raises_error(self) -> None:
        with pytest.raises(WorkflowsException, match="must have an entrypoint method"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                async def some_other_method(self) -> None:
                    pass

    def test_sync_entrypoint_raises_error(self) -> None:
        with pytest.raises(WorkflowsException, match="must be async"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                @workflow.entrypoint  # pyright: ignore[reportArgumentType]
                def run(self) -> None:
                    pass

    def test_entrypoint_with_invalid_param_schema_raises_error(self) -> None:
        class InvalidType:
            value: str

        with pytest.raises(WorkflowsException, match="Cannot generate Pydantic model from parameters"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self, data: InvalidType) -> None:
                    pass

    def test_workflow_define_requires_name_parameter(self) -> None:
        with pytest.raises(WorkflowsException, match="requires 'name' parameter"):

            @workflow.define()  # pyright: ignore[reportCallIssue]
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

    def test_workflow_define_on_non_class_raises_error(self) -> None:
        with pytest.raises(WorkflowsException, match="only supports classes"):

            @workflow.define(name="test")  # pyright: ignore[reportGeneralTypeIssues]
            async def some_function() -> None:
                pass

    def test_entrypoint_method_name_is_preserved(self) -> None:
        @workflow.define(name="test_workflow")
        class TestWorkflow:
            @workflow.entrypoint
            async def execute(self) -> None:
                pass

        assert hasattr(TestWorkflow, "execute")
        assert callable(TestWorkflow.execute)
