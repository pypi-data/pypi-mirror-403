from __future__ import annotations

import time
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import pyarrow as pa

    from spiral.project import Project


NUM_FINEWEB_ROWS = 100_000
FINEWEB_TABLE = "examples.fineweb-100k"

NUM_EMBEDDINGS_ROWS = 1_000_000
EMBEDDINGS_TABLE = "examples.embeddings-1m"


def ingest_fineweb(project: Project) -> dict:
    """Ingest FineWeb dataset from HuggingFace.

    Table is created as spiral-test.fineweb-100k (100,000 rows).
    Returns a dict with keys: elapsed, num_rows, table_name.
    """
    from spiral.huggingface import check_huggingface_installed, ingest_dataset

    check_huggingface_installed()

    from datasets import IterableDataset, IterableDatasetDict, load_dataset

    dataset_dict = load_dataset("HuggingFaceFW/fineweb", "sample-10BT", streaming=True)
    dataset = cast(IterableDataset, cast(IterableDatasetDict, dataset_dict)["train"].take(NUM_FINEWEB_ROWS))

    start = time.time()
    ingest_dataset(
        dataset,
        project,
        FINEWEB_TABLE,
        key_columns=["date", "id"],
        batch_size=10_000,
        exist_ok=False,
        total_rows=NUM_FINEWEB_ROWS,
    )
    return {"elapsed": time.time() - start, "num_rows": NUM_FINEWEB_ROWS, "table_name": FINEWEB_TABLE}


def _generate_embeddings(num_rows: int) -> pa.Table:
    """Generate a synthetic embeddings PyArrow table with progress."""
    import numpy as np
    import pyarrow as pa
    from rich.progress import Progress

    num_sessions = 10
    num_layers = 4
    num_positions = 500
    embeddings_length = 1408
    timestamp_offset = 1770000000
    session_prefix = "very_long_session_identifier_"

    n_timestamps = num_rows // (num_sessions * num_layers * num_positions)
    sessions = np.repeat([f"{session_prefix}{i}" for i in range(num_sessions)], num_rows // num_sessions)
    timestamps = np.tile(
        np.repeat(
            np.arange(timestamp_offset * 1000, timestamp_offset * 1000 + n_timestamps * 100, 100),
            num_layers * num_positions,
        ),
        num_sessions,
    )
    layers = np.tile(np.repeat(np.arange(num_layers), num_positions), n_timestamps * num_sessions)
    positions = np.tile(np.arange(num_positions), n_timestamps * num_layers * num_sessions)

    chunk_size = 50_000
    chunks: list[pa.Array] = []
    with Progress() as progress:
        task = progress.add_task("Generating embeddings...", total=num_rows)
        for offset in range(0, num_rows, chunk_size):
            n = min(chunk_size, num_rows - offset)
            chunk = np.random.rand(n, embeddings_length)
            chunks.append(pa.array(chunk.tolist(), pa.list_(pa.float64(), embeddings_length)))
            progress.advance(task, n)

    data = pa.concat_arrays(chunks)

    return pa.Table.from_arrays(
        [
            pa.array(sessions, type=pa.string_view()),
            pa.array(timestamps, type=pa.int64()),
            pa.array(layers, type=pa.uint16()),
            pa.array(positions, type=pa.uint16()),
            data,
        ],
        names=["session", "timestamp", "layer", "pos", "embeddings"],
    )


def ingest_embeddings(project: Project) -> dict:
    """Ingest synthetic embeddings data.

    Table is created as spiral-test.embeddings-1m (1,000,000 rows).
    Returns a dict with keys: elapsed, num_rows, table_name.
    """
    import pyarrow as pa

    num_rows = NUM_EMBEDDINGS_ROWS

    key_schema = pa.schema(
        [("session", pa.string()), ("timestamp", pa.int64()), ("layer", pa.uint16()), ("pos", pa.uint16())]
    )
    table = project.create_table(EMBEDDINGS_TABLE, key_schema=key_schema, exist_ok=False)

    tbl = _generate_embeddings(num_rows)

    start = time.time()
    table.write(tbl)
    return {"elapsed": time.time() - start, "num_rows": num_rows, "table_name": EMBEDDINGS_TABLE}
