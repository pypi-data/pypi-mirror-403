from collections.abc import Callable, Mapping, Set as AbstractSet
from types import EllipsisType
from typing import Final, final

from typing_extensions import override

from ._cap_http_requests import cap_http_requests
from ._collections import DelegatingConvertingMapping, SupportsUncheckedMappingLookup
from ._cube_definition import CubeDefinition, _CreationMode
from ._cube_discovery import cached_discovery, get_discovery
from ._cube_filter_condition import CubeFilterCondition
from ._get_selection_field_from_column_identifier import (
    get_selection_field_from_column_identifier,
)
from ._graphql import (
    CreateCubeInput,
    CubeFilterCondition as GraphqlCubeFilterCondition,
    CubeFilterLeafCondition as GraphqlCubeFilterLeafCondition,
    CubeFilterLogicalCondition as GraphqlCubeFilterLogicalCondition,
    CubeFilterLogicalConditionOperator as GraphqlCubeFilterLogicalConditionOperator,
    CubeFilterMembershipCondition as GraphqlCubeFilterMembershipCondition,
    CubeFilterMembershipConditionOperator as GraphqlCubeFilterMembershipConditionOperator,
    CubeFilterRelationalCondition as GraphqlCubeFilterRelationalCondition,
    CubeFilterRelationalConditionOperator as GraphqlCubeFilterRelationalConditionOperator,
    DeleteCubeInput,
    HierarchiesCreationMode,
    MeasuresCreationMode,
    create_delete_status_validator,
)
from ._identification import (
    ApplicationName,
    CubeIdentifier,
    CubeName,
    TableIdentifier,
    identify,
)
from ._ipython import ReprJson, ReprJsonable
from ._operation import condition_to_graphql
from ._session_id import SessionId
from .client import Client
from .cube import Cube


def _get_application_name(
    application_name: ApplicationName | EllipsisType | None,
    /,
    *,
    cube_name: str,
) -> ApplicationName | None:
    match application_name:
        case str():
            return application_name
        case EllipsisType():
            return cube_name
        case None:  # pragma: no branch (avoid `case _` to detect new variants)
            return None


def _get_hierarchies_creation_mode(mode: _CreationMode, /) -> HierarchiesCreationMode:
    match mode:
        case "auto":
            return HierarchiesCreationMode.AUTO
        case "manual":  # pragma: no branch (avoid `case _` to detect new variants)
            return HierarchiesCreationMode.MANUAL


def _get_measures_creation_mode(mode: _CreationMode, /) -> MeasuresCreationMode:
    match mode:
        case "auto":
            return MeasuresCreationMode.AUTO
        case "manual":  # pragma: no branch (avoid `case _` to detect new variants)
            return MeasuresCreationMode.MANUAL


def _cube_filter_condition_to_graphql(
    condition: CubeFilterCondition,
    /,
    *,
    client: Client,
    fact_table_identifier: TableIdentifier,
) -> GraphqlCubeFilterCondition:
    return condition_to_graphql(  # type: ignore[no-any-return]
        condition,
        convert_leaf_condition_subject=lambda subject: get_selection_field_from_column_identifier(
            {subject}, client=client, fact_table_identifier=fact_table_identifier
        )[subject]
        ._to_identifier()
        ._to_graphql(),
        membership_condition_class=GraphqlCubeFilterMembershipCondition,
        membership_condition_operator_class=GraphqlCubeFilterMembershipConditionOperator,
        convert_membership_condition_element=lambda element: element,
        relational_condition_class=GraphqlCubeFilterRelationalCondition,
        relational_condition_operator_class=GraphqlCubeFilterRelationalConditionOperator,
        convert_relational_condition_target=lambda target: target,
        leaf_condition_class=GraphqlCubeFilterLeafCondition,
        logical_condition_class=GraphqlCubeFilterLogicalCondition,
        logical_condition_operator_class=GraphqlCubeFilterLogicalConditionOperator,
        condition_class=GraphqlCubeFilterCondition,
    )


