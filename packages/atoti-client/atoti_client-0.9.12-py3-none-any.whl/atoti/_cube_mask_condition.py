from typing import Literal, TypeAlias

from ._constant import ScalarConstant
from ._identification import HierarchyIdentifier
from ._operation import (
    EqualityOperator,
    HierarchyMembershipConditionBound,
    LogicalCondition,
    MembershipCondition,
    MembershipOperator,
    RelationalCondition,
)

_CubeMaskLeafCondition: TypeAlias = (
    HierarchyMembershipConditionBound
    | MembershipCondition[HierarchyIdentifier, MembershipOperator, ScalarConstant]
    | RelationalCondition[HierarchyIdentifier, EqualityOperator, ScalarConstant]
)

CubeMaskCondition: TypeAlias = (
    _CubeMaskLeafCondition | LogicalCondition[_CubeMaskLeafCondition, Literal["AND"]]
)
