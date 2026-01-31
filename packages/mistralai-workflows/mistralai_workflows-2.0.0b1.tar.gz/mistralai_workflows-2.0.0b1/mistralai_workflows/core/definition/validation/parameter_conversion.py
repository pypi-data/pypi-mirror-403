from typing import Any, Type

from pydantic import BaseModel


def convert_params_dict_to_user_args(
    params_dict: dict,
    user_params_dict: dict[str, Type],
    input_model: Type[BaseModel] | None,
) -> tuple[Any, ...]:
    """Convert Temporal's parameter dict to user function arguments."""
    if not input_model or not user_params_dict:
        return ()

    validated_params = input_model.model_validate(params_dict)

    if len(user_params_dict) == 1:
        param_name = next(iter(user_params_dict.keys()))
        param_type = user_params_dict[param_name]

        if hasattr(param_type, "__mro__") and BaseModel in param_type.__mro__:
            return (validated_params,)
        else:
            return (getattr(validated_params, param_name),)
    else:
        return tuple(getattr(validated_params, name) for name in user_params_dict.keys())


def convert_result_to_temporal_format(
    result: Any,
    output_model: Type[BaseModel] | None,
) -> Any:
    """Convert handler result to Temporal's dict format."""
    if result is None:
        return None

    if isinstance(result, BaseModel):
        return result.model_dump()

    if output_model:
        if hasattr(output_model, "model_fields") and "result" in output_model.model_fields:
            return output_model(result=result).model_dump()
        return output_model.model_validate(result).model_dump()

    return result


def convert_query_update_result_to_temporal_format(
    result: Any,
    output_model: Type[BaseModel] | None,
) -> Any:
    """Convert query/update handler result to Temporal's format.

    Unlike workflows, queries and updates return primitive values directly
    without wrapping them in a dict when called via Temporal's native client.
    """
    if result is None:
        return None

    if isinstance(result, BaseModel):
        return result.model_dump()

    return result
