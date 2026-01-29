from collections.abc import Callable
from typing import Final, ParamSpec, TypeVar

from ._cap_http_requests import HasHttpClient, cap_http_requests

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _is_measure_function(function: Callable[_P, _R]) -> bool:
    for measure_function_module_names in (
        "atoti.agg",
        "atoti.array",
        "atoti.finance",
        "atoti.function",
        "atoti.math",
    ):
        if (
            function.__module__ == measure_function_module_names
            or function.__module__.startswith(f"{measure_function_module_names}.")
        ):
            return True

    return False


_DEFAULT_THRESHOLD: Final = 1


def auto_cap_http_requests(function: Callable[_P, _R], /) -> Callable[_P, _R]:
    http_client_getter = HasHttpClient.http_client.fget  # type: ignore[attr-defined]
    assert http_client_getter is not None

    if (
        function.__name__ == http_client_getter.__name__
        or function.__qualname__ == "Session.client"
    ):
        # To avoid infinite recursion.
        return function

    if function.__name__ in {
        # An `__init__()` method in the API is either:
        # - a dataclass constructor without a `Client` parameter since dataclasses should not cause side effects.
        # - a regular class constructor which should not cause side effects either because the better place for them is the `__enter__()` method.
        "__init__",
        "isin",
        "isnull",
    } or _is_measure_function(function):
        return cap_http_requests(0, allow_missing_client=True)(function)

    return cap_http_requests(_DEFAULT_THRESHOLD)(function)
