from __future__ import annotations

from abc import ABC
from typing import Literal, final, overload

from typing_extensions import override

from .._constant import ConstantT_co
from .._identification import HasIdentifier, IdentifierT_co
from ._other_identifier import OtherIdentifierT_co
from .operation import (
    OperandConvertible,
    Operation,
    RelationalCondition,
    convert_to_operand,
)


class OperandConvertibleWithIdentifier(
    OperandConvertible[IdentifierT_co],
    HasIdentifier[IdentifierT_co],
    ABC,
):
    """This class overrides `OperandConvertible`'s `Condition`-creating methods so that the type of the returned `Condition`'s `subject` is narrowed down to an instance of `Identifier` instead of `Identifier | Operation`.

    The returned `Condition`'s `target` is also kept as narrow as possible thanks to `@overload`s.
    """

    @override
    # Without this, the classes inheriting from this class are considered unhashable.
    def __hash__(self) -> int:
        return super().__hash__()

    @override
    def isnull(
        self,
    ) -> RelationalCondition[IdentifierT_co, Literal["EQ"], None]:
        return RelationalCondition(
            subject=self._operation_operand, operator="EQ", target=None
        )

    @property
    @override
    def _operation_operand(self) -> IdentifierT_co:  # pragma: no cover (missing tests)
        return self._identifier

    # The signature is not compatible with `object.__eq__()` on purpose.
    @overload  # type: ignore[override]
    def __eq__(
        self,
        other: ConstantT_co,  # type: ignore[misc]
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["EQ"], ConstantT_co]: ...

    @overload
    def __eq__(
        self,
        other: HasIdentifier[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["EQ"], OtherIdentifierT_co]: ...

    @overload
    def __eq__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[  # pragma: no cover
        IdentifierT_co,
        Literal["EQ"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]: ...

    @final
    @override
    # The signature is not compatible with `object.__eq__()` on purpose.
    def __eq__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[
        IdentifierT_co,
        Literal["EQ"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]:
        assert other is not None, "Use `isnull()` instead."
        return RelationalCondition(
            subject=self._operation_operand,
            operator="EQ",
            target=convert_to_operand(other),
        )

    @overload
    def __ge__(
        self,
        other: ConstantT_co,  # type: ignore[misc]
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["GE"], ConstantT_co]: ...

    @overload
    def __ge__(
        self,
        other: HasIdentifier[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["GE"], OtherIdentifierT_co]: ...

    @overload
    def __ge__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[  # pragma: no cover
        IdentifierT_co,
        Literal["GE"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]: ...

    @override
    def __ge__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[
        IdentifierT_co,
        Literal["GE"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]:
        return RelationalCondition(
            subject=self._operation_operand,
            operator="GE",
            target=convert_to_operand(other),
        )

    @overload
    def __gt__(
        self,
        other: ConstantT_co,  # type: ignore[misc]
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["GT"], ConstantT_co]: ...

    @overload
    def __gt__(
        self,
        other: HasIdentifier[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["GT"], OtherIdentifierT_co]: ...

    @overload
    def __gt__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[  # pragma: no cover
        IdentifierT_co,
        Literal["GT"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]: ...

    @final
    @override
    def __gt__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[
        IdentifierT_co,
        Literal["GT"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]:
        return RelationalCondition(
            subject=self._operation_operand,
            operator="GT",
            target=convert_to_operand(other),
        )

    @overload
    def __le__(
        self,
        other: ConstantT_co,  # type: ignore[misc]
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["LE"], ConstantT_co]: ...

    @overload
    def __le__(
        self,
        other: HasIdentifier[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["LE"], OtherIdentifierT_co]: ...

    @overload
    def __le__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[  # pragma: no cover
        IdentifierT_co,
        Literal["LE"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]: ...

    @final
    @override
    def __le__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[
        IdentifierT_co,
        Literal["LE"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]:
        return RelationalCondition(
            subject=self._operation_operand,
            operator="LE",
            target=convert_to_operand(other),
        )

    @overload
    def __lt__(
        self,
        other: ConstantT_co,  # type: ignore[misc]
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["LT"], ConstantT_co]: ...

    @overload
    def __lt__(
        self,
        other: HasIdentifier[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["LT"], OtherIdentifierT_co]: ...

    @overload
    def __lt__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[  # pragma: no cover
        IdentifierT_co,
        Literal["LT"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]: ...

    @final
    @override
    def __lt__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[
        IdentifierT_co,
        Literal["LT"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]:
        return RelationalCondition(
            subject=self._operation_operand,
            operator="LT",
            target=convert_to_operand(other),
        )

    # The signature is not compatible with `object.__ne__()` on purpose.
    @overload  # type: ignore[override]
    def __ne__(
        self,
        other: ConstantT_co,  # type: ignore[misc]
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["NE"], ConstantT_co]: ...

    @overload
    def __ne__(
        self,
        other: HasIdentifier[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[IdentifierT_co, Literal["NE"], OtherIdentifierT_co]: ...

    @overload
    def __ne__(
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[  # pragma: no cover
        IdentifierT_co,
        Literal["NE"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]: ...

    @final
    @override
    # The signature is not compatible with `object.__ne__()` on purpose.
    def __ne__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        other: ConstantT_co
        | HasIdentifier[OtherIdentifierT_co]
        | Operation[OtherIdentifierT_co],
        /,
    ) -> RelationalCondition[
        IdentifierT_co,
        Literal["NE"],
        ConstantT_co | OtherIdentifierT_co | Operation[OtherIdentifierT_co],
    ]:
        assert other is not None, "Use `~isnull()` instead."
        return RelationalCondition(
            subject=self._operation_operand,
            operator="NE",
            target=convert_to_operand(other),
        )
