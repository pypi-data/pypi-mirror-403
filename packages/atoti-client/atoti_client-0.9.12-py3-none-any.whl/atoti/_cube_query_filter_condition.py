from __future__ import annotations

from typing import Literal, TypeAlias

from ._constant import Constant, ScalarConstant
from ._identification import HierarchyIdentifier, LevelIdentifier, MeasureIdentifier
from ._operation import (
    EqualityOperator,
    HierarchyMembershipCondition,
    LogicalCondition,
    MembershipCondition,
    MembershipOperator,
    RelationalCondition,
    RelationalOperator,
)

_CubeQueryFilterHierarchyMembershipCondition: TypeAlias = HierarchyMembershipCondition[
    Literal["IN"], ScalarConstant
]
_CubeQueryFilterIsInHierarchyCondition: TypeAlias = MembershipCondition[
    HierarchyIdentifier, MembershipOperator, ScalarConstant
]
_CubeQueryFilterIsInLevelCondition: TypeAlias = MembershipCondition[
    LevelIdentifier, MembershipOperator, ScalarConstant
]
_CubeQueryFilterIsInMeasureCondition: TypeAlias = MembershipCondition[
    MeasureIdentifier, MembershipOperator, Constant | None
]
_CubeQueryFilterRelationalHierarchyCondition: TypeAlias = RelationalCondition[
    HierarchyIdentifier, EqualityOperator, ScalarConstant
]
_CubeQueryFilterRelationalLevelCondition: TypeAlias = RelationalCondition[
    LevelIdentifier, RelationalOperator, ScalarConstant
]
_CubeQueryFilterRelationalMeasureCondition: TypeAlias = RelationalCondition[
    MeasureIdentifier, RelationalOperator, Constant | None
]
_CubeQueryFilterLeafCondition: TypeAlias = (
    _CubeQueryFilterHierarchyMembershipCondition
    | _CubeQueryFilterIsInHierarchyCondition
    | _CubeQueryFilterIsInLevelCondition
    | _CubeQueryFilterIsInMeasureCondition
    | _CubeQueryFilterRelationalHierarchyCondition
    | _CubeQueryFilterRelationalLevelCondition
    | _CubeQueryFilterRelationalMeasureCondition
)
CubeQueryFilterCondition: TypeAlias = (
    _CubeQueryFilterLeafCondition
    | LogicalCondition[_CubeQueryFilterLeafCondition, Literal["AND"]]
)
