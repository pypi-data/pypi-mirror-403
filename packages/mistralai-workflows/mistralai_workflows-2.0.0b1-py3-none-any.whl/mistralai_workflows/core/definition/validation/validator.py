import asyncio
import inspect
from types import NoneType, UnionType
from typing import Any, Callable, Dict, Tuple, Type, TypeVar, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel, TypeAdapter, ValidationError

from mistralai_workflows.core.definition.validation.schema_generator import (
    generate_pydantic_model_from_params,
    generate_pydantic_model_from_return_type,
)
from mistralai_workflows.core.dependencies.dependency_injector import DependsCls
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException

T = TypeVar("T", bound=Callable[..., Any])


def extract_origin_type(type_to_extract: Type) -> Type:
    origin = get_origin(type_to_extract)
    args: Tuple[Type, ...] = get_args(type_to_extract)
    if origin is Union and len(args) == 2 and NoneType in args:
        return next(arg for arg in args if arg is not NoneType)
    elif origin is UnionType and len(args) == 2 and NoneType in args:
        return next(arg for arg in args if arg is not NoneType)
    return type_to_extract


def check_is_valid_type(type_to_check: Type, expected_type: Type, allow_optional: bool = False) -> bool:
    if allow_optional:
        type_to_check = extract_origin_type(type_to_check)

    return (inspect.isclass(type_to_check) and issubclass(type_to_check, expected_type)) or (
        type_to_check is expected_type
    )


def get_function_signature_type_hints(func: Callable, is_method: bool) -> Tuple[Dict[str, Type], Type]:
    type_hints = get_type_hints(func)
    if "return" not in type_hints:
        raise WorkflowsException(
            code=ErrorCode.ACTIVITY_DEFINITION_ERROR,
            message=(
                f"'{func.__name__}' must have a return type annotation, use `-> None` if no return type is expected."
            ),
        )

    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())

    if is_method:
        if not param_names:
            raise WorkflowsException(
                code=ErrorCode.ACTIVITY_DEFINITION_ERROR,
                message=f"Method '{func.__name__}' has no parameters, expected 'self' or 'cls' as the first.",
            )
        type_hints.pop(param_names[0], None)
        param_names = param_names[1:]

    user_params_dict = {}
    for param_name in param_names:
        param = sig.parameters[param_name]

        if isinstance(param.default, DependsCls):
            continue

        # Only add to user params if it has a type hint
        if param_name in type_hints:
            user_params_dict[param_name] = type_hints[param_name]
        else:
            raise WorkflowsException(
                code=ErrorCode.ACTIVITY_DEFINITION_ERROR,
                message=f"Parameter '{param_name}' in '{func.__name__}' must have a type annotation.",
            )

    return_type = type_hints["return"]
    return user_params_dict, return_type


def raise_if_function_has_invalid_signature(func: Callable, is_method: bool = False) -> None:
    if not asyncio.iscoroutinefunction(func):
        raise WorkflowsException(
            code=ErrorCode.ACTIVITY_DEFINITION_ERROR,
            message=f"'{func.__name__}' must be async function. Use `async def`.",
        )

    user_params_dict, return_type = get_function_signature_type_hints(func, is_method=is_method)

    try:
        generate_pydantic_model_from_params(func.__name__, user_params_dict, func=func)
    except Exception as e:
        raise WorkflowsException(
            code=ErrorCode.ACTIVITY_DEFINITION_ERROR,
            message=f"Cannot generate Pydantic model from parameters of '{func.__name__}': {e}",
        ) from e

    try:
        generate_pydantic_model_from_return_type(func.__name__, return_type)
    except Exception as e:
        raise WorkflowsException(
            code=ErrorCode.ACTIVITY_DEFINITION_ERROR,
            message=f"Cannot generate Pydantic model from return type of '{func.__name__}': {e}",
        ) from e


