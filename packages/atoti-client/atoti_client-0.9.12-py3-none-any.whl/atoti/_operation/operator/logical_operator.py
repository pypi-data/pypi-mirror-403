from typing import Literal, TypeAlias

from typing_extensions import overload

LogicalOperator: TypeAlias = Literal["AND", "OR"]
"""See https://en.wikipedia.org/wiki/Logical_connective."""


def get_logical_symbol(operator: LogicalOperator, /) -> str:
    match operator:
        case "AND":
            return "&"
        case "OR":  # pragma: no branch (avoid `case _` to detect new variants)
            return "|"


@overload
def invert_logical_operator(operator: Literal["AND"], /) -> Literal["OR"]: ...
@overload
def invert_logical_operator(operator: Literal["OR"], /) -> Literal["AND"]: ...
@overload
def invert_logical_operator(operator: LogicalOperator, /) -> LogicalOperator: ...
def invert_logical_operator(operator: LogicalOperator, /) -> LogicalOperator:
    match operator:
        case "AND":
            return "OR"
        case "OR":  # pragma: no branch (avoid `case _` to detect new variants)
            return "AND"
