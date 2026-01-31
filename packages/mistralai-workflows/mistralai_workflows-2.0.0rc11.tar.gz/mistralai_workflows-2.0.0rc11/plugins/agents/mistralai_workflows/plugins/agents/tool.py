import json
from collections.abc import Awaitable, Callable
from typing import Any, Literal, cast

import mistralai
import mistralai.extra.run.tools
from mistralai_workflows.core.activity import check_is_activity, get_wrapped_activity
from mistralai_workflows.core.definition.validation.schema_generator import generate_pydantic_model_from_params
from mistralai_workflows.core.definition.validation.validator import get_function_signature_type_hints
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException
from pydantic import BaseModel, ValidationError

CustomTool = Callable[..., Awaitable[Any]]

Tool = (
    mistralai.CodeInterpreterTool
    | mistralai.DocumentLibraryTool
    | mistralai.FunctionTool
    | mistralai.ImageGenerationTool
    | mistralai.WebSearchTool
    | mistralai.WebSearchPremiumTool
    | CustomTool
)


_local_function_registry: dict[str, Callable] = {}


class ToolArgumentErrorResult(BaseModel):
    error: str
    success: Literal[False] = False


def raise_or_return_tool_call_error(
    message: str, raise_on_tool_fail: bool, code: ErrorCode, cause: Exception | None = None
) -> str:
    if raise_on_tool_fail:
        error = WorkflowsException(message, code=code)
        if cause:
            raise error from cause
        raise error
    return ToolArgumentErrorResult(error=message).model_dump_json()


def format_validation_error_for_llm(error: ValidationError, tool_name: str) -> str:
    """Format Pydantic validation errors in a clear way for LLMs."""
    errors = error.errors()

    error_lines = [f"Invalid arguments for tool {tool_name} with the following issues:\n"]

    for err in errors:
        location = " -> ".join(str(loc) for loc in err["loc"])
        error_type = err["type"]
        message = err["msg"]

        # Make it more readable
        if error_type == "missing":
            if location:
                error_lines.append(f"- Missing required field: '{location}'")
            else:
                error_lines.append("- Missing required field")
        elif "type" in error_type:
            if location:
                error_lines.append(f"- Wrong type for '{location}': {message}")
            else:
                error_lines.append(f"- Wrong type: {message}")
        else:
            if location:
                error_lines.append(f"- Error in '{location}': {message}")
            else:
                error_lines.append(f"- Error: {message}")

    return "\n".join(error_lines)


def check_is_custom_tool(tool: Tool) -> bool:
    return callable(tool)


def get_tool_name(tool: Tool) -> str | None:
    if callable(tool):
        return tool.__name__
    else:
        return tool.type


def convert_tool_to_mistral_tool(tool: Tool) -> mistralai.AgentCreationRequestToolsTypedDict:
    if callable(tool):
        if not check_is_activity(tool):
            _local_function_registry[tool.__name__] = tool
        mistral_tool_obj = mistralai.extra.run.tools.create_tool_call(tool)
        mistral_tool_obj.function.strict = None
        mistral_tool = mistral_tool_obj.model_dump()
    else:
        mistral_tool = tool.model_dump()
    return cast(mistralai.AgentCreationRequestToolsTypedDict, mistral_tool)


async def execute_activity_tool(
    activity_tool_name: str, activity_tool_kwargs: str | dict, raise_on_tool_fail: bool
) -> str:
    activity = get_wrapped_activity(activity_tool_name)
    if not activity:
        if activity_tool_name in _local_function_registry:
            activity = _local_function_registry[activity_tool_name]
        else:
            return raise_or_return_tool_call_error(
                f"Invalid tool name {activity_tool_name}.\nCould not find it in the declared agent tools.",
                raise_on_tool_fail,
                code=ErrorCode.ACTIVITY_NOT_FOUND_ERROR,
            )

    user_params_dict, _ = get_function_signature_type_hints(activity, is_method=False)

    param_type = None
    if user_params_dict:
        param_type = generate_pydantic_model_from_params(activity.__name__, user_params_dict, func=activity)

    if isinstance(activity_tool_kwargs, dict):
        json_params = activity_tool_kwargs
    elif isinstance(activity_tool_kwargs, str):
        try:
            json_params = json.loads(activity_tool_kwargs)
        except json.JSONDecodeError as e:
            return raise_or_return_tool_call_error(
                f"Invalid arguments for tool {activity_tool_name}.\n"
                f"Could not parse JSON provided to tool {activity_tool_kwargs}\nError: {e}",
                raise_on_tool_fail,
                code=ErrorCode.TOOL_ARGUMENT_ERROR,
                cause=e,
            )
    else:
        raise WorkflowsException(
            message=(
                f"Invalid arguments for tool {activity_tool_name}, "
                f"expected a string or dict. Got {type(activity_tool_kwargs)}"
            ),
            code=ErrorCode.TOOL_ARGUMENT_ERROR,
        )

    if param_type is not None:
        if len(json_params) != 1:
            return raise_or_return_tool_call_error(
                f"Invalid arguments for tool {activity_tool_name}, "
                f"expected a single argument in the form of : {param_type.model_json_schema()}",
                raise_on_tool_fail,
                code=ErrorCode.TOOL_ARGUMENT_ERROR,
            )

        json_param_key = next(iter(json_params))
        try:
            params = param_type.model_validate(json_params[json_param_key])
            result = await activity(params)
        except ValidationError as e:
            validation_error_message = (
                f"Invalid arguments for tool {activity_tool_name}: {e}"
                if raise_on_tool_fail
                else format_validation_error_for_llm(e, activity_tool_name)
            )
            return raise_or_return_tool_call_error(
                validation_error_message,
                raise_on_tool_fail,
                code=ErrorCode.TOOL_ARGUMENT_ERROR,
                cause=e,
            )

    else:
        result = await activity()

    assert not result or isinstance(result, BaseModel)
    return result.model_dump_json() if result else "None"
