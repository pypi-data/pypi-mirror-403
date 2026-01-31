from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spiral.client import Spiral
    from spiral.table import Table


def full_scan(sp: Spiral, table: Table) -> dict:
    """Run a full table scan and return statistics.

    Returns a dict with keys:
        total_rows, batch_count, elapsed,
        total_bytes, io_count, avg_io_duration_ns, p99_io_duration_ns
    """
    scan = sp.scan(table)

    start = time.time()
    total_rows = 0
    batch_count = 0
    for batch in scan.to_record_batches():
        total_rows += batch.num_rows
        batch_count += 1
    elapsed = time.time() - start

    total_bytes = 0
    io_count = 0
    avg_io_duration_ns = 0.0
    p99_io_duration_ns = 0.0
    for name, data in scan.metrics.items():
        if name == "spfs.io.bytes":
            io_count = int(data["count"])
            total_bytes = int(data["count"] * data["avg"])
        elif name == "spfs.io.duration":
            avg_io_duration_ns = data["avg"]
            p99_io_duration_ns = data["p99"]

    return {
        "total_rows": total_rows,
        "batch_count": batch_count,
        "elapsed": elapsed,
        "total_bytes": total_bytes,
        "io_count": io_count,
        "avg_io_duration_ns": avg_io_duration_ns,
        "p99_io_duration_ns": p99_io_duration_ns,
    }
