from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Generic, Protocol, TypeVar

LeafConditionSubjectT = TypeVar("LeafConditionSubjectT")
MembershipConditionElementT = TypeVar("MembershipConditionElementT")
RelationalConditionTargetT = TypeVar("RelationalConditionTargetT")
MembershipConditionOperatorT = TypeVar("MembershipConditionOperatorT", bound=Enum)
RelationalConditionOperatorT = TypeVar("RelationalConditionOperatorT", bound=Enum)
LogicalConditionOperatorT = TypeVar("LogicalConditionOperatorT", bound=Enum)


class MembershipCondition(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[
        LeafConditionSubjectT, RelationalConditionOperatorT, MembershipConditionElementT
    ],
    Protocol,
):
    @property
    def subject(self) -> LeafConditionSubjectT: ...

    @property
    def operator(self) -> RelationalConditionOperatorT: ...

    @property
    def elements(self) -> Sequence[MembershipConditionElementT]: ...


class RelationalCondition(  # type: ignore[misc] # pyright: ignore[reportInvalidTypeVarUse]
    Generic[
        LeafConditionSubjectT, RelationalConditionOperatorT, RelationalConditionTargetT
    ],
    Protocol,
):
    @property
    def subject(self) -> LeafConditionSubjectT: ...

    @property
    def operator(self) -> RelationalConditionOperatorT: ...

    @property
    def target(self) -> RelationalConditionTargetT: ...


class LeafCondition(  # type: ignore[misc]
    Generic[
        LeafConditionSubjectT,
        MembershipConditionOperatorT,
        MembershipConditionElementT,
        RelationalConditionOperatorT,
        RelationalConditionTargetT,
    ],
    Protocol,
):
    @property
    def membership(
        self,
    ) -> (
        MembershipCondition[
            LeafConditionSubjectT,
            MembershipConditionOperatorT,
            MembershipConditionElementT,
        ]
        | None
    ): ...

    @property
    def relational(
        self,
    ) -> (
        RelationalCondition[
            LeafConditionSubjectT,
            RelationalConditionOperatorT,
            RelationalConditionTargetT,
        ]
        | None
    ): ...


class LogicalCondition(
    Generic[
        LeafConditionSubjectT,
        MembershipConditionOperatorT,
        MembershipConditionElementT,
        RelationalConditionOperatorT,
        RelationalConditionTargetT,
        LogicalConditionOperatorT,
    ],
    Protocol,
):
    @property
    def operands(
        self,
    ) -> Sequence[
        Condition[
            LeafConditionSubjectT,
            MembershipConditionOperatorT,
            MembershipConditionElementT,
            RelationalConditionOperatorT,
            RelationalConditionTargetT,
            LogicalConditionOperatorT,
        ]
    ]: ...

    @property
    def operator(self) -> LogicalConditionOperatorT: ...


class Condition(
    Generic[
        LeafConditionSubjectT,
        MembershipConditionOperatorT,
        MembershipConditionElementT,
        RelationalConditionOperatorT,
        RelationalConditionTargetT,
        LogicalConditionOperatorT,
    ],
    Protocol,
):
    @property
    def leaf(
        self,
    ) -> (
        LeafCondition[
            LeafConditionSubjectT,
            MembershipConditionOperatorT,
            MembershipConditionElementT,
            RelationalConditionOperatorT,
            RelationalConditionTargetT,
        ]
        | None
    ): ...

    @property
    def logical(
        self,
    ) -> (
        LogicalCondition[
            LeafConditionSubjectT,
            MembershipConditionOperatorT,
            MembershipConditionElementT,
            RelationalConditionOperatorT,
            RelationalConditionTargetT,
            LogicalConditionOperatorT,
        ]
        | None
    ): ...
