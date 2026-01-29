from collections.abc import Callable
from typing import TypeAlias, TypeVar

from .client import DeleteStatus

_Key: TypeAlias = str | tuple[str, ...]


def _validate_delete_status(status: DeleteStatus, /, *, key: _Key) -> None:
    match status:
        case DeleteStatus.DELETED:
            return
        case (
            DeleteStatus.NOT_FOUND
        ):  # pragma: no branch (avoid `case _` to detect new variants)
            raise KeyError(key)


_O = TypeVar("_O")


def create_delete_status_validator(
    key: _Key,
    get_delete_status: Callable[[_O], DeleteStatus],
    /,
) -> Callable[[_O], None]:
    return lambda output: _validate_delete_status(get_delete_status(output), key=key)
