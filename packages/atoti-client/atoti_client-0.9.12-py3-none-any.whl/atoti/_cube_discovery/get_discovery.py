from collections.abc import Generator, MutableMapping
from contextlib import contextmanager
from weakref import WeakKeyDictionary

from ..client import Client
from ..client._get_json_response_body_type_adapter import (
    get_json_response_body_type_adapter,
)
from .discovery import Discovery

_DISCOVERY_CACHE: MutableMapping[Client, Discovery | None] = WeakKeyDictionary()


@contextmanager
def cached_discovery(*, client: Client) -> Generator[None, None, None]:
    is_already_caching = client in _DISCOVERY_CACHE
    if not is_already_caching:
        _DISCOVERY_CACHE[client] = None
    try:
        yield
    finally:
        if not is_already_caching:
            del _DISCOVERY_CACHE[client]


def get_discovery(*, client: Client) -> Discovery:
    if (discovery := _DISCOVERY_CACHE.get(client)) is not None:
        return discovery

    path = f"{client.get_path_and_version_id('activeviam/pivot')[0]}/cube/discovery"
    response = client.http_client.get(path).raise_for_status()
    body = response.content
    discovery = get_json_response_body_type_adapter(Discovery).validate_json(body)

    if _DISCOVERY_CACHE.get(client, default="missing") is None:
        _DISCOVERY_CACHE[client] = discovery

    return discovery
