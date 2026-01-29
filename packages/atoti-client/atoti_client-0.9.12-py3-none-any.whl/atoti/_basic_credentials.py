from __future__ import annotations

from collections.abc import Mapping, Set as AbstractSet
from typing import Final, final

from typing_extensions import override

from ._collections import DelegatingMutableMapping
from ._graphql import (
    CreateBasicAuthenticationUserInput,
    DeleteBasicAuthenticationUserInput,
    create_delete_status_validator,
)
from ._identification import UserName
from .client import Client

_REDACTED_PASSWORD = "**REDACTED**"  # noqa: S105


@final
class BasicCredentials(DelegatingMutableMapping[UserName, str]):
    def __init__(self, *, client: Client) -> None:
        self._client: Final = client

    @override
    def _get_delegate(self, *, key: UserName | None) -> Mapping[UserName, str]:
        output = self._client._require_graphql_client().get_basic_authentication_users()
        return {
            username: _REDACTED_PASSWORD
            for username in output.security.basic_authentication.usernames
            if key is None or username == key
        }

    @override
    def _update_delegate(self, other: Mapping[UserName, str], /) -> None:
        graphql_client = self._client._require_graphql_client()

        graphql_inputs = [
            CreateBasicAuthenticationUserInput(username=username, password=password)
            for username, password in other.items()
        ]

        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.create_basic_authentication_user(input=graphql_input)

    @override
    def _delete_delegate_keys(self, keys: AbstractSet[UserName], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            DeleteBasicAuthenticationUserInput(username=username) for username in keys
        ]

        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.delete_basic_authentication_user(
                    input=graphql_input,
                    validate_future_output=create_delete_status_validator(
                        graphql_input.username,
                        lambda output: output.delete_basic_authentication_user.status,
                    ),
                )
