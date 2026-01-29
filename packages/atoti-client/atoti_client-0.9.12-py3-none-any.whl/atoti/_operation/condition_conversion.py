from collections.abc import Callable
from typing import Generic, Protocol, TypeVar

from .._graphql import (
    Condition as GraphqlCondition,
    LeafCondition as GraphqlLeafCondition,
    LeafConditionSubjectT as GraphqlLeafConditionSubjectT,
    LogicalCondition as GraphqlLogicalCondition,
    LogicalConditionOperatorT as GraphqlLogicalConditionOperatorT,
    MembershipCondition as GraphqlMembershipCondition,
    MembershipConditionElementT as GraphqlMembershipConditionElementT,
    MembershipConditionOperatorT as GraphqlMembershipConditionOperatorT,
    RelationalCondition as GraphqlRelationalCondition,
    RelationalConditionOperatorT as GraphqlRelationalConditionOperatorT,
    RelationalConditionTargetT as GraphqlRelationalConditionTargetT,
)
from .operation import (
    LogicalCondition,
    LogicalConditionOperatorT_co,
    MembershipCondition,
    MembershipConditionElementT_co,
    MembershipConditionOperatorT_co,
    MembershipConditionSubjectT_co,
    RelationalCondition,
    RelationalConditionOperatorT_co,
    RelationalConditionTargetT_co,
)


def _membership_condition_from_graphql(
    condition: GraphqlMembershipCondition[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [GraphqlLeafConditionSubjectT], MembershipConditionSubjectT_co
    ],
    convert_membership_condition_operator: Callable[
        [GraphqlMembershipConditionOperatorT], MembershipConditionOperatorT_co
    ],
    convert_membership_condition_element: Callable[
        [GraphqlMembershipConditionElementT], MembershipConditionElementT_co
    ],
) -> MembershipCondition[
    MembershipConditionSubjectT_co,
    MembershipConditionOperatorT_co,
    MembershipConditionElementT_co,
]:
    subject = convert_leaf_condition_subject(condition.subject)
    operator = convert_membership_condition_operator(condition.operator)
    elements = frozenset(
        convert_membership_condition_element(element) for element in condition.elements
    )
    return MembershipCondition(subject=subject, operator=operator, elements=elements)


def _relational_condition_from_graphql(
    condition: GraphqlRelationalCondition[
        GraphqlLeafConditionSubjectT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [GraphqlLeafConditionSubjectT], MembershipConditionSubjectT_co
    ],
    convert_relational_condition_operator: Callable[
        [GraphqlRelationalConditionOperatorT], RelationalConditionOperatorT_co
    ],
    convert_relational_condition_target: Callable[
        [GraphqlRelationalConditionTargetT], RelationalConditionTargetT_co
    ],
) -> RelationalCondition[
    MembershipConditionSubjectT_co,
    RelationalConditionOperatorT_co,
    RelationalConditionTargetT_co,
]:
    subject = convert_leaf_condition_subject(condition.subject)
    operator = convert_relational_condition_operator(condition.operator)
    target = convert_relational_condition_target(condition.target)
    return RelationalCondition(subject=subject, operator=operator, target=target)


def _leaf_condition_from_graphql(
    condition: GraphqlLeafCondition[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [GraphqlLeafConditionSubjectT], MembershipConditionSubjectT_co
    ],
    convert_membership_condition_operator: Callable[
        [GraphqlMembershipConditionOperatorT], MembershipConditionOperatorT_co
    ],
    convert_membership_condition_element: Callable[
        [GraphqlMembershipConditionElementT], MembershipConditionElementT_co
    ],
    convert_relational_condition_operator: Callable[
        [GraphqlRelationalConditionOperatorT], RelationalConditionOperatorT_co
    ],
    convert_relational_condition_target: Callable[
        [GraphqlRelationalConditionTargetT], RelationalConditionTargetT_co
    ],
) -> (
    MembershipCondition[
        MembershipConditionSubjectT_co,
        MembershipConditionOperatorT_co,
        MembershipConditionElementT_co,
    ]
    | RelationalCondition[
        MembershipConditionSubjectT_co,
        RelationalConditionOperatorT_co,
        RelationalConditionTargetT_co,
    ]
):
    if condition.membership is not None:
        return _membership_condition_from_graphql(
            condition.membership,
            convert_leaf_condition_subject=convert_leaf_condition_subject,
            convert_membership_condition_operator=convert_membership_condition_operator,
            convert_membership_condition_element=convert_membership_condition_element,
        )

    if (
        condition.relational is not None
    ):  # pragma: no branch (ariadna-codegen does not generate a union for `oneOf` inputs)
        return _relational_condition_from_graphql(
            condition.relational,
            convert_leaf_condition_subject=convert_leaf_condition_subject,
            convert_relational_condition_operator=convert_relational_condition_operator,
            convert_relational_condition_target=convert_relational_condition_target,
        )

    raise ValueError(  # pragma: no cover (ariadna-codegen does not generate a union for `oneOf` inputs)
        f"Unexpected condition: {condition}."
    )