def raise_if_function_has_invalid_usage(
    func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any], is_method: bool = False
) -> None:
    user_params_dict, _ = get_function_signature_type_hints(func, is_method=is_method)

    if is_method:
        args = args[1:]

    if len(kwargs) > 0:
        raise WorkflowsException(
            code=ErrorCode.INVALID_ARGUMENTS_ERROR,
            message=(
                f"'{func.__name__}' should not take keyword arguments, "
                "use positional arguments instead. Found: "
                f"{len(kwargs)} keyword arguments."
            ),
        )

    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    if is_method:
        param_names = param_names[1:]

    required_count = 0
    for param_name in param_names:
        param = sig.parameters[param_name]
        if isinstance(param.default, DependsCls):
            continue
        if param.default is inspect.Parameter.empty:
            required_count += 1

    total_param_count = len(user_params_dict)

    if len(args) < required_count or len(args) > total_param_count:
        raise WorkflowsException(
            code=ErrorCode.INVALID_ARGUMENTS_ERROR,
            message=(
                f"'{func.__name__}' expects {required_count} to {total_param_count} parameters. "
                f"Found: {len(args)} arguments."
            ),
        )

    for i, (param_name, param_type) in enumerate(user_params_dict.items()):
        if i < len(args):
            arg = args[i]
            if inspect.isclass(param_type) and issubclass(param_type, BaseModel):
                if not isinstance(arg, param_type):
                    raise WorkflowsException(
                        code=ErrorCode.INVALID_ARGUMENTS_ERROR,
                        message=(
                            f"Parameter '{param_name}' in '{func.__name__}' should be of type '{param_type}'. "
                            f"Found: '{type(arg)}'."
                        ),
                    )


def raise_if_function_has_invalid_return_type(func: Callable, return_value: Any, is_method: bool = False) -> None:
    _, return_type = get_function_signature_type_hints(func, is_method=is_method)

    try:
        adapter = TypeAdapter(return_type)
        adapter.validate_python(return_value, strict=True)
    except ValidationError as e:
        raise WorkflowsException(
            code=ErrorCode.ACTIVITY_DEFINITION_ERROR,
            message=f"'{func.__name__}' return type validation failed: {e}",
        ) from e


def validate_signal_handler_signature(func: Callable, is_method: bool = True) -> None:
    user_params_dict, _ = get_function_signature_type_hints(func, is_method=is_method)

    try:
        generate_pydantic_model_from_params(func.__name__, user_params_dict, func=func)
    except Exception as e:
        raise WorkflowsException(
            code=ErrorCode.WORKFLOW_SIGNAL_DEFINITION_ERROR,
            message=f"Signal '{func.__name__}' has invalid parameters for schema generation: {e}",
        ) from e


def validate_query_handler_signature(func: Callable, is_method: bool = True) -> None:
    if asyncio.iscoroutinefunction(func):
        raise WorkflowsException(
            code=ErrorCode.REJECTED_QUERY_ERROR,
            message=f"Query '{func.__name__}' must be a synchronous function (def), not async def.",
        )

    user_params_dict, return_type = get_function_signature_type_hints(func, is_method=is_method)

    try:
        generate_pydantic_model_from_params(func.__name__, user_params_dict, func=func)
    except Exception as e:
        raise WorkflowsException(
            code=ErrorCode.REJECTED_QUERY_ERROR,
            message=f"Query '{func.__name__}' has invalid parameters for schema generation: {e}",
        ) from e

    if return_type is NoneType or return_type is type(None):
        raise WorkflowsException(
            code=ErrorCode.REJECTED_QUERY_ERROR,
            message=f"Query '{func.__name__}' must have a return type annotation other than None.",
        )

    try:
        generate_pydantic_model_from_return_type(func.__name__, return_type)
    except Exception as e:
        raise WorkflowsException(
            code=ErrorCode.REJECTED_QUERY_ERROR,
            message=f"Query '{func.__name__}' has invalid return type for schema generation: {e}",
        ) from e


def validate_update_handler_signature(func: Callable, is_method: bool = True) -> None:
    user_params_dict, return_type = get_function_signature_type_hints(func, is_method=is_method)

    try:
        generate_pydantic_model_from_params(func.__name__, user_params_dict, func=func)
    except Exception as e:
        raise WorkflowsException(
            code=ErrorCode.WORKFLOW_UPDATE_DEFINITION_ERROR,
            message=f"Update '{func.__name__}' has invalid parameters for schema generation: {e}",
        ) from e

    if return_type is NoneType or return_type is type(None):
        raise WorkflowsException(
            code=ErrorCode.WORKFLOW_UPDATE_DEFINITION_ERROR,
            message=f"Update '{func.__name__}' must have a return type annotation other than None.",
        )

    try:
        generate_pydantic_model_from_return_type(func.__name__, return_type)
    except Exception as e:
        raise WorkflowsException(
            code=ErrorCode.WORKFLOW_UPDATE_DEFINITION_ERROR,
            message=f"Update '{func.__name__}' has invalid return type for schema generation: {e}",
        ) from e
