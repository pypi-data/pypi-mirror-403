import httpx

from .has_http_client import HasHttpClient


def get_http_client_attribute(instance: object, /) -> httpx.Client | None:
    for attribute_name in ["client", "_client"]:
        client = getattr(instance, attribute_name, None)
        if isinstance(client, HasHttpClient):
            return client.http_client

    return None