def _logical_condition_from_graphql(
    condition: GraphqlLogicalCondition[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
        GraphqlLogicalConditionOperatorT,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [GraphqlLeafConditionSubjectT], MembershipConditionSubjectT_co
    ],
    convert_membership_condition_operator: Callable[
        [GraphqlMembershipConditionOperatorT], MembershipConditionOperatorT_co
    ],
    convert_membership_condition_element: Callable[
        [GraphqlMembershipConditionElementT], MembershipConditionElementT_co
    ],
    convert_relational_condition_operator: Callable[
        [GraphqlRelationalConditionOperatorT], RelationalConditionOperatorT_co
    ],
    convert_relational_condition_target: Callable[
        [GraphqlRelationalConditionTargetT], RelationalConditionTargetT_co
    ],
    convert_logical_condition_operator: Callable[
        [GraphqlLogicalConditionOperatorT], LogicalConditionOperatorT_co
    ],
) -> LogicalCondition[
    MembershipCondition[
        MembershipConditionSubjectT_co,
        MembershipConditionOperatorT_co,
        MembershipConditionElementT_co,
    ]
    | RelationalCondition[
        MembershipConditionSubjectT_co,
        RelationalConditionOperatorT_co,
        RelationalConditionTargetT_co,
    ],
    LogicalConditionOperatorT_co,
]:
    operands = tuple(
        condition_from_graphql(
            operand,
            convert_leaf_condition_subject=convert_leaf_condition_subject,
            convert_membership_condition_operator=convert_membership_condition_operator,
            convert_membership_condition_element=convert_membership_condition_element,
            convert_relational_condition_operator=convert_relational_condition_operator,
            convert_relational_condition_target=convert_relational_condition_target,
            convert_logical_condition_operator=convert_logical_condition_operator,
        )
        for operand in condition.operands
    )
    operator = convert_logical_condition_operator(condition.operator)
    return LogicalCondition(operands=operands, operator=operator)


def condition_from_graphql(
    condition: GraphqlCondition[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
        GraphqlLogicalConditionOperatorT,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [GraphqlLeafConditionSubjectT], MembershipConditionSubjectT_co
    ],
    convert_membership_condition_operator: Callable[
        [GraphqlMembershipConditionOperatorT], MembershipConditionOperatorT_co
    ],
    convert_membership_condition_element: Callable[
        [GraphqlMembershipConditionElementT], MembershipConditionElementT_co
    ],
    convert_relational_condition_operator: Callable[
        [GraphqlRelationalConditionOperatorT], RelationalConditionOperatorT_co
    ],
    convert_relational_condition_target: Callable[
        [GraphqlRelationalConditionTargetT], RelationalConditionTargetT_co
    ],
    convert_logical_condition_operator: Callable[
        [GraphqlLogicalConditionOperatorT], LogicalConditionOperatorT_co
    ],
) -> (
    MembershipCondition[
        MembershipConditionSubjectT_co,
        MembershipConditionOperatorT_co,
        MembershipConditionElementT_co,
    ]
    | RelationalCondition[
        MembershipConditionSubjectT_co,
        RelationalConditionOperatorT_co,
        RelationalConditionTargetT_co,
    ]
    | LogicalCondition[
        MembershipCondition[
            MembershipConditionSubjectT_co,
            MembershipConditionOperatorT_co,
            MembershipConditionElementT_co,
        ]
        | RelationalCondition[
            MembershipConditionSubjectT_co,
            RelationalConditionOperatorT_co,
            RelationalConditionTargetT_co,
        ],
        LogicalConditionOperatorT_co,
    ]
):
    if condition.leaf is not None:
        return _leaf_condition_from_graphql(
            condition.leaf,
            convert_leaf_condition_subject=convert_leaf_condition_subject,
            convert_membership_condition_operator=convert_membership_condition_operator,
            convert_membership_condition_element=convert_membership_condition_element,
            convert_relational_condition_operator=convert_relational_condition_operator,
            convert_relational_condition_target=convert_relational_condition_target,
        )

    if (
        condition.logical is not None
    ):  # pragma: no branch (ariadna-codegen does not generate a union for `oneOf` inputs)
        return _logical_condition_from_graphql(
            condition.logical,
            convert_leaf_condition_subject=convert_leaf_condition_subject,
            convert_membership_condition_operator=convert_membership_condition_operator,
            convert_membership_condition_element=convert_membership_condition_element,
            convert_relational_condition_operator=convert_relational_condition_operator,
            convert_relational_condition_target=convert_relational_condition_target,
            convert_logical_condition_operator=convert_logical_condition_operator,
        )

    raise ValueError(  # pragma: no cover (ariadna-codegen does not generate a union for `oneOf` inputs)
        f"Unexpected condition: {condition}."
    )


