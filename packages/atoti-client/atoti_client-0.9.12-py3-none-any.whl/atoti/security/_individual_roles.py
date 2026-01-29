from __future__ import annotations

from collections.abc import Mapping, Set as AbstractSet
from typing import Final, final

from typing_extensions import override

from .._collections import DelegatingMutableMapping
from .._graphql import (
    CreateIndividualRolesItemInput,
    DeleteIndividualRolesItemInput,
    create_delete_status_validator,
)
from .._identification import Role, UserName
from ..client import Client


@final
class IndividualRoles(DelegatingMutableMapping[UserName, AbstractSet[Role]]):
    def __init__(self, *, client: Client) -> None:
        self._client: Final = client

    @override
    def _get_delegate(
        self, *, key: UserName | None
    ) -> Mapping[UserName, AbstractSet[Role]]:
        graphql_client = self._client._require_graphql_client()

        if key is None:
            output_roles = graphql_client.get_individual_roles_items()
            return {
                item.username: frozenset(item.individual_roles)
                for item in output_roles.security.individual_roles_items
            }

        role_item = graphql_client.get_individual_roles_item(
            username=key
        ).security.individual_roles_item
        return {key: frozenset(role_item.individual_roles)} if role_item else {}

    @override
    def _update_delegate(self, other: Mapping[UserName, AbstractSet[Role]], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            CreateIndividualRolesItemInput(
                username=username,
                individual_roles=list(roles),
            )
            for username, roles in other.items()
        ]

        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.create_individual_roles_item(input=graphql_input)

    @override
    def _delete_delegate_keys(self, keys: AbstractSet[UserName], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            DeleteIndividualRolesItemInput(username=username) for username in keys
        ]

        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.delete_individual_roles_item(
                    input=graphql_input,
                    validate_future_output=create_delete_status_validator(
                        graphql_input.username,
                        lambda output: output.delete_individual_roles_item.status,
                    ),
                )
