from typing import Final, final

import httpx
import pyarrow as pa

from ..client import Client
from .context import Context


# Adapted from https://github.com/encode/httpx/discussions/2296#discussioncomment-6781355.
@final
class _FileLikeAdapter:
    def __init__(self, response: httpx.Response, /):
        self._response: Final = response
        self._iterator: Final = response.iter_raw()
        self._buffer = bytearray()

    @property
    def closed(self) -> bool:
        return self._response.is_closed

    def read(self, size: int) -> bytes:
        assert size > 0

        for chunk in self._iterator:
            self._buffer += chunk
            if len(self._buffer) >= size:  # pragma: no branch
                break

        data = bytes(self._buffer[:size])
        del self._buffer[:size]
        return data


def execute_query_to_arrow_table(  # pyright: ignore[reportUnknownParameterType]
    mdx: str, /, *, client: Client, context: Context
) -> pa.Table:
    path = f"{client.get_path_and_version_id('activeviam/pivot')[0]}/cube/dataexport/download"
    with client.http_client.stream(
        "POST",
        path,
        json={
            "jsonMdxQuery": {"context": context, "mdx": mdx},
            "outputConfiguration": {"format": "arrow"},
        },
    ) as response:
        response.raise_for_status()
        source = _FileLikeAdapter(response)
        with pa.ipc.open_stream(source) as reader:
            schema = pa.schema(
                [
                    field.with_nullable(True)  # noqa: FBT003
                    for field in reader.schema
                ]
            )
            return pa.Table.from_batches(reader, schema=schema)