_GraphqlMembershipConditionT = TypeVar("_GraphqlMembershipConditionT")


class _GraphqlMembershipConditionClass(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
        _GraphqlMembershipConditionT,
    ],
    Protocol,
):
    def __call__(
        self,
        *,
        subject: GraphqlLeafConditionSubjectT,
        operator: GraphqlMembershipConditionOperatorT,
        elements: list[GraphqlMembershipConditionElementT],
    ) -> _GraphqlMembershipConditionT: ...


class _GraphqlMembershipOperatorClass(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[MembershipConditionOperatorT_co, GraphqlMembershipConditionOperatorT],
    Protocol,
):
    def __getitem__(
        self,
        key: MembershipConditionOperatorT_co,  # type: ignore[misc] # pyright: ignore[reportGeneralTypeIssues]
        /,
    ) -> GraphqlMembershipConditionOperatorT: ...


def _membership_condition_to_graphql(
    condition: MembershipCondition[
        MembershipConditionSubjectT_co,
        MembershipConditionOperatorT_co,
        MembershipConditionElementT_co,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [MembershipConditionSubjectT_co], GraphqlLeafConditionSubjectT
    ],
    membership_condition_class: _GraphqlMembershipConditionClass[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
        _GraphqlMembershipConditionT,
    ],
    membership_condition_operator_class: _GraphqlMembershipOperatorClass[
        MembershipConditionOperatorT_co, GraphqlMembershipConditionOperatorT
    ],
    convert_membership_condition_element: Callable[
        [MembershipConditionElementT_co], GraphqlMembershipConditionElementT
    ],
) -> _GraphqlMembershipConditionT:
    subject = convert_leaf_condition_subject(condition.subject)
    operator = membership_condition_operator_class[condition.operator]
    _elements: list[GraphqlMembershipConditionElementT] = [
        convert_membership_condition_element(element) for element in condition.elements
    ]
    elements = sorted(_elements)  # type: ignore[type-var] # pyright: ignore[reportArgumentType]
    return membership_condition_class(
        subject=subject, operator=operator, elements=elements
    )


_GraphqlRelationalConditionT = TypeVar("_GraphqlRelationalConditionT")


class _GraphqlRelationalConditionClass(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[
        GraphqlLeafConditionSubjectT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
        _GraphqlRelationalConditionT,
    ],
    Protocol,
):
    def __call__(
        self,
        *,
        subject: GraphqlLeafConditionSubjectT,
        operator: GraphqlRelationalConditionOperatorT,
        target: GraphqlRelationalConditionTargetT,
    ) -> _GraphqlRelationalConditionT: ...


class _GraphqlRelationalOperatorClass(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[RelationalConditionOperatorT_co, GraphqlRelationalConditionOperatorT],
    Protocol,
):
    def __getitem__(
        self,
        key: RelationalConditionOperatorT_co,  # type: ignore[misc] # pyright: ignore[reportGeneralTypeIssues]
        /,
    ) -> GraphqlRelationalConditionOperatorT: ...


