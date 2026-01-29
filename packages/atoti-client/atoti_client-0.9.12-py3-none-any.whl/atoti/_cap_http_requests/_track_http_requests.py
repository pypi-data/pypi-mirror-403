from collections.abc import Generator
from contextlib import contextmanager
from threading import current_thread

import httpx


@contextmanager
def track_requests(
    http_client: httpx.Client, /
) -> Generator[list[httpx.Request], None, None]:
    original_thread = current_thread()
    requests: list[httpx.Request] = []

    def track_request(request: httpx.Request, /) -> None:
        if current_thread() is original_thread:
            requests.append(request)

    http_client.event_hooks["request"].append(track_request)
    try:
        yield requests
    finally:
        http_client.event_hooks["request"].remove(track_request)
