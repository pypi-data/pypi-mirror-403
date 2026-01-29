from collections.abc import Callable
from inspect import signature
from typing import TypeVar

from pydantic import validate_call as __validate_call
from typing_extensions import ParamSpec

from ._env import get_env_flag
from ._pydantic import PYDANTIC_CONFIG as _PYDANTIC_CONFIG

_P = ParamSpec("_P")
_R = TypeVar("_R")


_validate_call = __validate_call(config=_PYDANTIC_CONFIG)

DISABLE_CALL_VALIDATION_ENV_VAR_NAME = "_ATOTI_DISABLE_CALL_VALIDATION"


def _has_parameters(function: Callable[..., object], /) -> bool:
    parameters = signature(function).parameters
    parameter_names = list(parameters)
    if parameter_names and parameter_names[0] == "self":
        del parameter_names[0]
    return bool(parameter_names)


def validate_call(function: Callable[_P, _R], /) -> Callable[_P, _R]:
    if (
        not __debug__
        or get_env_flag(DISABLE_CALL_VALIDATION_ENV_VAR_NAME)
        # Since return type validation is skipped, functions without parameters do not need validation at all.
        or not _has_parameters(function)
    ):
        return function

    return _validate_call(function)
