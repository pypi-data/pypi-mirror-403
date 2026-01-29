from collections.abc import Set as AbstractSet
from typing import Final, final

from typing_extensions import override

from .._collections import DelegatingMutableSet
from .._graphql import UpdateSsoSecurityInput
from .._identification import Role
from ..client import Client
from ._authentication_type import AuthenticationType


@final
class DefaultRoles(DelegatingMutableSet[Role]):
    """Roles granted to users who have been granted no :attr:`individual <atoti.security.Security.individual_roles>` and :class:`mapped <atoti.security.role_mapping.RoleMapping>` roles."""

    def __init__(
        self, *, authentication_type: AuthenticationType, client: Client
    ) -> None:
        self._authentication_type: Final = authentication_type
        self._client: Final = client

    @override
    def _get_delegate(self) -> AbstractSet[Role]:
        return frozenset(
            self._client._require_graphql_client()
            .get_default_roles()
            .security.sso.default_roles
        )

    @override
    def _set_delegate(self, new_set: AbstractSet[Role], /) -> None:
        self._client._require_graphql_client().update_sso_security(
            input=UpdateSsoSecurityInput(default_roles=list(new_set))
        )