def _get_create_cube_input(
    definition: CubeDefinition, /, *, client: Client, identifier: CubeIdentifier
) -> CreateCubeInput:
    graphql_input = CreateCubeInput(
        catalog_names=list(definition.catalog_names),
        cube_name=identifier.cube_name,
        fact_table_name=identify(definition.fact_table).table_name,
        hierarchies=_get_hierarchies_creation_mode(definition.hierarchies),
        measures=_get_measures_creation_mode(definition.measures),
    )

    application_name = _get_application_name(
        definition.application_name, cube_name=identifier.cube_name
    )
    _filter = (
        None
        if definition.filter is None
        else _cube_filter_condition_to_graphql(
            definition.filter,
            client=client,
            fact_table_identifier=identify(definition.fact_table),
        )
    )
    if application_name is not None:
        graphql_input.application_name = application_name

    if definition.id_in_cluster is not None:
        graphql_input.id_in_cluster = definition.id_in_cluster

    if definition.priority is not None:
        graphql_input.priority = definition.priority

    if _filter is not None:
        graphql_input.filter = _filter

    return graphql_input


@final
class Cubes(
    SupportsUncheckedMappingLookup[CubeName, CubeName, Cube],
    DelegatingConvertingMapping[CubeName, CubeName, Cube, CubeDefinition],
    ReprJsonable,
):
    r"""Manage the :class:`~atoti.Cube`\ s of a :class:`~atoti.Session`."""

    def __init__(
        self,
        *,
        client: Client,
        get_widget_creation_code: Callable[[], str | None],
        session_id: SessionId,
    ) -> None:
        self._client: Final = client
        self._get_widget_creation_code: Final = get_widget_creation_code
        self._session_id: Final = session_id

    @override
    def _create_lens(self, key: CubeName, /) -> Cube:
        return Cube(
            CubeIdentifier(key),
            client=self._client,
            get_widget_creation_code=self._get_widget_creation_code,
            session_id=self._session_id,
        )

    @override
    def _get_unambiguous_keys(self, *, key: CubeName | None) -> list[CubeName]:
        # Remove `self._client._py4j_client is None` once `QuerySession`s are supported.
        if self._client._py4j_client is None or self._client._graphql_client is None:
            discovery = get_discovery(client=self._client)
            return [
                cube_name
                for cube_name in discovery.cubes
                if key is None or cube_name == key
            ]

        if key is None:
            output = self._client._graphql_client.get_cubes()
            return [cube.name for cube in output.data_model.cubes]

        output = self._client._graphql_client.find_cube(cube_name=key)  # type: ignore[assignment] # See https://github.com/python/mypy/issues/12968.
        cube = output.data_model.cube  # type: ignore[attr-defined]
        return [] if cube is None else [cube.name]

    @cap_http_requests("unlimited")
    @override
    def _update_delegate(
        self,
        other: Mapping[CubeName, CubeDefinition],
        /,
    ) -> None:
        py4j_api = self._client._require_py4j_client()

        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            _get_create_cube_input(
                definition, client=self._client, identifier=CubeIdentifier(name)
            )
            for name, definition in other.items()
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.create_cube(input=graphql_input)

        if (
            not graphql_client.mutation_batcher.batching
        ):  # pragma: no branch (missing tests)
            readiness = graphql_client.get_readiness().readiness.value

            match readiness:
                case "READY":
                    for name in other:
                        # AutoJoin distributed clusters if the session has been marked as ready
                        py4j_api.auto_join_distributed_clusters(cube_name=name)

                    py4j_api.refresh()

                case "UNREADY":
                    ...

    @override
    def _delete_delegate_keys(self, keys: AbstractSet[CubeName], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [DeleteCubeInput(cube_name=key) for key in keys]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.delete_cube(
                    input=graphql_input,
                    validate_future_output=create_delete_status_validator(
                        graphql_input.cube_name,
                        lambda output: output.delete_cube.status,
                    ),
                )

    @cap_http_requests("unlimited")
    @override
    def _repr_json_(self) -> ReprJson:
        """Return the JSON representation of cubes."""
        with cached_discovery(client=self._client):
            data = {name: cube._repr_json_()[0] for name, cube in sorted(self.items())}

        return (data, {"expanded": False, "root": "Cubes"})
