from typing import Literal

from typing_extensions import overload

MembershipOperator = Literal["IN", "NOT_IN"]
"""See https://docs.python.org/3/reference/expressions.html#membership-test-operations."""


@overload
def invert_membership_operator(operator: Literal["IN"], /) -> Literal["NOT_IN"]: ...
@overload
def invert_membership_operator(operator: Literal["NOT_IN"], /) -> Literal["IN"]: ...
@overload
def invert_membership_operator(
    operator: MembershipOperator, /
) -> MembershipOperator: ...
def invert_membership_operator(operator: MembershipOperator, /) -> MembershipOperator:
    match operator:
        case "IN":
            return "NOT_IN"
        case "NOT_IN":  # pragma: no branch (avoid `case _` to detect new variants)
            return "IN"
