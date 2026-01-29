from __future__ import annotations

from collections.abc import Mapping, Set as AbstractSet
from typing import Final, final

from typing_extensions import override

from .._collections import DelegatingMutableMapping
from .._graphql import (
    CreateDatabaseRestrictionInput,
    DeleteDatabaseRestrictionInput,
    create_delete_status_validator,
)
from .._identification import Role
from .._reserved_roles import check_no_reserved_roles
from ..client import Client
from .database_restriction import (
    DatabaseRestrictionCondition,
    database_restriction_condition_from_graphql,
    database_restriction_condition_to_graphql,
)


@final
class DatabaseRestrictions(
    DelegatingMutableMapping[Role, DatabaseRestrictionCondition]
):
    def __init__(self, *, client: Client) -> None:
        self._client: Final = client

    @override
    def _get_delegate(
        self, *, key: Role | None
    ) -> Mapping[Role, DatabaseRestrictionCondition]:
        if key is None:
            restrictions = (
                self._client._require_graphql_client().get_database_restrictions()
            )
            return {
                restriction.role: database_restriction_condition_from_graphql(
                    restriction.condition.value
                )
                for restriction in restrictions.data_model.database.restrictions
            }

        restriction = self._client._require_graphql_client().get_database_restriction(
            role=key,
        )
        return (
            {}
            if restriction.data_model.database.restriction is None
            else {
                key: database_restriction_condition_from_graphql(
                    restriction.data_model.database.restriction.condition.value
                )
            }
        )

    @override
    def _update_delegate(
        self, other: Mapping[Role, DatabaseRestrictionCondition], /
    ) -> None:
        check_no_reserved_roles(other)

        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            CreateDatabaseRestrictionInput(
                condition=database_restriction_condition_to_graphql(condition),
                role=role,
            )
            for role, condition in other.items()
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.create_database_restriction(input=graphql_input)

    @override
    def _delete_delegate_keys(self, keys: AbstractSet[Role], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            DeleteDatabaseRestrictionInput(
                role=role,
            )
            for role in keys
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.delete_database_restriction(
                    input=graphql_input,
                    validate_future_output=create_delete_status_validator(
                        graphql_input.role,
                        lambda output: output.delete_database_restriction.status,
                    ),
                )
