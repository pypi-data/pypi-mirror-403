from typing import Any

import pytest

import mistralai_workflows
from mistralai_workflows import get_workflow_definition

from .fixtures import (
    ChildWorkflow,
    ChildWorkflowCustomExecute,
    ChildWorkflowParams,
    MultiArgChildWorkflow,
    MultiArgParentWorkflow,
    MultiParamWithPrefixInput,
    NestedChildLevel1,
    NestedChildLevel2,
    NestedParentWorkflow,
    ParentWorkflow,
    PersonData,
    PrimitiveChildWorkflow,
    PrimitiveParentWorkflow,
    PrimitiveWorkflowParams,
    ProcessingResult,
    PydanticChildWorkflow,
    PydanticParentWorkflow,
    StandaloneWorkflowWithMultiArgs,
    StandaloneWorkflowWithPydantic,
)
from .utils import create_test_worker


class TestExecuteWorkflowBasic:
    @pytest.mark.asyncio
    async def test_simple_child_workflow(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[ParentWorkflow, ChildWorkflow], activities=[]):
            workflow_def = get_workflow_definition(ParentWorkflow)
            assert workflow_def is not None
            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"name": "Test"},
                id="test-parent-workflow",
                task_queue="test-task-queue",
            )

            result = await handle.result()
            assert "Child says: Test" in result["result"]
            assert "Parent got:" in result["result"]


class TestExecuteWorkflowWithPydantic:
    @pytest.mark.asyncio
    async def test_child_workflow_with_pydantic_model(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env, workflows=[PydanticParentWorkflow, PydanticChildWorkflow], activities=[]
        ):
            workflow_def = get_workflow_definition(PydanticParentWorkflow)
            person = PersonData(first_name="John", last_name="Doe", age=25)

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                person.model_dump(),
                id="test-pydantic-parent",
                task_queue="test-task-queue",
            )

            result = await handle.result()
            assert "Processed: John Doe is an adult" in result["result"]

    @pytest.mark.asyncio
    async def test_child_workflow_with_pydantic_minor(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env, workflows=[PydanticParentWorkflow, PydanticChildWorkflow], activities=[]
        ):
            workflow_def = get_workflow_definition(PydanticParentWorkflow)
            person = PersonData(first_name="Jane", last_name="Smith", age=16)

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                person.model_dump(),
                id="test-pydantic-parent-minor",
                task_queue="test-task-queue",
            )

            result = await handle.result()
            assert "Processed: Jane Smith is a minor" in result["result"]


class TestExecuteWorkflowWithMultipleArgs:
    @pytest.mark.asyncio
    async def test_child_workflow_with_multiple_args(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env, workflows=[MultiArgParentWorkflow, MultiArgChildWorkflow], activities=[]
        ):
            workflow_def = get_workflow_definition(MultiArgParentWorkflow)

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"name": "Hello", "count": 3},
                id="test-multi-arg-parent",
                task_queue="test-task-queue",
            )

            result = await handle.result()
            assert "Parent received: Hello repeated 3 times: Hello, Hello, Hello" in result["result"]


class TestExecuteWorkflowWithPrimitives:
    @pytest.mark.asyncio
    async def test_child_workflow_with_primitive_types(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env, workflows=[PrimitiveParentWorkflow, PrimitiveChildWorkflow], activities=[]
        ):
            workflow_def = get_workflow_definition(PrimitiveParentWorkflow)

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"message": "TestMessage"},
                id="test-primitive-parent",
                task_queue="test-task-queue",
            )

            result = await handle.result()
            assert "Got back: Echo: TestMessage" in result["result"]


class TestExecuteWorkflowNested:
    @pytest.mark.asyncio
    async def test_nested_child_workflows(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env,
            workflows=[NestedParentWorkflow, NestedChildLevel1, NestedChildLevel2],
            activities=[],
        ):
            workflow_def = get_workflow_definition(NestedParentWorkflow)

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"value": "test"},
                id="test-nested-parent",
                task_queue="test-task-queue",
            )

            result = await handle.result()
            assert result["result"] == "L0[L1[L2[test]]]"


class TestExecuteWorkflowDirect:
    @pytest.mark.asyncio
    async def test_direct_execute_workflow_with_pydantic(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[StandaloneWorkflowWithPydantic], activities=[]):
            person = PersonData(first_name="Alice", last_name="Johnson", age=30)

            result = await mistralai_workflows.execute_workflow(StandaloneWorkflowWithPydantic, params=person)

            assert isinstance(result, ProcessingResult)
            assert result.full_name == "Alice Johnson"
            assert result.is_adult is True
            assert "Standalone: Alice Johnson is an adult" in result.message

    @pytest.mark.asyncio
    async def test_direct_execute_workflow_with_multiple_args(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[StandaloneWorkflowWithMultiArgs], activities=[]):
            result = await mistralai_workflows.execute_workflow(
                StandaloneWorkflowWithMultiArgs, params=MultiParamWithPrefixInput(name="Item", count=3, prefix=">> ")
            )

            assert isinstance(result, str)
            assert result == "Generated: >> Item, >> Item, >> Item"

    @pytest.mark.asyncio
    async def test_direct_execute_workflow_returns_primitive(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[PrimitiveChildWorkflow], activities=[]):
            result = await mistralai_workflows.execute_workflow(
                PrimitiveChildWorkflow, params=PrimitiveWorkflowParams(message="DirectCall")
            )

            assert isinstance(result, str)
            assert result == "Echo: DirectCall"


class TestChildWorkflowCustomEntrypoint:
    def test_child_workflow_with_custom_entrypoint_name_has_correct_method(self) -> None:
        assert hasattr(ChildWorkflowCustomExecute, "execute")
        assert callable(ChildWorkflowCustomExecute.execute)

    @pytest.mark.asyncio
    async def test_execute_workflow_works_with_custom_entrypoint_name(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[ChildWorkflowCustomExecute], activities=[]):
            result = await mistralai_workflows.execute_workflow(
                ChildWorkflowCustomExecute, params=ChildWorkflowParams(name="Test")
            )

            assert result == "Child with custom entrypoint says: Test"
