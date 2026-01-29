from abc import ABC, abstractmethod

from pydantic.dataclasses import dataclass

from .._pydantic import PYDANTIC_CONFIG as _PYDANTIC_CONFIG, get_type_adapter


def _stringify_property(value: object) -> str:
    match value:
        case bool():
            return str(value).lower()
        case int():  # pragma: no cover (trivial)
            return str(value)
        case str():  # pragma: no cover (trivial)
            return value
        case _:  # pragma: no cover (missing tests)
            raise TypeError(f"Unsupported property type: `{type(value)}`.")


@dataclass(config=_PYDANTIC_CONFIG, frozen=True)
class DiscoveryProtocol(ABC):
    """Protocol used by a :class:`~atoti.Cluster` to discover its nodes and let them communicate with each other.

    The available protocols are:

    * :class:`~atoti_jdbc.JdbcPingDiscoveryProtocol`
    * :class:`~atoti_aws.S3PingDiscoveryProtocol`

    """

    @property
    @abstractmethod
    def _name(self) -> str: ...

    @property
    def _properties(self) -> dict[str, object]:
        type_adapter = get_type_adapter(type(self))
        properties = type_adapter.dump_python(self)
        assert isinstance(properties, dict)
        return properties

    @property
    def _xml(self) -> str:
        stringified_properties = " ".join(
            f'{key}="{_stringify_property(value)}"'
            for key, value in self._properties.items()
            if value is not None
        )
        return f"<{self._name} {stringified_properties} />"
