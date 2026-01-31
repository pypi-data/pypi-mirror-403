from typing import Any

import pytest
from pydantic import BaseModel

from mistralai_workflows import activity, get_workflow_definition, workflow

from .fixtures import (
    GreetingParams,
    ParamsModel,
    UpdateInput,
    WorkflowWithPydanticHandlers,
)
from .utils import create_test_worker


class SimpleInput(BaseModel):
    message: str


class ComplexOutput(BaseModel):
    result: str
    count: int


@workflow.define(name="workflow_with_defaults")
class WorkflowWithDefaults:
    @workflow.entrypoint
    async def run(self, name: str, greeting: str = "Hello", count: int = 1) -> str:
        return f"{greeting}, {name}! (x{count})"


@workflow.define(name="workflow_all_defaults")
class WorkflowAllDefaults:
    @workflow.entrypoint
    async def run(self, name: str = "World", greeting: str = "Hello") -> str:
        return f"{greeting}, {name}!"


@workflow.define(name="workflow_mixed_params")
class WorkflowMixedParams:
    @workflow.entrypoint
    async def run(
        self,
        required_str: str,
        optional_int: int = 42,
        optional_bool: bool = False,
        optional_str: str = "default",
    ) -> str:
        return f"{required_str}: int={optional_int}, bool={optional_bool}, str={optional_str}"


@activity()
async def activity_with_defaults(name: str, prefix: str = "Mr.", suffix: str = "") -> str:
    result = f"{prefix} {name}"
    if suffix:
        result += f" {suffix}"
    return result


@activity()
async def activity_all_defaults(x: int = 10, y: int = 20) -> int:
    return x + y


@workflow.define(name="workflow_calling_activity_with_defaults")
class WorkflowCallingActivityWithDefaults:
    @workflow.entrypoint
    async def run(self, name: str) -> str:
        result1 = await activity_with_defaults(name, "Dr.", "PhD")
        result2 = await activity_with_defaults(name, "Ms.")
        result3 = await activity_with_defaults(name)
        result4 = await activity_all_defaults()
        result5 = await activity_all_defaults(5)
        result6 = await activity_all_defaults(5, 15)
        return f"{result1} | {result2} | {result3} | {result4} | {result5} | {result6}"


@workflow.define(name="workflow_with_signal_defaults")
class WorkflowWithSignalDefaults:
    def __init__(self) -> None:
        self.messages: list[str] = []

    @workflow.entrypoint
    async def run(self) -> str:
        await workflow.wait_condition(lambda: len(self.messages) >= 2)
        return " | ".join(self.messages)

    @workflow.signal(name="add_message")
    async def add_message(self, text: str, priority: int = 0, tag: str = "info") -> None:
        self.messages.append(f"[{tag}:{priority}] {text}")


@workflow.define(name="workflow_with_query_defaults")
class WorkflowWithQueryDefaults:
    def __init__(self) -> None:
        self.counter = 0

    @workflow.entrypoint
    async def run(self) -> str:
        await workflow.wait_condition(lambda: self.counter >= 10)
        return "done"

    @workflow.signal(name="increment")
    async def increment(self, amount: int = 1) -> None:
        self.counter += amount

    @workflow.query(name="get_counter")
    def get_counter(self, multiplier: int = 1, offset: int = 0) -> int:
        return (self.counter * multiplier) + offset


@workflow.define(name="workflow_with_update_defaults")
class WorkflowWithUpdateDefaults:
    def __init__(self) -> None:
        self.value = 100

    @workflow.entrypoint
    async def run(self) -> int:
        await workflow.wait_condition(lambda: self.value <= 0)
        return self.value

    @workflow.update(name="adjust_value")
    async def adjust_value(self, delta: int, min_value: int = 0, max_value: int = 200) -> dict:
        old_value = self.value
        self.value += delta
        self.value = max(min_value, min(max_value, self.value))
        return {"old": old_value, "new": self.value, "clamped": old_value + delta != self.value}


class TestWorkflowDefaultParameters:
    @pytest.mark.asyncio
    async def test_workflow_with_some_defaults(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[WorkflowWithDefaults], activities=[]):
            workflow_def = get_workflow_definition(WorkflowWithDefaults)
            assert workflow_def is not None

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"name": "Alice", "greeting": "Hi", "count": 3},
                id="test-all-params",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert result["result"] == "Hi, Alice! (x3)"

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"name": "Bob"},
                id="test-required-only",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert result["result"] == "Hello, Bob! (x1)"

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"name": "Charlie", "count": 5},
                id="test-partial-defaults",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert result["result"] == "Hello, Charlie! (x5)"

    @pytest.mark.asyncio
    async def test_workflow_with_all_defaults(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[WorkflowAllDefaults], activities=[]):
            workflow_def = get_workflow_definition(WorkflowAllDefaults)
            assert workflow_def is not None

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {},
                id="test-no-params",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert result["result"] == "Hello, World!"

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"name": "Python"},
                id="test-one-param",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert result["result"] == "Hello, Python!"

    @pytest.mark.asyncio
    async def test_workflow_mixed_default_types(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[WorkflowMixedParams], activities=[]):
            workflow_def = get_workflow_definition(WorkflowMixedParams)
            assert workflow_def is not None

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"required_str": "test"},
                id="test-mixed-required-only",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert result["result"] == "test: int=42, bool=False, str=default"

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"required_str": "custom", "optional_int": 99, "optional_bool": True},
                id="test-mixed-partial",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            assert result["result"] == "custom: int=99, bool=True, str=default"


