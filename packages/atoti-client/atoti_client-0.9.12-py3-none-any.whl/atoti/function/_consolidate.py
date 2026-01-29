from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from .._identification import ColumnIdentifier, Identifiable, identify
from .._measure.consolidated_measure import ConsolidateMeasure
from .._measure_convertible import VariableMeasureConvertible
from .._measure_definition import MeasureDefinition, convert_to_measure_definition
from ..hierarchy import Hierarchy

_Mode = Literal["shared-only", "shared-and-standard"]


def consolidate(
    measure: VariableMeasureConvertible | str,
    /,
    *,
    hierarchy: Hierarchy,
    factors: Sequence[Identifiable[ColumnIdentifier]],
    member_mode: _Mode = "shared-and-standard",
) -> MeasureDefinition:  # pragma: no cover (missing tests)
    columns = []
    for level_name in hierarchy:
        level = hierarchy[level_name]
        selection_field = level._selection_field
        assert selection_field
        columns.append(selection_field.column_identifier)
    return ConsolidateMeasure(
        _underlying_measure=convert_to_measure_definition(measure),
        _hierarchy=hierarchy._identifier,
        _level_columns=tuple(columns),
        _factors=tuple(identify(column) for column in factors),
        _member_mode=member_mode,
    )
