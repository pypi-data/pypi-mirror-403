from __future__ import annotations

from typing import Literal, TypeAlias

from ._constant import ScalarConstant
from ._identification import ColumnIdentifier
from ._operation import (
    LogicalCondition,
    LogicalOperator,
    MembershipCondition,
    RelationalCondition,
    RelationalOperator,
)

ScalarConstantColumnLeafCondition: TypeAlias = (
    MembershipCondition[ColumnIdentifier, Literal["IN"], ScalarConstant | None]
    | RelationalCondition[ColumnIdentifier, RelationalOperator, ScalarConstant | None]
)
ScalarConstantColumnLogicalCondition: TypeAlias = LogicalCondition[
    ScalarConstantColumnLeafCondition, LogicalOperator
]
ScalarConstantColumnCondition: TypeAlias = (
    ScalarConstantColumnLeafCondition | ScalarConstantColumnLogicalCondition
)
