from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

import pandas as pd

from .._column_definition import ColumnDefinition
from .._data_type import DataType
from .convert_series import convert_series


def create_dataframe(
    rows: Collection[tuple[object, ...]],
    column_definitions_or_data_types: Sequence[ColumnDefinition]
    | Mapping[str, DataType],
    /,
) -> pd.DataFrame:
    """Return a DataFrame with columns of the given data types."""
    columns: Collection[ColumnDefinition] = (
        [
            ColumnDefinition(name=name, data_type=data_type)
            for name, data_type in column_definitions_or_data_types.items()
        ]
        if isinstance(column_definitions_or_data_types, Mapping)
        else column_definitions_or_data_types
    )

    dataframe = pd.DataFrame(
        rows,
        columns=[columns.name for columns in columns],
        dtype="object",  # To prevent any preliminary conversion.
    )

    for column in columns:
        converted_series = convert_series(
            dataframe[column.name],
            data_type=column.data_type,
            nullable=column.nullable,
        )
        dataframe[column.name] = converted_series

    return dataframe