def _relational_condition_to_graphql(
    condition: RelationalCondition[
        MembershipConditionSubjectT_co,
        RelationalConditionOperatorT_co,
        RelationalConditionTargetT_co,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [MembershipConditionSubjectT_co], GraphqlLeafConditionSubjectT
    ],
    relational_condition_class: _GraphqlRelationalConditionClass[
        GraphqlLeafConditionSubjectT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
        _GraphqlRelationalConditionT,
    ],
    relational_condition_operator_class: _GraphqlRelationalOperatorClass[
        RelationalConditionOperatorT_co, GraphqlRelationalConditionOperatorT
    ],
    convert_relational_condition_target: Callable[
        [RelationalConditionTargetT_co], GraphqlRelationalConditionTargetT
    ],
) -> _GraphqlRelationalConditionT:
    subject = convert_leaf_condition_subject(condition.subject)
    operator = relational_condition_operator_class[condition.operator]
    target = convert_relational_condition_target(condition.target)
    return relational_condition_class(subject=subject, operator=operator, target=target)


_GraphqlLeafConditionT = TypeVar("_GraphqlLeafConditionT")


class _GraphqlLeafConditionClass(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[
        _GraphqlMembershipConditionT,
        _GraphqlRelationalConditionT,
        _GraphqlLeafConditionT,
    ],
    Protocol,
):
    def __call__(
        self,
        *,
        membership: _GraphqlMembershipConditionT | None = None,
        relational: _GraphqlRelationalConditionT | None = None,
    ) -> _GraphqlLeafConditionT: ...


def _leaf_condition_to_graphql(
    condition: MembershipCondition[
        MembershipConditionSubjectT_co,
        MembershipConditionOperatorT_co,
        MembershipConditionElementT_co,
    ]
    | RelationalCondition[
        MembershipConditionSubjectT_co,
        RelationalConditionOperatorT_co,
        RelationalConditionTargetT_co,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [MembershipConditionSubjectT_co], GraphqlLeafConditionSubjectT
    ],
    membership_condition_class: _GraphqlMembershipConditionClass[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
        _GraphqlMembershipConditionT,
    ],
    membership_condition_operator_class: _GraphqlMembershipOperatorClass[
        MembershipConditionOperatorT_co, GraphqlMembershipConditionOperatorT
    ],
    convert_membership_condition_element: Callable[
        [MembershipConditionElementT_co], GraphqlMembershipConditionElementT
    ],
    relational_condition_class: _GraphqlRelationalConditionClass[
        GraphqlLeafConditionSubjectT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
        _GraphqlRelationalConditionT,
    ],
    relational_condition_operator_class: _GraphqlRelationalOperatorClass[
        RelationalConditionOperatorT_co, GraphqlRelationalConditionOperatorT
    ],
    convert_relational_condition_target: Callable[
        [RelationalConditionTargetT_co], GraphqlRelationalConditionTargetT
    ],
    leaf_condition_class: _GraphqlLeafConditionClass[
        _GraphqlMembershipConditionT,
        _GraphqlRelationalConditionT,
        _GraphqlLeafConditionT,
    ],
) -> _GraphqlLeafConditionT:
    match condition:
        case MembershipCondition():
            membership_condition = _membership_condition_to_graphql(
                condition,
                convert_leaf_condition_subject=convert_leaf_condition_subject,
                membership_condition_class=membership_condition_class,
                membership_condition_operator_class=membership_condition_operator_class,
                convert_membership_condition_element=convert_membership_condition_element,
            )
            return leaf_condition_class(membership=membership_condition)
        case RelationalCondition():  # pragma: no branch (avoid `case _` to detect new variants)
            relational_condition = _relational_condition_to_graphql(
                condition,
                convert_leaf_condition_subject=convert_leaf_condition_subject,
                relational_condition_class=relational_condition_class,
                relational_condition_operator_class=relational_condition_operator_class,
                convert_relational_condition_target=convert_relational_condition_target,
            )
            return leaf_condition_class(relational=relational_condition)


_GraphqlLogicalConditionT = TypeVar("_GraphqlLogicalConditionT")
_GraphqlConditionT = TypeVar("_GraphqlConditionT")


