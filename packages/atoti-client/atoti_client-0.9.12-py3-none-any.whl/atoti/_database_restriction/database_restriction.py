from __future__ import annotations

from typing import Literal, TypeAlias

from .._constant import ScalarConstant
from .._graphql import (
    DatabaseRestrictionCondition as GraphqlDatabaseRestrictionCondition,
    DatabaseRestrictionLeafCondition as GraphqlDatabaseRestrictionLeafCondition,
    DatabaseRestrictionLogicalCondition as GraphqlDatabaseRestrictionLogicalCondition,
    DatabaseRestrictionLogicalConditionOperator as GraphqlDatabaseRestrictionLogicalConditionOperator,
    DatabaseRestrictionMembershipCondition as GraphqlDatabaseRestrictionMembershipCondition,
    DatabaseRestrictionMembershipConditionOperator as GraphqlDatabaseRestrictionMembershipConditionOperator,
    DatabaseRestrictionRelationalCondition as GraphqlDatabaseRestrictionRelationalCondition,
    DatabaseRestrictionRelationalConditionOperator as GraphqlDatabaseRestrictionRelationalConditionOperator,
)
from .._identification import ColumnIdentifier
from .._operation import (
    LogicalCondition,
    MembershipCondition,
    RelationalCondition,
    condition_from_graphql,
    condition_to_graphql,
)

DatabaseRestrictionMembershipConditionOperator: TypeAlias = Literal["IN"]
DatabaseRestrictionRelationalConditionOperator: TypeAlias = Literal["EQ"]
DatabaseRestrictionLeafCondition: TypeAlias = (
    MembershipCondition[
        ColumnIdentifier, DatabaseRestrictionMembershipConditionOperator, ScalarConstant
    ]
    | RelationalCondition[
        ColumnIdentifier, DatabaseRestrictionRelationalConditionOperator, ScalarConstant
    ]
)
DatabaseRestrictionLogicalConditionOperator: TypeAlias = Literal["AND"]
DatabaseRestrictionLogicalCondition: TypeAlias = LogicalCondition[
    DatabaseRestrictionLeafCondition, DatabaseRestrictionLogicalConditionOperator
]
DatabaseRestrictionCondition: TypeAlias = (
    DatabaseRestrictionLeafCondition | DatabaseRestrictionLogicalCondition
)


def database_restriction_condition_from_graphql(
    condition: GraphqlDatabaseRestrictionCondition, /
) -> DatabaseRestrictionCondition:
    return condition_from_graphql(
        condition,
        convert_leaf_condition_subject=ColumnIdentifier._from_graphql,
        convert_membership_condition_operator=lambda operator: operator.value,
        convert_membership_condition_element=lambda element: element,
        convert_relational_condition_operator=lambda operator: operator.value,
        convert_relational_condition_target=lambda target: target,
        convert_logical_condition_operator=lambda operator: operator.value,
    )


def database_restriction_condition_to_graphql(
    condition: DatabaseRestrictionCondition, /
) -> GraphqlDatabaseRestrictionCondition:
    return condition_to_graphql(  # type: ignore[no-any-return]
        condition,
        convert_leaf_condition_subject=lambda subject: subject._to_graphql(),
        membership_condition_class=GraphqlDatabaseRestrictionMembershipCondition,
        membership_condition_operator_class=GraphqlDatabaseRestrictionMembershipConditionOperator,
        convert_membership_condition_element=lambda element: element,
        relational_condition_class=GraphqlDatabaseRestrictionRelationalCondition,
        relational_condition_operator_class=GraphqlDatabaseRestrictionRelationalConditionOperator,
        convert_relational_condition_target=lambda target: target,
        leaf_condition_class=GraphqlDatabaseRestrictionLeafCondition,
        logical_condition_class=GraphqlDatabaseRestrictionLogicalCondition,
        logical_condition_operator_class=GraphqlDatabaseRestrictionLogicalConditionOperator,
        condition_class=GraphqlDatabaseRestrictionCondition,
    )
