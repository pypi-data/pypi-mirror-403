from typing import Optional

import pytest
from pydantic import BaseModel, Field

from mistralai_workflows import workflow
from mistralai_workflows.core.definition.validation.validator import (
    get_function_signature_type_hints,
    raise_if_function_has_invalid_return_type,
    raise_if_function_has_invalid_signature,
    raise_if_function_has_invalid_usage,
)
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException


class ParamsModel(BaseModel):
    name: str = Field(description="Test name")
    count: int = Field(default=1)


class ResultModel(BaseModel):
    message: str
    success: bool = True


class TestGetFunctionSignatureTypeHints:
    def test_function_with_dependency_injection(self) -> None:
        from mistralai_workflows.core.dependencies.dependency_injector import Depends

        def get_service() -> str:
            return "service"

        async def test_func(params: ParamsModel, service: str = Depends(get_service)) -> ResultModel:
            return ResultModel(message="ok")

        params_dict, return_type = get_function_signature_type_hints(test_func, is_method=False)

        # Should only count params, not dependency
        assert "params" in params_dict
        assert params_dict["params"] == ParamsModel
        assert "service" not in params_dict  # Depends params are filtered out
        assert return_type == ResultModel

    def test_function_without_type_annotation_raises_error(self) -> None:
        async def test_func(params) -> ResultModel:  # type: ignore[no-untyped-def]
            return ResultModel(message="ok")

        with pytest.raises(WorkflowsException, match="must have a type annotation") as exc:
            get_function_signature_type_hints(test_func, is_method=False)
        assert exc.value.code == ErrorCode.ACTIVITY_DEFINITION_ERROR


class TestRaiseIfFunctionHasInvalidSignature:
    def test_sync_function_raises_error(self) -> None:
        def sync_func(params: ParamsModel) -> ResultModel:
            return ResultModel(message="sync")

        with pytest.raises(WorkflowsException, match="must be async function") as exc:
            raise_if_function_has_invalid_signature(sync_func, is_method=False)
        assert exc.value.code == ErrorCode.ACTIVITY_DEFINITION_ERROR

    def test_primitive_param_works(self) -> None:
        async def valid_func(name: str, count: int) -> dict:
            return {"name": name, "count": count}

        raise_if_function_has_invalid_signature(valid_func, is_method=False)

    def test_primitive_return_works(self) -> None:
        async def valid_func(params: ParamsModel) -> str:
            return "valid"

        raise_if_function_has_invalid_signature(valid_func, is_method=False)

    def test_invalid_pydantic_conversion_raises_error(self) -> None:
        class InvalidType:
            def __init__(self) -> None:
                self.value = "test"

        async def invalid_func(params: InvalidType) -> ResultModel:
            return ResultModel(message="ok")

        with pytest.raises(WorkflowsException, match="Cannot generate Pydantic model from parameters") as exc:
            raise_if_function_has_invalid_signature(invalid_func, is_method=False)
        assert exc.value.code == ErrorCode.ACTIVITY_DEFINITION_ERROR

    def test_invalid_return_type_pydantic_conversion_raises_error(self) -> None:
        class InvalidReturnType:
            def __init__(self) -> None:
                self.value = "test"

        async def invalid_func(params: ParamsModel) -> InvalidReturnType:
            return InvalidReturnType()

        with pytest.raises(WorkflowsException, match="Cannot generate Pydantic model from return type") as exc:
            raise_if_function_has_invalid_signature(invalid_func, is_method=False)
        assert exc.value.code == ErrorCode.ACTIVITY_DEFINITION_ERROR


class TestRaiseIfFunctionHasInvalidUsage:
    def test_kwargs_raises_error(self) -> None:
        async def test_func(params: ParamsModel) -> ResultModel:
            return ResultModel(message="ok")

        with pytest.raises(WorkflowsException, match="should not take keyword arguments") as exc:
            raise_if_function_has_invalid_usage(test_func, (), {"params": ParamsModel(name="test")}, is_method=False)
        assert exc.value.code == ErrorCode.INVALID_ARGUMENTS_ERROR

    def test_wrong_param_type_raises_error(self) -> None:
        async def test_func(params: ParamsModel) -> ResultModel:
            return ResultModel(message="ok")

        with pytest.raises(WorkflowsException, match="should be of type") as exc:
            raise_if_function_has_invalid_usage(test_func, ("wrong_type",), {}, is_method=False)
        assert exc.value.code == ErrorCode.INVALID_ARGUMENTS_ERROR

    def test_wrong_param_count_raises_error(self) -> None:
        async def test_func(param1: ParamsModel, param2: str) -> ResultModel:
            return ResultModel(message="ok")

        with pytest.raises(WorkflowsException, match="expects 2 to 2 parameters. Found: 1") as exc:
            raise_if_function_has_invalid_usage(test_func, (ParamsModel(name="test"),), {}, is_method=False)
        assert exc.value.code == ErrorCode.INVALID_ARGUMENTS_ERROR


