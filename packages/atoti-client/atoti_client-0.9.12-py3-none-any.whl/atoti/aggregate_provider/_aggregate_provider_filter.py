from __future__ import annotations

from typing import Literal, TypeAlias

from .._constant import ScalarConstant
from .._graphql import (
    AggregateProviderFilterCondition as GraphqlAggregateProviderFilterCondition,
    AggregateProviderFilterLeafCondition as GraphqlAggregateProviderFilterLeafCondition,
    AggregateProviderFilterLogicalCondition as GraphqlAggregateProviderFilterLogicalCondition,
    AggregateProviderFilterLogicalConditionOperator as GraphqlAggregateProviderFilterLogicalConditionOperator,
    AggregateProviderFilterMembershipCondition as GraphqlAggregateProviderFilterMembershipCondition,
    AggregateProviderFilterMembershipConditionOperator as GraphqlAggregateProviderFilterMembershipConditionOperator,
    AggregateProviderFilterRelationalCondition as GraphqlAggregateProviderFilterRelationalCondition,
    AggregateProviderFilterRelationalConditionOperator as GraphqlAggregateProviderFilterRelationalConditionOperator,
)
from .._identification import LevelIdentifier
from .._operation import (
    LogicalCondition,
    MembershipCondition,
    RelationalCondition,
    condition_from_graphql,
    condition_to_graphql,
)

AggregateProviderFilterMembershipConditionOperator: TypeAlias = Literal["IN"]
AggregateProviderFilterRelationalConditionOperator: TypeAlias = Literal["EQ"]
AggregateProviderFilterLeafCondition: TypeAlias = (
    MembershipCondition[
        LevelIdentifier,
        AggregateProviderFilterMembershipConditionOperator,
        ScalarConstant,
    ]
    | RelationalCondition[
        LevelIdentifier,
        AggregateProviderFilterRelationalConditionOperator,
        ScalarConstant,
    ]
)
AggregateProviderFilterLogicalConditionOperator: TypeAlias = Literal["AND"]
AggregateProviderFilterLogicalCondition: TypeAlias = LogicalCondition[
    AggregateProviderFilterLeafCondition,
    AggregateProviderFilterLogicalConditionOperator,
]
AggregateProviderFilterCondition: TypeAlias = (
    AggregateProviderFilterLeafCondition | AggregateProviderFilterLogicalCondition
)


def aggregate_provider_filter_condition_from_graphql(
    condition: GraphqlAggregateProviderFilterCondition, /
) -> AggregateProviderFilterCondition:
    return condition_from_graphql(
        condition,
        convert_leaf_condition_subject=LevelIdentifier._from_graphql,
        convert_membership_condition_operator=lambda operator: operator.value,
        convert_membership_condition_element=lambda element: element,
        convert_relational_condition_operator=lambda operator: operator.value,
        convert_relational_condition_target=lambda target: target,
        convert_logical_condition_operator=lambda operator: operator.value,
    )


def aggregate_provider_filter_condition_to_graphql(
    condition: AggregateProviderFilterCondition, /
) -> GraphqlAggregateProviderFilterCondition:
    return condition_to_graphql(  # type: ignore[no-any-return]
        condition,
        convert_leaf_condition_subject=lambda subject: subject._to_graphql(),
        membership_condition_class=GraphqlAggregateProviderFilterMembershipCondition,
        membership_condition_operator_class=GraphqlAggregateProviderFilterMembershipConditionOperator,
        convert_membership_condition_element=lambda element: element,
        relational_condition_class=GraphqlAggregateProviderFilterRelationalCondition,
        relational_condition_operator_class=GraphqlAggregateProviderFilterRelationalConditionOperator,
        convert_relational_condition_target=lambda target: target,
        leaf_condition_class=GraphqlAggregateProviderFilterLeafCondition,
        logical_condition_class=GraphqlAggregateProviderFilterLogicalCondition,
        logical_condition_operator_class=GraphqlAggregateProviderFilterLogicalConditionOperator,
        condition_class=GraphqlAggregateProviderFilterCondition,
    )
