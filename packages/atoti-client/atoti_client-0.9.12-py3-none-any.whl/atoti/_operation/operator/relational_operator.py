from typing import Literal, TypeAlias

from typing_extensions import overload

EqualityOperator: TypeAlias = Literal["EQ", "NE"]
InequalityOperator: TypeAlias = Literal["GE", "GT", "LE", "LT"]

RelationalOperator: TypeAlias = EqualityOperator | InequalityOperator
"""See https://en.wikipedia.org/wiki/Relational_operator."""


def get_relational_symbol(operator: RelationalOperator, /) -> str:
    match operator:  # pragma: no cover (trivial)
        case "EQ":
            return "=="
        case "NE":
            return "!="
        case "GE":
            return ">="
        case "GT":
            return ">"
        case "LE":
            return "<="
        case "LT":
            return "<"


@overload
def invert_relational_operator(operator: Literal["EQ"], /) -> Literal["NE"]: ...
@overload
def invert_relational_operator(operator: Literal["NE"], /) -> Literal["EQ"]: ...
@overload
def invert_relational_operator(operator: EqualityOperator, /) -> EqualityOperator: ...
@overload
def invert_relational_operator(operator: Literal["GE"], /) -> Literal["LT"]: ...
@overload
def invert_relational_operator(operator: Literal["GT"], /) -> Literal["LE"]: ...
@overload
def invert_relational_operator(operator: Literal["LE"], /) -> Literal["GT"]: ...
@overload
def invert_relational_operator(operator: Literal["LT"], /) -> Literal["GE"]: ...
@overload
def invert_relational_operator(
    operator: InequalityOperator, /
) -> InequalityOperator: ...
@overload
def invert_relational_operator(
    operator: RelationalOperator, /
) -> RelationalOperator: ...
def invert_relational_operator(operator: RelationalOperator, /) -> RelationalOperator:
    match operator:  # pragma: no cover (trivial)
        case "EQ":
            return "NE"
        case "NE":
            return "EQ"
        case "GE":
            return "LT"
        case "GT":
            return "LE"
        case "LE":
            return "GT"
        case "LT":
            return "GE"
