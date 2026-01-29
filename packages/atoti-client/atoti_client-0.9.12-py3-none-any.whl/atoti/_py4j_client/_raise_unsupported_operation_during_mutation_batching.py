import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")  # ParamSpec for the function's arguments
_R = TypeVar("_R")  # Type variable for the function's return type


def raise_unsupported_operation_during_mutation_batching(
    function: Callable[_P, _R], /, *, is_batching_mutations: Callable[[object], bool]
) -> Callable[_P, _R]:
    @functools.wraps(function)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        self = args[0]
        if is_batching_mutations(self):
            raise RuntimeError(
                "This operation is not supported while batching mutations."
            )
        return function(*args, **kwargs)

    return wrapper
