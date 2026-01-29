from __future__ import annotations

from collections.abc import Mapping, Sequence, Set as AbstractSet

from ._graphql import (
    GetDatabaseFields,
    GetDatabaseFieldsDatabaseDataModelDatabaseTables,
)
from ._identification import (
    ColumnIdentifier,
    JoinIdentifier,
    TableIdentifier,
)
from ._selection_field import SelectionField
from .client import Client


def _visit_table(
    table_identifier: TableIdentifier,
    /,
    *,
    column_identifiers: AbstractSet[ColumnIdentifier],
    join_identifiers: Sequence[JoinIdentifier],
    selection_field_from_column_identifier: dict[ColumnIdentifier, SelectionField],
    table_from_identifier: Mapping[
        TableIdentifier, GetDatabaseFieldsDatabaseDataModelDatabaseTables
    ],
) -> None:
    table = table_from_identifier[table_identifier]

    for column in table.columns:
        column_identifier = ColumnIdentifier(
            table_identifier=table_identifier,
            column_name=column.name,
        )

        if column_identifier not in column_identifiers:
            continue

        if (
            existing_selection_field_identifier
            := selection_field_from_column_identifier.get(column_identifier)
        ) is not None:  # pragma: no cover (missing tests)
            raise RuntimeError(
                f"{column_identifier} is reachable from different paths: {existing_selection_field_identifier.join_identifiers} and {join_identifiers}. "
            )

        selection_field_from_column_identifier[column_identifier] = SelectionField(
            join_identifiers, column_identifier
        )

    for join in table.joins:
        _visit_table(
            TableIdentifier._from_graphql(join.target),
            column_identifiers=column_identifiers,
            join_identifiers=[*join_identifiers, JoinIdentifier._from_graphql(join)],
            selection_field_from_column_identifier=selection_field_from_column_identifier,
            table_from_identifier=table_from_identifier,
        )


def _get_selection_field_from_column_identifier(
    all_store_fields: GetDatabaseFields,
    /,
    *,
    column_identifiers: AbstractSet[ColumnIdentifier],
    fact_table_identifier: TableIdentifier,
) -> dict[ColumnIdentifier, SelectionField]:
    selection_field_from_column_identifier: dict[ColumnIdentifier, SelectionField] = {}
    table_from_identifier = {
        TableIdentifier._from_graphql(table): table
        for table in all_store_fields.database_data_model.database.tables
    }
    _visit_table(
        fact_table_identifier,
        column_identifiers=column_identifiers,
        join_identifiers=[],
        selection_field_from_column_identifier=selection_field_from_column_identifier,
        table_from_identifier=table_from_identifier,
    )
    return selection_field_from_column_identifier


def get_selection_field_from_column_identifier(
    column_identifiers: AbstractSet[ColumnIdentifier],
    /,
    *,
    client: Client,
    fact_table_identifier: TableIdentifier,
) -> dict[ColumnIdentifier, SelectionField]:
    if not column_identifiers:
        return {}

    output = client._require_graphql_client().get_database_fields()

    return _get_selection_field_from_column_identifier(
        output,
        column_identifiers=column_identifiers,
        fact_table_identifier=fact_table_identifier,
    )
