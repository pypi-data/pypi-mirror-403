from __future__ import annotations

from collections.abc import Set as AbstractSet
from typing import Annotated, final
from warnings import warn

from pydantic import Field
from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .._deprecated_warning_category import (
    DEPRECATED_WARNING_CATEGORY as _DEPRECATED_WARNING_CATEGORY,
)
from .._graphql import AggregateProviderFragment, CreateAggregateProviderInput
from .._identification import (
    CubeIdentifier,
    Identifiable,
    LevelIdentifier,
    MeasureIdentifier,
    identify,
)
from .._pydantic import PYDANTIC_CONFIG as _PYDANTIC_CONFIG
from .._validate_hierarchy_unicity import validate_hierarchy_unicity
from ._aggregate_provider_filter import (
    AggregateProviderFilterCondition,
    aggregate_provider_filter_condition_from_graphql,
    aggregate_provider_filter_condition_to_graphql,
)
from ._aggregate_provider_plugin_key import (
    AggregateProviderPluginKey,
    plugin_key_from_graphql,
    plugin_key_to_graphql,
)


@final
@dataclass(config=_PYDANTIC_CONFIG, frozen=True, kw_only=True)
class AggregateProvider:
    """An aggregate provider pre-aggregates some measures up to certain levels.

    If a step of a query uses a subset of the aggregate provider's levels and measures, the provider will speed up the query.

    An aggregate provider uses additional memory to store the intermediate aggregates.
    The more levels and measures are added, the more memory it requires.

    Example:
        .. doctest::
            :hide:

            >>> session = getfixture("default_session")

        >>> df = pd.DataFrame(
        ...     {
        ...         "Seller": ["Seller_1", "Seller_1", "Seller_2", "Seller_2"],
        ...         "ProductId": ["aBk3", "ceJ4", "aBk3", "ceJ4"],
        ...         "Price": [2.5, 49.99, 3.0, 54.99],
        ...     }
        ... )
        >>> table = session.read_pandas(df, table_name="Seller")
        >>> cube = session.create_cube(table)
        >>> l, m = cube.levels, cube.measures
        >>> cube.aggregate_providers["Seller"] = tt.AggregateProvider(
        ...     filter=l["Seller"] == "Seller_1",
        ...     key="bitmap",
        ...     levels={l["Seller"]},
        ...     measures={m["Price.SUM"]},
        ...     partitioning="modulo4(Seller)",
        ... )
        >>> cube.aggregate_providers
        {'Seller': AggregateProvider(filter=l['Seller', 'Seller', 'Seller'] == 'Seller_1', key='bitmap', levels=frozenset({l['Seller', 'Seller', 'Seller']}), measures=frozenset({m['Price.SUM']}), partitioning='modulo4(Seller)')}

        Pre-aggregating all measures:

        >>> from dataclasses import replace
        >>> cube.aggregate_providers["Seller"] = replace(
        ...     cube.aggregate_providers["Seller"],
        ...     measures=None,
        ... )
        >>> cube.aggregate_providers["Seller"]
        AggregateProvider(filter=l['Seller', 'Seller', 'Seller'] == 'Seller_1', key='bitmap', levels=frozenset({l['Seller', 'Seller', 'Seller']}), measures=None, partitioning='modulo4(Seller)')

    """

    filter: AggregateProviderFilterCondition | None = None
    """Only compute and provide aggregates matching this condition."""

    key: AggregateProviderPluginKey = "leaf"
    """The key of the provider.

    The bitmap is generally faster but also takes more memory.
    """

    levels: (
        Annotated[
            AbstractSet[Identifiable[LevelIdentifier]],
            Field(min_length=1),
            # Uncomment in the next breaking release.
            # AfterValidator(validate_hierarchy_unicity),
        ]
        | None
    ) = None
    """The levels to build the provider on.

    If a passed level is part of a multilevel hierarchy, all shallower levels will be pre-aggregated too.
    If ``None``, all eligible levels will be pre-aggregated.
    """

    measures: (
        Annotated[
            AbstractSet[Identifiable[MeasureIdentifier]],
            Field(min_length=1),
        ]
        | None
    ) = None
    """The measures to build the provider on.

    If ``None``, all eligible measures will be pre-aggregated.

    .. note::
        This collection cannot contain any measure created from a column in a :meth:`partially joined <atoti.Table.join>` table.
    """

    partitioning: str | None = None
    """The partitioning of the provider.

    Default to the partitioning of the cube's fact table.
    """

    @classmethod
    def _from_graphql(cls, aggregate_provider: AggregateProviderFragment, /) -> Self:
        return cls(
            filter=None
            if aggregate_provider.filter is None
            else aggregate_provider_filter_condition_from_graphql(
                aggregate_provider.filter.value
            ),
            key=plugin_key_from_graphql(aggregate_provider.plugin_key),
            levels=None
            if aggregate_provider.levels is None
            else {
                LevelIdentifier._from_graphql(level)
                for level in aggregate_provider.levels
            },
            measures=None
            if aggregate_provider.measures is None
            else {
                MeasureIdentifier._from_graphql(measure)
                for measure in aggregate_provider.measures
            },
            partitioning=aggregate_provider.partitioning,
        )

    def __post_init__(self) -> None:
        if self.levels:
            try:
                validate_hierarchy_unicity(self.levels)
            except ValueError as error:  # pragma: no cover (missing tests)
                warn(
                    error.args[0],
                    category=_DEPRECATED_WARNING_CATEGORY,
                    stacklevel=2,
                )

    def _to_create_aggregate_provider_input(
        self, /, *, cube_identifier: CubeIdentifier, name: str
    ) -> CreateAggregateProviderInput:
        graphql_input = CreateAggregateProviderInput(
            aggregate_provider_name=name,
            cube_name=cube_identifier.cube_name,
            plugin_key=plugin_key_to_graphql(self.key),
        )

        if self.filter is not None:
            graphql_input.filter = aggregate_provider_filter_condition_to_graphql(
                self.filter
            )

        if self.levels is not None:
            graphql_input.level_identifiers = [
                identify(level)._to_graphql() for level in self.levels
            ]

        if self.measures is not None:
            graphql_input.measure_names = [
                identify(measure).measure_name for measure in self.measures
            ]

        if self.partitioning is not None:
            graphql_input.partitioning = self.partitioning

        return graphql_input
