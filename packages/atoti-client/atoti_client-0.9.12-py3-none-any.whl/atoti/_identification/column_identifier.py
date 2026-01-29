from dataclasses import KW_ONLY
from typing import final

from pydantic.dataclasses import dataclass
from typing_extensions import Self, override

from .._graphql import (
    ColumnIdentifier as GraphqlColumnIdentifier,
    ColumnIdentifierFragment,
)
from ._identifier_pydantic_config import IDENTIFIER_PYDANTIC_CONFIG
from .column_name import ColumnName
from .identifier import Identifier
from .table_identifier import TableIdentifier


@final
@dataclass(config=IDENTIFIER_PYDANTIC_CONFIG, frozen=True)
class ColumnIdentifier(Identifier):
    """The identifier of a :class:`~atoti.Column` in the context of a :class:`~atoti.Session`."""

    table_identifier: TableIdentifier
    column_name: ColumnName
    _: KW_ONLY

    @classmethod
    def _from_graphql(
        cls, identifier: ColumnIdentifierFragment | GraphqlColumnIdentifier, /
    ) -> Self:
        match identifier:
            case ColumnIdentifierFragment():
                return cls(
                    TableIdentifier._from_graphql(identifier.table), identifier.name
                )
            case GraphqlColumnIdentifier():  # pragma: no branch (avoid `case _` to detect new variants)
                return cls(
                    TableIdentifier(identifier.table_name),
                    identifier.column_name,
                )

    def _to_graphql(self) -> GraphqlColumnIdentifier:
        return GraphqlColumnIdentifier(
            table_name=self.table_identifier.table_name,
            column_name=self.column_name,
        )

    @override
    def __repr__(self) -> str:
        return f"""{self.table_identifier}[{self.column_name!r}]"""
