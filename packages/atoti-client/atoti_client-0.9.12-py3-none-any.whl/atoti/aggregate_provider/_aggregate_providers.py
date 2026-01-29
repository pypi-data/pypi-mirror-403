from collections.abc import Mapping, Set as AbstractSet
from typing import Final, final

from typing_extensions import override

from .._collections import DelegatingMutableMapping
from .._graphql import (
    DeleteAggregateProviderInput,
    create_delete_status_validator,
)
from .._identification import CubeIdentifier
from ..client import Client
from .aggregate_provider import AggregateProvider


@final
class AggregateProviders(DelegatingMutableMapping[str, AggregateProvider]):
    def __init__(self, cube_identifier: CubeIdentifier, /, *, client: Client):
        self._client: Final = client
        self._cube_identifier: Final = cube_identifier

    @override
    def _get_delegate(
        self,
        *,
        key: str | None,
    ) -> Mapping[str, AggregateProvider]:
        if key is None:
            output = self._client._require_graphql_client().get_aggregate_providers(
                cube_name=self._cube_identifier.cube_name,
            )
            return {
                provider.name: AggregateProvider._from_graphql(provider)
                for provider in output.data_model.cube.aggregate_providers
            }

        output = self._client._require_graphql_client().find_aggregate_provider(  # type: ignore[assignment] # See https://github.com/python/mypy/issues/12968.
            cube_name=self._cube_identifier.cube_name,
            name=key,
        )
        cube = output.data_model.cube

        return (
            {}
            if cube.aggregate_provider is None  # type: ignore[attr-defined]
            else {key: AggregateProvider._from_graphql(cube.aggregate_provider)}  # type: ignore[attr-defined]
        )

    @override
    def _update_delegate(self, other: Mapping[str, AggregateProvider], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            aggregate_provider._to_create_aggregate_provider_input(
                cube_identifier=self._cube_identifier, name=name
            )
            for name, aggregate_provider in other.items()
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.create_aggregate_provider(input=graphql_input)

    @override
    def _delete_delegate_keys(self, keys: AbstractSet[str], /) -> None:
        graphql_client = self._client._require_graphql_client()
        graphql_inputs = [
            DeleteAggregateProviderInput(
                aggregate_provider_name=key,
                cube_name=self._cube_identifier.cube_name,
            )
            for key in keys
        ]
        with graphql_client.mutation_batcher.batch():
            for graphql_input in graphql_inputs:
                graphql_client.delete_aggregate_provider(
                    input=graphql_input,
                    validate_future_output=create_delete_status_validator(
                        graphql_input.aggregate_provider_name,
                        lambda output: output.delete_aggregate_provider.status,
                    ),
                )
