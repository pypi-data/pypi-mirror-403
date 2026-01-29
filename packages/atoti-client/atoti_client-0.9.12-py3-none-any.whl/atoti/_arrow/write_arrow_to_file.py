from pathlib import Path

import pyarrow as pa

DEFAULT_MAX_CHUNKSIZE = 1_000


def write_arrow_to_file(
    table: pa.Table,  # pyright: ignore[reportUnknownParameterType]
    path: Path,
    /,
    *,
    max_chunksize: int = DEFAULT_MAX_CHUNKSIZE,
) -> None:
    with pa.ipc.new_file(path, table.schema) as writer:
        for batch in table.to_batches(max_chunksize=max_chunksize):
            writer.write(batch)