class _GraphqlLogicalConditionClass(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[
        _GraphqlConditionT,
        GraphqlLogicalConditionOperatorT,
        _GraphqlLogicalConditionT,
    ],
    Protocol,
):
    def __call__(
        self,
        *,
        operands: list[_GraphqlConditionT],
        operator: GraphqlLogicalConditionOperatorT,
    ) -> _GraphqlLogicalConditionT: ...


class _GraphqlLogicalOperatorClass(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[LogicalConditionOperatorT_co, GraphqlLogicalConditionOperatorT],
    Protocol,
):
    def __getitem__(
        self,
        key: LogicalConditionOperatorT_co,  # type: ignore[misc] # pyright: ignore[reportGeneralTypeIssues]
        /,
    ) -> GraphqlLogicalConditionOperatorT: ...


class _GraphqlConditionClass(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[
        _GraphqlLeafConditionT,
        _GraphqlLogicalConditionT,
        _GraphqlConditionT,
    ],
    Protocol,
):
    def __call__(
        self,
        *,
        leaf: _GraphqlLeafConditionT | None = None,
        logical: _GraphqlLogicalConditionT | None = None,
    ) -> _GraphqlConditionT: ...


def _logical_condition_to_graphql(
    condition: LogicalCondition[
        MembershipCondition[
            MembershipConditionSubjectT_co,
            MembershipConditionOperatorT_co,
            MembershipConditionElementT_co,
        ]
        | RelationalCondition[
            MembershipConditionSubjectT_co,
            RelationalConditionOperatorT_co,
            RelationalConditionTargetT_co,
        ],
        LogicalConditionOperatorT_co,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [MembershipConditionSubjectT_co], GraphqlLeafConditionSubjectT
    ],
    membership_condition_class: _GraphqlMembershipConditionClass[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
        _GraphqlMembershipConditionT,
    ],
    membership_condition_operator_class: _GraphqlMembershipOperatorClass[
        MembershipConditionOperatorT_co, GraphqlMembershipConditionOperatorT
    ],
    convert_membership_condition_element: Callable[
        [MembershipConditionElementT_co], GraphqlMembershipConditionElementT
    ],
    relational_condition_class: _GraphqlRelationalConditionClass[
        GraphqlLeafConditionSubjectT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
        _GraphqlRelationalConditionT,
    ],
    relational_condition_operator_class: _GraphqlRelationalOperatorClass[
        RelationalConditionOperatorT_co, GraphqlRelationalConditionOperatorT
    ],
    convert_relational_condition_target: Callable[
        [RelationalConditionTargetT_co], GraphqlRelationalConditionTargetT
    ],
    leaf_condition_class: _GraphqlLeafConditionClass[
        _GraphqlMembershipConditionT,
        _GraphqlRelationalConditionT,
        _GraphqlLeafConditionT,
    ],
    logical_condition_class: _GraphqlLogicalConditionClass[
        _GraphqlConditionT,
        GraphqlLogicalConditionOperatorT,
        _GraphqlLogicalConditionT,
    ],
    logical_condition_operator_class: _GraphqlLogicalOperatorClass[
        LogicalConditionOperatorT_co, GraphqlLogicalConditionOperatorT
    ],
    condition_class: _GraphqlConditionClass[
        _GraphqlLeafConditionT,
        _GraphqlLogicalConditionT,
        _GraphqlConditionT,
    ],
) -> _GraphqlLogicalConditionT:
    operands = [
        condition_to_graphql(
            operand,
            convert_leaf_condition_subject=convert_leaf_condition_subject,
            membership_condition_class=membership_condition_class,
            membership_condition_operator_class=membership_condition_operator_class,
            convert_membership_condition_element=convert_membership_condition_element,
            relational_condition_class=relational_condition_class,
            relational_condition_operator_class=relational_condition_operator_class,
            convert_relational_condition_target=convert_relational_condition_target,
            leaf_condition_class=leaf_condition_class,
            logical_condition_class=logical_condition_class,
            logical_condition_operator_class=logical_condition_operator_class,
            condition_class=condition_class,
        )
        for operand in condition.operands
    ]
    operator = logical_condition_operator_class[condition.operator]
    return logical_condition_class(operands=operands, operator=operator)


