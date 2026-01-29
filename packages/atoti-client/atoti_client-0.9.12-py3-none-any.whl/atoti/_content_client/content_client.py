from __future__ import annotations

from typing import Final, final
from urllib.parse import urlencode

import httpx

from .._pydantic import get_type_adapter
from ..client._get_path_and_version_id import get_path_and_version_id
from ..client._server_versions import ServerVersions
from .content import ContentTree

_API_NAME = "activeviam/content"


@final
class ContentClient:
    def __init__(
        self, *, http_client: httpx.Client, server_versions: ServerVersions
    ) -> None:
        self._http_client: Final = http_client
        self._path: Final = get_path_and_version_id(
            _API_NAME, server_versions=server_versions
        )[0]

    def _add_path(self, path: str, /) -> str:
        return f"{self._path}/files?{urlencode({'path': path})}"

    def get(self, path: str, /) -> ContentTree | None:
        path = self._add_path(path)
        response = self._http_client.get(path)
        if (
            response.status_code == httpx.codes.NOT_FOUND
        ):  # pragma: no cover (missing tests)
            return None
        response.raise_for_status()
        body = response.content
        return get_type_adapter(ContentTree).validate_json(body)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
