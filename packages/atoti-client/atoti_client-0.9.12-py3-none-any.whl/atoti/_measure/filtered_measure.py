from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, final

from typing_extensions import override

from .._constant import ScalarConstant
from .._identification import LevelIdentifier, MeasureIdentifier
from .._measure_definition import MeasureDefinition
from .._operation import (
    HierarchyMembershipCondition,
    LogicalCondition,
    MembershipCondition,
    MembershipOperator,
    RelationalCondition,
    RelationalOperator,
    dnf_from_condition,
)
from .._py4j_client import Py4jClient
from .._py4j_client._utils import to_java_list, to_java_object


@final
@dataclass(eq=False, frozen=True, kw_only=True)
class WhereMeasure(MeasureDefinition):
    """A measure that returns the value of other measures based on conditions."""

    _conditions_to_target_measure: Sequence[tuple[MeasureDefinition, MeasureDefinition]]
    _default_measure: MeasureDefinition | None

    @override
    def _do_distil(
        self,
        identifier: MeasureIdentifier | None = None,
        /,
        *,
        py4j_client: Py4jClient,
        cube_name: str,
    ) -> MeasureIdentifier:
        underlying_default_measure = (
            self._default_measure._distil(
                py4j_client=py4j_client,
                cube_name=cube_name,
            ).measure_name
            if self._default_measure is not None
            else None
        )

        return py4j_client.create_measure(
            identifier,
            "WHERE",
            {
                (
                    condition._distil(
                        py4j_client=py4j_client,
                        cube_name=cube_name,
                    ).measure_name
                ): measure._distil(
                    py4j_client=py4j_client,
                    cube_name=cube_name,
                ).measure_name
                for condition, measure in self._conditions_to_target_measure
            },
            underlying_default_measure,
            cube_name=cube_name,
        )


_FilterLeafCondition = (
    HierarchyMembershipCondition[Literal["IN"], ScalarConstant]
    | MembershipCondition[LevelIdentifier, MembershipOperator, ScalarConstant]
    | RelationalCondition[LevelIdentifier, RelationalOperator, ScalarConstant]
)
FilterCondition = (
    _FilterLeafCondition | LogicalCondition[_FilterLeafCondition, Literal["AND"]]
)


@final
@dataclass(eq=False, frozen=True, kw_only=True)
class LevelValueFilteredMeasure(MeasureDefinition):
    """A measure on a part of the cube filtered on a level value."""

    _underlying_measure: MeasureDefinition
    _filter: FilterCondition

    @override
    def _do_distil(  # noqa: C901
        self,
        identifier: MeasureIdentifier | None = None,
        /,
        *,
        cube_name: str,
        py4j_client: Py4jClient,
    ) -> MeasureIdentifier:
        underlying_name: str = self._underlying_measure._distil(
            py4j_client=py4j_client,
            cube_name=cube_name,
        ).measure_name

        def _process(  # noqa: C901
            leaf_condition: _FilterLeafCondition, /
        ) -> list[dict[str, object]]:
            match leaf_condition:
                case RelationalCondition(
                    subject=subject, operator=operator, target=target
                ):
                    match operator:
                        case "EQ":
                            _operator = "eq"
                        case "NE":
                            _operator = "ne"
                        case "LT":
                            _operator = "lt"
                        case "LE":
                            _operator = "le"
                        case "GT":
                            _operator = "gt"
                        case (
                            "GE"
                        ):  # pragma: no branch (avoid `case _` to detect new variants)
                            _operator = "ge"

                    return [
                        {
                            "level": subject._java_description,
                            "type": "constant",
                            "operation": _operator,
                            "value": to_java_object(
                                target, gateway=py4j_client.gateway
                            ),
                        }
                    ]
                case MembershipCondition(
                    subject=subject,
                    operator=operator,
                    elements=elements,
                ):
                    match operator:
                        case "IN":
                            return [
                                {
                                    "level": subject._java_description,
                                    "type": "constant",
                                    "operation": "li",
                                    "value": to_java_list(
                                        leaf_condition.elements,
                                        gateway=py4j_client.gateway,
                                    ),
                                }
                            ]
                        case (
                            "NOT_IN"
                        ):  # pragma: no branch (avoid `case _` to detect new variants)
                            is_not_in_condition = MembershipCondition(  # type: ignore[var-annotated]
                                subject=subject, operator="NOT_IN", elements=elements
                            )
                            logical_relational_condition = (
                                is_not_in_condition._logical_relational()
                            )
                            is_not_in_condition_dnf: tuple[
                                tuple[
                                    RelationalCondition[
                                        LevelIdentifier,
                                        RelationalOperator,
                                        ScalarConstant,
                                    ],
                                    ...,
                                ]
                            ] = dnf_from_condition(  # type: ignore[assignment]
                                logical_relational_condition
                            )
                            (conjunct_relational_conditions,) = is_not_in_condition_dnf
                            return [
                                condition
                                for relational_condition in conjunct_relational_conditions
                                for condition in _process(relational_condition)
                            ]
                case HierarchyMembershipCondition(
                    subject=subject,
                    operator="IN",  # `NOT_IN` is not supported.
                    member_paths=member_paths,
                    level_names=level_names,
                ):  # pragma: no branch (avoid `case _` to detect new variants)
                    return [
                        {
                            "level": LevelIdentifier(
                                subject, level_names[0]
                            )._java_description,
                            "type": "constant",
                            "operation": "hi",
                            "value": [
                                {
                                    LevelIdentifier(
                                        subject, level_name
                                    )._java_description: member
                                    for level_name, member in zip(
                                        level_names, member_path, strict=False
                                    )
                                }
                                for member_path in member_paths
                            ],
                        }
                    ]

        dnf: tuple[tuple[_FilterLeafCondition, ...]] = dnf_from_condition(self._filter)
        (conjunct_conditions,) = dnf
        conditions: list[dict[str, object]] = [
            condition
            for leaf_condition in conjunct_conditions
            for condition in _process(leaf_condition)
        ]

        # Create the filtered measure and return its name.
        return py4j_client.create_measure(
            identifier,
            "FILTER",
            underlying_name,
            conditions,
            cube_name=cube_name,
        )