def condition_to_graphql(
    condition: MembershipCondition[
        MembershipConditionSubjectT_co,
        MembershipConditionOperatorT_co,
        MembershipConditionElementT_co,
    ]
    | RelationalCondition[
        MembershipConditionSubjectT_co,
        RelationalConditionOperatorT_co,
        RelationalConditionTargetT_co,
    ]
    | LogicalCondition[
        MembershipCondition[
            MembershipConditionSubjectT_co,
            MembershipConditionOperatorT_co,
            MembershipConditionElementT_co,
        ]
        | RelationalCondition[
            MembershipConditionSubjectT_co,
            RelationalConditionOperatorT_co,
            RelationalConditionTargetT_co,
        ],
        LogicalConditionOperatorT_co,
    ],
    /,
    *,
    convert_leaf_condition_subject: Callable[
        [MembershipConditionSubjectT_co], GraphqlLeafConditionSubjectT
    ],
    membership_condition_class: _GraphqlMembershipConditionClass[
        GraphqlLeafConditionSubjectT,
        GraphqlMembershipConditionOperatorT,
        GraphqlMembershipConditionElementT,
        _GraphqlMembershipConditionT,
    ],
    membership_condition_operator_class: _GraphqlMembershipOperatorClass[
        MembershipConditionOperatorT_co, GraphqlMembershipConditionOperatorT
    ],
    convert_membership_condition_element: Callable[
        [MembershipConditionElementT_co], GraphqlMembershipConditionElementT
    ],
    relational_condition_class: _GraphqlRelationalConditionClass[
        GraphqlLeafConditionSubjectT,
        GraphqlRelationalConditionOperatorT,
        GraphqlRelationalConditionTargetT,
        _GraphqlRelationalConditionT,
    ],
    relational_condition_operator_class: _GraphqlRelationalOperatorClass[
        RelationalConditionOperatorT_co, GraphqlRelationalConditionOperatorT
    ],
    convert_relational_condition_target: Callable[
        [RelationalConditionTargetT_co], GraphqlRelationalConditionTargetT
    ],
    leaf_condition_class: _GraphqlLeafConditionClass[
        _GraphqlMembershipConditionT,
        _GraphqlRelationalConditionT,
        _GraphqlLeafConditionT,
    ],
    logical_condition_class: _GraphqlLogicalConditionClass[
        _GraphqlConditionT,
        GraphqlLogicalConditionOperatorT,
        _GraphqlLogicalConditionT,
    ],
    logical_condition_operator_class: _GraphqlLogicalOperatorClass[
        LogicalConditionOperatorT_co, GraphqlLogicalConditionOperatorT
    ],
    condition_class: _GraphqlConditionClass[
        _GraphqlLeafConditionT,
        _GraphqlLogicalConditionT,
        _GraphqlConditionT,
    ],
) -> _GraphqlConditionT:
    match condition:
        case LogicalCondition():
            logical_condition = _logical_condition_to_graphql(
                condition,
                convert_leaf_condition_subject=convert_leaf_condition_subject,
                membership_condition_class=membership_condition_class,
                membership_condition_operator_class=membership_condition_operator_class,
                convert_membership_condition_element=convert_membership_condition_element,
                relational_condition_class=relational_condition_class,
                relational_condition_operator_class=relational_condition_operator_class,
                convert_relational_condition_target=convert_relational_condition_target,
                leaf_condition_class=leaf_condition_class,
                logical_condition_class=logical_condition_class,
                logical_condition_operator_class=logical_condition_operator_class,
                condition_class=condition_class,
            )
            return condition_class(logical=logical_condition)
        case _:
            leaf_condition = _leaf_condition_to_graphql(
                condition,
                convert_leaf_condition_subject=convert_leaf_condition_subject,
                membership_condition_class=membership_condition_class,
                membership_condition_operator_class=membership_condition_operator_class,
                convert_membership_condition_element=convert_membership_condition_element,
                relational_condition_class=relational_condition_class,
                relational_condition_operator_class=relational_condition_operator_class,
                convert_relational_condition_target=convert_relational_condition_target,
                leaf_condition_class=leaf_condition_class,
            )
            return condition_class(leaf=leaf_condition)
