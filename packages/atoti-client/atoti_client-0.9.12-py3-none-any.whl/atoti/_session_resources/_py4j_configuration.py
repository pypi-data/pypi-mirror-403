from typing import final

import httpx
from pydantic.dataclasses import dataclass

from .._pydantic import PYDANTIC_CONFIG
from ..client import Client
from ..client._get_json_response_body_type_adapter import (
    get_json_response_body_type_adapter,
)


@final
@dataclass(config=PYDANTIC_CONFIG, frozen=True, kw_only=True)
class Py4jConfiguration:
    distributed: bool
    port: int
    token: str | None = None


def get_py4j_configuration(*, client: Client) -> Py4jConfiguration | None:
    path = f"{client.get_path_and_version_id('atoti')[0]}/py4j/configuration"
    response = client.http_client.get(path)
    return (
        get_json_response_body_type_adapter(Py4jConfiguration).validate_json(
            response.content
        )
        if response.status_code == httpx.codes.OK
        else None
    )
