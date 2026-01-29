from __future__ import annotations

from typing import Literal, TypeAlias

from .._constant import ScalarConstant
from .._graphql import (
    CubeRestrictionCondition as GraphqlCubeRestrictionCondition,
    CubeRestrictionLeafCondition as GraphqlCubeRestrictionLeafCondition,
    CubeRestrictionLogicalCondition as GraphqlCubeRestrictionLogicalCondition,
    CubeRestrictionLogicalConditionOperator as GraphqlCubeRestrictionLogicalConditionOperator,
    CubeRestrictionMembershipCondition as GraphqlCubeRestrictionMembershipCondition,
    CubeRestrictionMembershipConditionOperator as GraphqlCubeRestrictionMembershipConditionOperator,
    CubeRestrictionRelationalCondition as GraphqlCubeRestrictionRelationalCondition,
    CubeRestrictionRelationalConditionOperator as GraphqlCubeRestrictionRelationalConditionOperator,
)
from .._identification import LevelIdentifier
from .._operation import (
    LogicalCondition,
    MembershipCondition,
    RelationalCondition,
    condition_from_graphql,
    condition_to_graphql,
)

CubeRestrictionMembershipConditionOperator: TypeAlias = Literal["IN"]
CubeRestrictionRelationalConditionOperator: TypeAlias = Literal["EQ"]
CubeRestrictionLeafCondition: TypeAlias = (
    MembershipCondition[
        LevelIdentifier, CubeRestrictionMembershipConditionOperator, ScalarConstant
    ]
    | RelationalCondition[
        LevelIdentifier, CubeRestrictionRelationalConditionOperator, ScalarConstant
    ]
)
CubeRestrictionLogicalConditionOperator: TypeAlias = Literal["AND"]
CubeRestrictionLogicalCondition: TypeAlias = LogicalCondition[
    CubeRestrictionLeafCondition, CubeRestrictionLogicalConditionOperator
]
CubeRestrictionCondition: TypeAlias = (
    CubeRestrictionLeafCondition | CubeRestrictionLogicalCondition
)


def cube_restriction_condition_from_graphql(
    condition: GraphqlCubeRestrictionCondition, /
) -> CubeRestrictionCondition:
    return condition_from_graphql(
        condition,
        convert_leaf_condition_subject=LevelIdentifier._from_graphql,
        convert_membership_condition_operator=lambda operator: operator.value,
        convert_membership_condition_element=lambda element: element,
        convert_relational_condition_operator=lambda operator: operator.value,
        convert_relational_condition_target=lambda target: target,
        convert_logical_condition_operator=lambda operator: operator.value,
    )


def cube_restriction_condition_to_graphql(
    condition: CubeRestrictionCondition, /
) -> GraphqlCubeRestrictionCondition:
    return condition_to_graphql(  # type: ignore[no-any-return]
        condition,
        convert_leaf_condition_subject=lambda subject: subject._to_graphql(),
        membership_condition_class=GraphqlCubeRestrictionMembershipCondition,
        membership_condition_operator_class=GraphqlCubeRestrictionMembershipConditionOperator,
        convert_membership_condition_element=lambda element: element,
        relational_condition_class=GraphqlCubeRestrictionRelationalCondition,
        relational_condition_operator_class=GraphqlCubeRestrictionRelationalConditionOperator,
        convert_relational_condition_target=lambda target: target,
        leaf_condition_class=GraphqlCubeRestrictionLeafCondition,
        logical_condition_class=GraphqlCubeRestrictionLogicalCondition,
        logical_condition_operator_class=GraphqlCubeRestrictionLogicalConditionOperator,
        condition_class=GraphqlCubeRestrictionCondition,
    )
