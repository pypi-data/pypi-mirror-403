from __future__ import annotations

from collections.abc import Mapping, Set as AbstractSet
from typing import Final, final

from typing_extensions import override

from .._collections import DelegatingMutableMapping
from .._graphql import (
    CreateCubeRestrictionInput,
    DeleteCubeRestrictionInput,
    create_delete_status_validator,
)
from .._identification import CubeIdentifier, Role
from .._reserved_roles import check_no_reserved_roles
from ..client import Client
from .cube_restriction import (
    CubeRestrictionCondition,
    cube_restriction_condition_from_graphql,
    cube_restriction_condition_to_graphql,
)


@final
class CubeRestrictions(DelegatingMutableMapping[Role, CubeRestrictionCondition]):
    def __init__(self, cube_identifier: CubeIdentifier, /, *, client: Client) -> None:
        self._client: Final = client
        self._cube_identifier: Final = cube_identifier

    @override
    def _get_delegate(
        self, *, key: Role | None
    ) -> Mapping[str, CubeRestrictionCondition]:
        if key is None:
            output = self._client._require_graphql_client().get_cube_restrictions(
                cube_name=self._cube_identifier.cube_name
            )
            return {
                restriction.role: cube_restriction_condition_from_graphql(
                    restriction.condition.value
                )
                for restriction in output.data_model.cube.restrictions
            }

        output = self._client._require_graphql_client().find_cube_restriction(  # type: ignore[assignment] # See https://github.com/python/mypy/issues/12968.
            cube_name=self._cube_identifier.cube_name,
            role=key,
        )
        cube = output.data_model.cube
        return (
            {}
            if cube.restriction is None  # type: ignore[attr-defined]
            else {
                key: cube_restriction_condition_from_graphql(
                    cube.restriction.condition.value  # type: ignore[attr-defined]
                )
            }
        )

    @override
    def _update_delegate(
        self, other: Mapping[Role, CubeRestrictionCondition], /
    ) -> None:
        check_no_reserved_roles(other)

        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            CreateCubeRestrictionInput(
                condition=cube_restriction_condition_to_graphql(condition),
                cube_name=self._cube_identifier.cube_name,
                role=role,
            )
            for role, condition in other.items()
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.create_cube_restriction(input=graphql_input)

    @override
    def _delete_delegate_keys(self, keys: AbstractSet[Role], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            DeleteCubeRestrictionInput(
                cube_name=self._cube_identifier.cube_name,
                role=role,
            )
            for role in keys
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.delete_cube_restriction(
                    input=graphql_input,
                    validate_future_output=create_delete_status_validator(
                        graphql_input.role,
                        lambda output: output.delete_cube_restriction.status,
                    ),
                )
