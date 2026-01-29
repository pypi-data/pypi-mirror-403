import pyarrow as pa

from .._data_type import DataType
from .data_type_from_and_to_arrow import data_type_from_arrow


def _data_type_from_arrow(
    arrow_data_type: pa.DataType,  # pyright: ignore[reportUnknownParameterType]
    /,
    *,
    field_name: str,
) -> DataType:
    try:
        return data_type_from_arrow(arrow_data_type)
    except ValueError as error:  # pragma: no cover (missing tests)
        raise TypeError(f"Field `{field_name}` has unsupported DataType.") from error


def data_types_from_arrow(
    schema: pa.Schema,  # pyright: ignore[reportUnknownParameterType]
    /,
) -> dict[str, DataType]:
    return {
        field.name: _data_type_from_arrow(
            field.type.value_type
            if isinstance(field.type, pa.DictionaryType)
            else field.type,
            field_name=field.name,
        )
        for field in schema
    }
