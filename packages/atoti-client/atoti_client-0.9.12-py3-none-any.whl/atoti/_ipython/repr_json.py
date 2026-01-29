from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection, Mapping, Set as AbstractSet
from typing import Any, final

from typing_extensions import override

_INDENTATION = "  "

ReprJson = tuple[Any, dict[str, bool | str]]


def _json_to_html(
    obj: Collection[Any] | Mapping[str, Any],
    *,
    indent: int = 0,
) -> str:
    return (
        _mapping_to_html(obj, indent=indent)
        if isinstance(obj, Mapping)
        else _iterable_to_html(obj, indent=indent)
    )


def _mapping_to_html(mapping: Mapping[str, Any], *, indent: int = 0) -> str:
    pretty = f"{_INDENTATION * indent}<ul>\n"
    for key, value in mapping.items():
        if isinstance(value, Collection | Mapping) and not isinstance(value, str):
            pretty += f"{_INDENTATION * indent}<li>{key}\n"
            pretty += _json_to_html(value, indent=indent + 1)
            pretty += f"{_INDENTATION * indent}</li>\n"
        else:  # pragma: no cover (missing tests)
            pretty += f"{_INDENTATION * indent}<li>{key}: {value}</li>\n"
    return f"{pretty}{_INDENTATION * indent}</ul>\n"


def _iterable_to_html(iterable: Collection[Any], *, indent: int = 0) -> str:
    pretty = f"{_INDENTATION * indent}<ol>\n"
    for value in iterable:
        if isinstance(value, Collection | Mapping) and not isinstance(
            value, str
        ):  # pragma: no cover (missing tests)
            pretty += f"{_INDENTATION * indent}<li>{_json_to_html(value, indent=indent + 1)}</li>\n"
        else:
            pretty += f"{_INDENTATION * indent}<li>{value}</li>\n"
    return f"{pretty}{_INDENTATION * indent}</ol>"


_CLASSES: set[type] = set()


def inheriting_classes() -> AbstractSet[type]:
    return _CLASSES


class ReprJsonable(ABC):
    @override
    def __init_subclass__(cls, *args: object, **kwargs: object) -> None:
        super().__init_subclass__(*args, **kwargs)

        if not __debug__:
            return

        if (
            ABC not in cls.__bases__
        ):  # pragma: no branch (impossible to check if a class is `@final` at runtime)
            _CLASSES.add(cls)

    @abstractmethod
    def _repr_json_(self) -> ReprJson: ...

    @final
    def _repr_html_(self) -> str:
        repr_json = self._repr_json_()
        metadata = repr_json[1]
        if "root" in metadata:
            obj = {str(repr_json[1]["root"]): repr_json[0]}
        else:  # pragma: no cover (missing tests)
            obj = repr_json[0]
        return _json_to_html(obj)
