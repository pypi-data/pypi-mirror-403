from collections.abc import Callable, Sequence
from functools import wraps
from itertools import chain
from os import linesep
from typing import TypeVar

import httpx
from typing_extensions import ParamSpec

from .._env import get_env_flag
from ._get_http_client_attribute import get_http_client_attribute
from ._get_request_info import get_request_info
from ._threshold import Threshold
from ._track_http_requests import track_requests
from .cap_http_requests_env_var_name import CAP_HTTP_REQUESTS_ENV_VAR_NAME
from .has_http_client import HasHttpClient

_P = ParamSpec("_P")
_R = TypeVar("_R")


_ATTRIBUTE_NAME = "_cap_http_requests"


def _get_too_many_requests_message(
    function: Callable[_P, _R],
    /,
    *,
    requests: Sequence[httpx.Request],
    threshold: int,
) -> str:
    separator = "#" * 42
    return linesep.join(
        [
            f"Expected {function.__qualname__}() to send at most {threshold} HTTP requests, but {len(requests)} were sent:",
            *[
                line
                for index, request in enumerate(requests, start=1)
                for line in [
                    "",
                    separator,
                    "",
                    get_request_info(request, index=index),
                ]
            ],
            "",
        ]
    )


def cap_http_requests(
    threshold: Threshold,
    /,
    *,
    allow_missing_client: bool = False,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Decorate a callable to ensure that it sends at most *threshold* HTTP requests.

    The callable must take an HTTP client instance (or a provider of one) as either a positional argument, a keyword argument, or as a class attribute (if the callable is a method).
    """
    if isinstance(threshold, int):
        assert threshold >= 0

    # To prevent regressions when passing a client to a function that used to take none, the threshold is forced to zero.
    assert not allow_missing_client or threshold == 0

    if not get_env_flag(CAP_HTTP_REQUESTS_ENV_VAR_NAME):
        return lambda function: function

    def decorator(function: Callable[_P, _R], /) -> Callable[_P, _R]:
        if hasattr(function, _ATTRIBUTE_NAME):
            return function

        @wraps(function)
        def wrapper(
            *args: _P.args,
            **kwargs: _P.kwargs,
        ) -> _R:
            http_client: httpx.Client | None = next(
                (
                    arg.http_client if isinstance(arg, HasHttpClient) else arg
                    for arg in chain(args, kwargs.values())
                    if isinstance(arg, httpx.Client | HasHttpClient)
                ),
                None,
            )

            if http_client is None and args:
                http_client = get_http_client_attribute(args[0])

            if http_client is None:
                assert allow_missing_client, (
                    f"Could not find HTTP client in {function.__qualname__}()."
                )
                return function(*args, **kwargs)

            with track_requests(http_client) as requests:
                result = function(*args, **kwargs)

            if threshold != "unlimited" and len(requests) > threshold:
                message = _get_too_many_requests_message(
                    function, requests=requests, threshold=threshold
                )
                raise AssertionError(message)

            return result

        setattr(wrapper, _ATTRIBUTE_NAME, threshold)

        return wrapper

    return decorator