class TestRaiseIfFunctionHasInvalidReturnType:
    def test_wrong_return_type_raises_error(self) -> None:
        async def test_func(params: ParamsModel) -> ResultModel:
            return ResultModel(message="ok")

        with pytest.raises(WorkflowsException, match="return type validation failed") as exc:
            raise_if_function_has_invalid_return_type(test_func, "wrong_type", is_method=False)
        assert exc.value.code == ErrorCode.ACTIVITY_DEFINITION_ERROR

    def test_pydantic_model_validation_error(self) -> None:
        async def test_func(params: ParamsModel) -> ResultModel:
            return ResultModel(message="ok")

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func, {"invalid": "structure"}, is_method=False)

    def test_generic_list_return_type_works(self) -> None:
        async def test_func_list_str(offset: int, limit: int) -> list[str]:
            return ["item1", "item2", "item3"]

        # This should not raise TypeError
        result = ["item1", "item2", "item3"]
        raise_if_function_has_invalid_return_type(test_func_list_str, result, is_method=False)

    def test_generic_dict_return_type_works(self) -> None:
        async def test_func_dict(key: str) -> dict[str, int]:
            return {"count": 42}

        result = {"count": 42}
        raise_if_function_has_invalid_return_type(test_func_dict, result, is_method=False)

    def test_generic_optional_list_return_type_works(self) -> None:
        async def test_func_optional_list(query: str) -> Optional[list[str]]:
            return ["result1", "result2"]

        result = ["result1", "result2"]
        raise_if_function_has_invalid_return_type(test_func_optional_list, result, is_method=False)

        raise_if_function_has_invalid_return_type(test_func_optional_list, None, is_method=False)

    def test_list_with_wrong_element_type_raises_error(self) -> None:
        async def test_func_list_str(offset: int, limit: int) -> list[str]:
            return ["item1", "item2", "item3"]

        with pytest.raises(WorkflowsException, match="return type validation failed") as exc:
            raise_if_function_has_invalid_return_type(test_func_list_str, [1, 2, 3], is_method=False)
        assert exc.value.code == ErrorCode.ACTIVITY_DEFINITION_ERROR

    def test_list_with_mixed_element_types_raises_error(self) -> None:
        async def test_func_list_str(offset: int, limit: int) -> list[str]:
            return ["item1", "item2", "item3"]

        with pytest.raises(WorkflowsException, match="return type validation failed") as exc:
            raise_if_function_has_invalid_return_type(test_func_list_str, ["str", 1, 2], is_method=False)
        assert exc.value.code == ErrorCode.ACTIVITY_DEFINITION_ERROR

    def test_dict_with_wrong_value_type_raises_error(self) -> None:
        async def test_func_dict(key: str) -> dict[str, int]:
            return {"count": 42}

        with pytest.raises(WorkflowsException, match="return type validation failed") as exc:
            raise_if_function_has_invalid_return_type(test_func_dict, {"count": "not_an_int"}, is_method=False)
        assert exc.value.code == ErrorCode.ACTIVITY_DEFINITION_ERROR

    def test_nested_list_dict_validation(self) -> None:
        async def test_func_nested(query: str) -> list[dict[str, int]]:
            return [{"count": 1}, {"count": 2}]

        raise_if_function_has_invalid_return_type(test_func_nested, [{"count": 1}, {"count": 2}], is_method=False)

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func_nested, [{"count": "wrong"}], is_method=False)

    def test_tuple_fixed_length_validation(self) -> None:
        async def test_func_tuple(query: str) -> tuple[str, int, bool]:
            return ("test", 42, True)

        raise_if_function_has_invalid_return_type(test_func_tuple, ("test", 42, True), is_method=False)

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func_tuple, ("test", "wrong", True), is_method=False)

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func_tuple, ("test", 42), is_method=False)

    def test_tuple_variable_length_validation(self) -> None:
        async def test_func_tuple(query: str) -> tuple[str, ...]:
            return ("a", "b", "c")

        raise_if_function_has_invalid_return_type(test_func_tuple, ("a", "b", "c"), is_method=False)

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func_tuple, ("a", 1, "c"), is_method=False)

    def test_set_validation(self) -> None:
        async def test_func_set(query: str) -> set[str]:
            return {"a", "b", "c"}

        raise_if_function_has_invalid_return_type(test_func_set, {"a", "b", "c"}, is_method=False)

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func_set, {1, 2, 3}, is_method=False)

    def test_frozenset_validation(self) -> None:
        async def test_func_frozenset(query: str) -> frozenset[int]:
            return frozenset([1, 2, 3])

        raise_if_function_has_invalid_return_type(test_func_frozenset, frozenset([1, 2, 3]), is_method=False)

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func_frozenset, frozenset(["a", "b"]), is_method=False)

    def test_union_validation(self) -> None:
        async def test_func_union(query: str) -> str | int:
            return "test"

        raise_if_function_has_invalid_return_type(test_func_union, "test", is_method=False)

        raise_if_function_has_invalid_return_type(test_func_union, 42, is_method=False)

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func_union, [], is_method=False)

    def test_deeply_nested_validation(self) -> None:
        async def test_func_deep(query: str) -> dict[str, list[tuple[int, str]]]:
            return {"key": [(1, "a"), (2, "b")]}

        raise_if_function_has_invalid_return_type(test_func_deep, {"key": [(1, "a"), (2, "b")]}, is_method=False)

        with pytest.raises(WorkflowsException, match="return type validation failed"):
            raise_if_function_has_invalid_return_type(test_func_deep, {"key": [(1, 2), (2, "b")]}, is_method=False)


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

    def test_query_with_invalid_return_type_schema(self) -> None:
        class InvalidType:
            value: str

        with pytest.raises(WorkflowsException, match="has invalid return type for schema generation"):

            @workflow.define(name="test_workflow")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

                @workflow.query()
                def invalid_query(self) -> InvalidType:
                    return InvalidType()


class TestReservedHandlerNames:
    def test_reserved_query_name_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Query name '__get_pending_inputs' is reserved by the framework"):

            @workflow.define(name="test_workflow_reserved_query")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

                @workflow.query(name="__get_pending_inputs")
                def bad_query(self) -> dict:
                    return {}

    def test_reserved_update_name_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Update name '__submit_input' is reserved by the framework"):

            @workflow.define(name="test_workflow_reserved_update")
            class TestWorkflow:
                @workflow.entrypoint
                async def run(self) -> None:
                    pass

                @workflow.update(name="__submit_input")
                async def bad_update(self, data: dict) -> dict:
                    return {}
