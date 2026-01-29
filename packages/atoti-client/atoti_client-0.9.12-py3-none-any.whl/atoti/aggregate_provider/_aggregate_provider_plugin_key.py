from __future__ import annotations

from typing import Literal, TypeAlias

from .._graphql import (
    AggregateProviderPluginKey as GraphqlAggregateProviderPluginKey,
)

AggregateProviderPluginKey: TypeAlias = Literal["bitmap", "leaf"]


def plugin_key_from_graphql(  # type: ignore[return]
    plugin_key: GraphqlAggregateProviderPluginKey, /
) -> AggregateProviderPluginKey:
    match plugin_key.value:
        case "BITMAP":
            return "bitmap"
        case "LEAF":  # pragma: no branch (avoid `case _` to detect new variants)
            return "leaf"


def plugin_key_to_graphql(
    plugin_key: AggregateProviderPluginKey, /
) -> GraphqlAggregateProviderPluginKey:
    match plugin_key:
        case "bitmap":
            return GraphqlAggregateProviderPluginKey.BITMAP
        case "leaf":  # pragma: no branch (avoid `case _` to detect new variants)
            return GraphqlAggregateProviderPluginKey.LEAF
