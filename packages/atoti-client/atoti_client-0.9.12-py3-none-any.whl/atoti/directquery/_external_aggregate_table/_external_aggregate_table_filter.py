from __future__ import annotations

from typing import Literal, TypeAlias

from ..._constant import Constant
from ..._identification import ColumnIdentifier
from ..._operation import LogicalCondition, MembershipCondition, RelationalCondition

_ExternalAggregateTableFilterLeafCondition: TypeAlias = (
    MembershipCondition[ColumnIdentifier, Literal["IN"], Constant]
    | RelationalCondition[ColumnIdentifier, Literal["EQ"], Constant]
)
ExternalAggregateTableFilterCondition: TypeAlias = (
    _ExternalAggregateTableFilterLeafCondition
    | LogicalCondition[_ExternalAggregateTableFilterLeafCondition, Literal["AND"]]
)