class TestActivityDefaultParameters:
    @pytest.mark.asyncio
    async def test_activity_with_defaults(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env,
            workflows=[WorkflowCallingActivityWithDefaults],
            activities=[activity_with_defaults, activity_all_defaults],
        ):
            workflow_def = get_workflow_definition(WorkflowCallingActivityWithDefaults)
            assert workflow_def is not None

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {"name": "Smith"},
                id="test-activity-defaults",
                task_queue="test-task-queue",
            )
            result = await handle.result()
            expected = "Dr. Smith PhD | Ms. Smith | Mr. Smith | 30 | 25 | 20"
            assert result["result"] == expected


class TestSignalDefaultParameters:
    @pytest.mark.asyncio
    async def test_signal_with_defaults(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[WorkflowWithSignalDefaults], activities=[]):
            workflow_def = get_workflow_definition(WorkflowWithSignalDefaults)
            assert workflow_def is not None

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {},
                id="test-signal-defaults",
                task_queue="test-task-queue",
            )

            await handle.signal("add_message", {"text": "urgent", "priority": 10, "tag": "error"})

            await handle.signal("add_message", {"text": "normal"})

            result = await handle.result()
            assert "[error:10] urgent" in result["result"]
            assert "[info:0] normal" in result["result"]

    @pytest.mark.asyncio
    async def test_signal_empty_dict_uses_all_defaults(self, temporal_env: Any) -> None:
        """
        Regression test: empty dict with all default parameters.

        Without selective @functools.wraps (excluding __annotations__), Temporal would see
        the original function signature and fail to deserialize an empty dict.
        See workflows/worker/workflow.py signal/query/update decorators.
        """

        @workflow.define(name="test_signal_empty_dict_defaults")
        class SignalEmptyDictDefaultsWorkflow:
            def __init__(self) -> None:
                self.counter = 0

            @workflow.entrypoint
            async def run(self) -> int:
                await workflow.wait_condition(lambda: self.counter >= 2)
                return self.counter

            @workflow.signal(name="increment")
            async def increment(self, amount: int = 1) -> None:
                self.counter += amount

        async with create_test_worker(temporal_env, workflows=[SignalEmptyDictDefaultsWorkflow], activities=[]):
            handle = await temporal_env.client.start_workflow(
                "test_signal_empty_dict_defaults",
                {},
                id="test-signal-empty-dict",
                task_queue="test-task-queue",
            )

            await handle.signal("increment", {"amount": 1})
            await handle.signal("increment", {})

            result = await handle.result()
            assert result["result"] == 2


class TestQueryDefaultParameters:
    @pytest.mark.asyncio
    async def test_query_with_defaults(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[WorkflowWithQueryDefaults], activities=[]):
            workflow_def = get_workflow_definition(WorkflowWithQueryDefaults)
            assert workflow_def is not None

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {},
                id="test-query-defaults",
                task_queue="test-task-queue",
            )

            await handle.signal("increment", {"amount": 5})
            await handle.signal("increment", {})  # default amount=1

            result = await handle.query("get_counter", {})
            assert result == 6  # 5 + 1, multiplier=1, offset=0

            result = await handle.query("get_counter", {"multiplier": 2})
            assert result == 12  # (5 + 1) * 2 + 0

            result = await handle.query("get_counter", {"multiplier": 3, "offset": 10})
            assert result == 28  # (5 + 1) * 3 + 10


class TestUpdateDefaultParameters:
    @pytest.mark.asyncio
    async def test_update_with_defaults(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[WorkflowWithUpdateDefaults], activities=[]):
            workflow_def = get_workflow_definition(WorkflowWithUpdateDefaults)
            assert workflow_def is not None

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                {},
                id="test-update-defaults",
                task_queue="test-task-queue",
            )

            result = await handle.execute_update("adjust_value", {"delta": -30})
            assert result["old"] == 100
            assert result["new"] == 70
            assert result["clamped"] is False

            result = await handle.execute_update("adjust_value", {"delta": 150, "max_value": 150})
            assert result["old"] == 70
            assert result["new"] == 150
            assert result["clamped"] is True

            result = await handle.execute_update("adjust_value", {"delta": -200, "min_value": -10})
            assert result["old"] == 150
            assert result["new"] == -10
            assert result["clamped"] is True


class TestPydanticParameters:
    @pytest.mark.asyncio
    async def test_pydantic_signal_query_update_handlers(self, temporal_env: Any) -> None:
        async with create_test_worker(temporal_env, workflows=[WorkflowWithPydanticHandlers], activities=[]):
            workflow_def = get_workflow_definition(WorkflowWithPydanticHandlers)
            assert workflow_def is not None

            params = ParamsModel(name="TestWorkflow", count=2)
            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                params.model_dump(),
                id="test-pydantic-handlers",
                task_queue="test-task-queue",
            )

            query_result = await handle.query("get_status")
            assert isinstance(query_result, dict)
            assert "message" in query_result
            assert "TestWorkflow" in query_result["message"]

            update_input = UpdateInput(new_value="updated_value")
            update_result = await handle.execute_update("update_value", update_input.model_dump())
            assert isinstance(update_result, dict)
            assert update_result["old_value"] == "TestWorkflow"
            assert update_result["new_value"] == "updated_value"
            assert update_result["success"] is True

            await handle.signal("add_greeting", GreetingParams(name="Alice").model_dump())
            await handle.signal("add_greeting", GreetingParams(name="Bob").model_dump())

            result = await handle.result()
            assert isinstance(result, dict)
            assert result["success"] is True
            assert "2 greetings" in result["message"]
