from __future__ import annotations

from collections.abc import Mapping, Set as AbstractSet
from typing import Final, TypeAlias, final

from typing_extensions import override

from .._collections import DelegatingMutableMapping
from .._graphql import (
    CreateRoleMappingItemInput,
    DeleteRoleMappingItemInput,
    GetRoleMappingItemSecuritySsoLdapSecurity,
    GetRoleMappingItemSecuritySsoOidcSecurity,
    GetRoleMappingItemsSecuritySsoLdapSecurity,
    GetRoleMappingItemsSecuritySsoOidcSecurity,
    create_delete_status_validator,
)
from .._identification import Role
from ..client import Client
from ._authentication_type import AuthenticationType

_RoleMapping: TypeAlias = Mapping[str, AbstractSet[Role]]


@final
class RoleMapping(DelegatingMutableMapping[str, AbstractSet[Role]]):
    """Mapping from role or username coming from the authentication provider to roles to use in the session."""

    def __init__(
        self,
        *,
        authentication_type: AuthenticationType,
        client: Client,
    ) -> None:
        self._authentication_type: Final = authentication_type
        self._client: Final = client

    @override
    def _get_delegate(self, *, key: str | None) -> _RoleMapping:
        graphql_client = self._client._require_graphql_client()

        if key is None:
            output = graphql_client.get_role_mapping_items()
            sso = output.security.sso
            assert isinstance(
                sso,
                (
                    GetRoleMappingItemsSecuritySsoLdapSecurity
                    | GetRoleMappingItemsSecuritySsoOidcSecurity
                ),
            )
            return {
                item.external_role: frozenset(item.internal_roles)
                for item in sso.role_mapping_items
            }

        output_item = graphql_client.get_role_mapping_item(username=key)
        sso_item = output_item.security.sso
        assert isinstance(
            sso_item,
            (
                GetRoleMappingItemSecuritySsoLdapSecurity
                | GetRoleMappingItemSecuritySsoOidcSecurity
            ),
        )
        return (
            {key: frozenset(sso_item.role_mapping_item.internal_roles)}
            if sso_item.role_mapping_item
            else {}
        )

    @override
    def _update_delegate(self, other: Mapping[str, AbstractSet[Role]], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            CreateRoleMappingItemInput(
                external_role=external_role, internal_roles=list(internal_roles)
            )
            for external_role, internal_roles in other.items()
        ]

        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.create_role_mapping_item(input=graphql_input)

    @override
    def _delete_delegate_keys(self, keys: AbstractSet[str], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [DeleteRoleMappingItemInput(external_role=key) for key in keys]

        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.delete_role_mapping_item(
                    input=graphql_input,
                    validate_future_output=create_delete_status_validator(
                        graphql_input.external_role,
                        lambda output: output.delete_role_mapping_item.status,
                    ),
                )
