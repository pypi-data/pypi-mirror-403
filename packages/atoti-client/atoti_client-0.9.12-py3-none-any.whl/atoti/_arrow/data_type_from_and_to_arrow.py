from collections.abc import Mapping

import pyarrow as pa

from .._data_type import DataType

# The order is significant.
# It is used by `data_type_to_arrow` to find the best matching type.
_DATA_TYPE_FROM_ARROW: Mapping[pa.DataType, DataType] = {
    pa.bool_(): "boolean",
    pa.float64(): "double",
    pa.list_(pa.float64()): "double[]",
    pa.float32(): "float",
    pa.list_(pa.float32()): "float[]",
    pa.int32(): "int",
    pa.list_(pa.int32()): "int[]",
    pa.date32(): "LocalDate",
    pa.timestamp("ns"): "LocalDateTime",
    pa.timestamp("s"): "LocalDateTime",
    pa.time64("ns"): "LocalTime",
    pa.int64(): "long",
    pa.list_(pa.int64()): "long[]",
    pa.string(): "String",
    # Not supported on purpose because PyArrow docs mentions:
    # > Unless you need to represent data larger than 2GB, you should prefer string().
    # See https://arrow.apache.org/docs/20.0/python/generated/pyarrow.large_string.html.
    # pa.large_string(): "String",
    pa.null(): "String",  # Consider changing this to `None`.
}


def data_type_from_arrow(
    arrow_data_type: pa.DataType,  # pyright: ignore[reportUnknownParameterType]
    /,
) -> DataType:
    if isinstance(arrow_data_type, pa.Decimal128Type | pa.Decimal256Type):
        return "double"

    if isinstance(arrow_data_type, pa.TimestampType) and arrow_data_type.tz is not None:
        return "ZonedDateTime"

    data_type = _DATA_TYPE_FROM_ARROW.get(arrow_data_type)
    if data_type is None:  # pragma: no cover
        raise ValueError(f"Unsupported Arrow DataType: {arrow_data_type}.")

    return data_type


def data_type_to_arrow(data_type: DataType, /) -> pa.DataType | None:  # pyright: ignore[reportUnknownParameterType]
    # Converting `ZonedDateTime` to an Arrow type is too complicated.
    # It will fall back to the type inferred by Arrow.
    if data_type == "ZonedDateTime":
        return None

    return next(
        arrow_data_type
        for arrow_data_type, _data_type in _DATA_TYPE_FROM_ARROW.items()
        if _data_type == data_type
    )
