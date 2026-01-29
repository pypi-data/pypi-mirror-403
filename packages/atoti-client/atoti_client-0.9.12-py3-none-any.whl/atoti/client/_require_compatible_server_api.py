from typing import TypeVar

_T = TypeVar("_T")


def require_compatible_server_api(value: _T | None) -> _T:
    if value is None:
        raise RuntimeError(
            "This action is not available. See `Session.connect()`'s documentation for more information."
        )
    return value
