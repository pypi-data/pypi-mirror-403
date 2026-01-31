import inspect
from types import NoneType, UnionType
from typing import Callable, Dict, Type, Union, get_args, get_origin

from pydantic import BaseModel, Field, create_model


def generate_pydantic_model_from_params(
    func_name: str, user_params_dict: Dict[str, Type], model_suffix: str = "Input", func: Callable | None = None
) -> Type[BaseModel] | None:
    if not user_params_dict:
        model_name = f"{func_name}_{model_suffix}"
        return create_model(model_name)

    if len(user_params_dict) == 1:
        param_type = next(iter(user_params_dict.values()))
        if inspect.isclass(param_type) and issubclass(param_type, BaseModel):
            return param_type

    fields = {}
    sig = inspect.signature(func) if func else None

    for param_name, param_type in user_params_dict.items():
        if sig and param_name in sig.parameters:
            param = sig.parameters[param_name]
            if param.default is not inspect.Parameter.empty:
                fields[param_name] = (param_type, Field(default=param.default))
            else:
                fields[param_name] = (param_type, ...)
        else:
            fields[param_name] = (param_type, ...)

    model_name = f"{func_name}_{model_suffix}"
    return create_model(model_name, **fields)  # type: ignore[call-overload, no-any-return]


def generate_pydantic_model_from_return_type(
    func_name: str, return_type: Type, model_suffix: str = "Output"
) -> Type[BaseModel] | None:
    if return_type is NoneType or return_type is type(None):
        return None

    if inspect.isclass(return_type) and issubclass(return_type, BaseModel):
        return return_type

    origin = get_origin(return_type)
    if origin in (Union, UnionType):
        args = get_args(return_type)
        non_none_types = [arg for arg in args if arg is not NoneType and arg is not type(None)]
        if non_none_types:
            actual_type = non_none_types[0]
            if inspect.isclass(actual_type) and issubclass(actual_type, BaseModel):
                return actual_type
            return_type = actual_type

    model_name = f"{func_name}_{model_suffix}"
    return create_model(model_name, result=(return_type, ...))
