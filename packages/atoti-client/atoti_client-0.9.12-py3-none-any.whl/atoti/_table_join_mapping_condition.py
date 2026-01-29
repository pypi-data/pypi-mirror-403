from typing import Literal, TypeAlias

from ._identification import ColumnIdentifier
from ._operation import LogicalCondition, RelationalCondition

_TableJoinMappingLeafCondition: TypeAlias = RelationalCondition[
    ColumnIdentifier,
    Literal["EQ"],
    ColumnIdentifier,
]
TableJoinMappingCondition: TypeAlias = (
    _TableJoinMappingLeafCondition
    | LogicalCondition[_TableJoinMappingLeafCondition, Literal["AND"]]
)
