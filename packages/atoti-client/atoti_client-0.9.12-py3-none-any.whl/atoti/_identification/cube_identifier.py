from dataclasses import KW_ONLY
from typing import final

from pydantic.dataclasses import dataclass
from typing_extensions import override

from ._identifier_pydantic_config import IDENTIFIER_PYDANTIC_CONFIG
from .cube_name import CubeName
from .identifier import Identifier


@final
@dataclass(config=IDENTIFIER_PYDANTIC_CONFIG, frozen=True)
class CubeIdentifier(Identifier):
    """The identifier of a :class:`~atoti.Cube` in the context of a :class:`~atoti.Session`."""

    cube_name: CubeName
    _: KW_ONLY

    @override
    def __repr__(self) -> str:  # pragma: no cover (missing tests)
        return f"cubes[{self.cube_name!r}]"
