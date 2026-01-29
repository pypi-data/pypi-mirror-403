from collections.abc import Mapping, Set as AbstractSet
from typing import Final, final

from typing_extensions import override

from ._collections import DelegatingMutableMapping
from ._graphql import (
    CreateMemberPropertyInput,
    DeleteMemberPropertyInput,
    create_delete_status_validator,
)
from ._identification import (
    ColumnIdentifier,
    CubeIdentifier,
    Identifiable,
    LevelIdentifier,
    identify,
)
from .client import Client


@final
class MemberProperties(DelegatingMutableMapping[str, Identifiable[ColumnIdentifier]]):
    def __init__(
        self,
        level_identifier: LevelIdentifier,
        /,
        *,
        client: Client,
        cube_identifier: CubeIdentifier,
    ):
        self._client: Final = client
        self._cube_identifier: Final = cube_identifier
        self._level_identifier: Final = level_identifier

    @override
    def _get_delegate(
        self,
        *,
        key: str | None,
    ) -> Mapping[str, Identifiable[ColumnIdentifier]]:
        graphql_client = self._client._require_graphql_client()
        if key is None:
            get_properties_output = graphql_client.get_member_properties(
                cube_name=self._cube_identifier.cube_name,
                dimension_name=self._level_identifier.hierarchy_identifier.dimension_identifier.dimension_name,
                hierarchy_name=self._level_identifier.hierarchy_identifier.hierarchy_name,
                level_name=self._level_identifier.level_name,
            )

            return {
                member_property.name: ColumnIdentifier._from_graphql(
                    member_property.column
                )
                for member_property in get_properties_output.data_model.cube.dimension.hierarchy.level.member_properties
            }

        get_property_output = graphql_client.find_member_property(
            cube_name=self._cube_identifier.cube_name,
            dimension_name=self._level_identifier.hierarchy_identifier.dimension_identifier.dimension_name,
            hierarchy_name=self._level_identifier.hierarchy_identifier.hierarchy_name,
            level_name=self._level_identifier.level_name,
            property_name=key,
        )

        identifier = get_property_output.data_model.cube.dimension.hierarchy.level.member_property
        if identifier is None:  # pragma: no cover (missing tests)
            return {}
        return {identifier.name: ColumnIdentifier._from_graphql(identifier.column)}

    @override
    def _update_delegate(
        self,
        other: Mapping[str, Identifiable[ColumnIdentifier]],
        /,
    ) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            CreateMemberPropertyInput(
                column_identifier=identify(column)._to_graphql(),
                cube_name=self._cube_identifier.cube_name,
                level_identifier=self._level_identifier._to_graphql(),
                property_name=name,
            )
            for name, column in other.items()
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.create_member_property(input=graphql_input)

    @override
    def _delete_delegate_keys(self, keys: AbstractSet[str], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            DeleteMemberPropertyInput(
                cube_name=self._cube_identifier.cube_name,
                level_identifier=self._level_identifier._to_graphql(),
                property_name=key,
            )
            for key in keys
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.delete_member_property(
                    input=graphql_input,
                    validate_future_output=create_delete_status_validator(
                        graphql_input.property_name,
                        lambda output: output.delete_member_property.status,
                    ),
                )
