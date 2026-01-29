from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from py4j.protocol import Py4JError, Py4JJavaError

_P = ParamSpec("_P")
_R = TypeVar("_R")


def retrieve_stack_trace_before_it_is_too_late(
    function: Callable[_P, _R],
) -> Callable[_P, _R]:
    @wraps(function)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        try:
            return function(*args, **kwargs)
        except Py4JJavaError as error:
            raise Py4JError(str(error)) from error

    return wrapper
