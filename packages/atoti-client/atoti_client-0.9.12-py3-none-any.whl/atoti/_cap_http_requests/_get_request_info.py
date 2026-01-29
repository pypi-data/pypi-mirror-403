import json
from collections.abc import Mapping
from mimetypes import types_map
from os import linesep
from pprint import pformat
from typing import final

import httpx
from typing_extensions import TypedDict

from .._mime_type import GRAPHQL_RESPONSE_MIME_TYPE
from .._pydantic import get_type_adapter


@final
class _GraphqlRequestBody(TypedDict, total=True):
    query: str
    operationName: str | None
    variables: Mapping[str, object]


def get_request_info(request: httpx.Request, /, *, index: int | None = None) -> str:
    assert index is None or index >= 1

    lines = [f"{'' if index is None else f'{index}. '}{request.method} {request.url}"]

    if request.method not in {"GET", "HEAD", "DELETE"}:
        lines.append("")

        if (
            request.headers.get("Content-Type") == types_map[".json"]
        ):  # pragma: no branch (missing tests)
            if request.headers.get("Accept") == GRAPHQL_RESPONSE_MIME_TYPE:
                graphql_request_body = get_type_adapter(
                    _GraphqlRequestBody
                ).validate_json(request.content)
                operation_name = graphql_request_body["operationName"]
                lines.extend(
                    [
                        "Variables:"
                        if operation_name is None
                        else f"Operation: {operation_name}, variables:",
                        "",
                        pformat(graphql_request_body["variables"]),
                        "",
                        "```graphql",
                        *graphql_request_body["query"].splitlines(),
                        "```",
                    ]
                )
            else:
                body = json.loads(request.content)
                lines.append(pformat(body))

    return linesep.join(lines)
