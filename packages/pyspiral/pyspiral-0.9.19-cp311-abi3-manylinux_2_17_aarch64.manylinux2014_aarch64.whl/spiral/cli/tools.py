import typer

from spiral.cli import CONSOLE, AsyncTyper, state
from spiral.cli.types_ import ProjectArg
from spiral.tools.ingest import EMBEDDINGS_TABLE, FINEWEB_TABLE, ingest_embeddings, ingest_fineweb
from spiral.tools.scan import full_scan

app = AsyncTyper(short_help="Developer tools and utilities.")


def _ensure_not_exists(p, name: str) -> None:
    """Prompt to drop if table exists, otherwise no-op."""
    try:
        p.table(name)
        if not typer.confirm("Test table already exists. Drop and reingest?"):
            raise SystemExit(0)
        p.drop_table(name)
    except ValueError:
        pass


def _choose_ingest() -> str:
    """Prompt user to select which test dataset to ingest."""
    from questionary import Choice

    from spiral.cli.chooser import choose

    choices = [
        Choice(title="[HuggingFace] Fineweb (100k)", value="fineweb"),
        Choice(title="[Generated] Embeddings (1m)", value="embeddings"),
    ]
    return choose("Select a dataset to ingest", choices)


@app.command(name="ingest", help="Ingest a test dataset.")
def ingest(
    project: ProjectArg,
) -> None:
    p = state.spiral.project(project)
    dataset = _choose_ingest()

    if dataset == "fineweb":
        _ensure_not_exists(p, FINEWEB_TABLE)
        CONSOLE.print("Ingesting 100k fineweb rows...")
        stats = ingest_fineweb(p)
        CONSOLE.print(f"Streamed {stats['num_rows']:,} rows in {stats['elapsed']:.2f}s")
    else:
        _ensure_not_exists(p, EMBEDDINGS_TABLE)
        stats = ingest_embeddings(p)
        CONSOLE.print(f"Wrote {stats['num_rows']:,} rows in {stats['elapsed']:.2f}s")


def _choose_table(p) -> str:
    """List all tables in the project and let user pick one. Returns table identifier."""
    from questionary import Choice

    from spiral.cli.chooser import choose

    tables = p.list_tables()
    if not tables:
        CONSOLE.print("[red]No tables found in this project.[/red]")
        raise SystemExit(1)

    choices = [Choice(title=f"{t.dataset}.{t.table}", value=f"{t.dataset}.{t.table}") for t in tables]

    return choose("Select a table to scan", choices)


def _fmt_bytes(n: int) -> str:
    for unit, t in [("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)]:
        if n >= t:
            return f"{n / t:.2f} {unit}"
    return f"{n} B"


def _fmt_duration(ns: float) -> str:
    for unit, t in [("s", 1e9), ("ms", 1e6), ("us", 1e3)]:
        if ns >= t:
            return f"{ns / t:.2f} {unit}"
    return f"{ns:.0f} ns"


@app.command(name="scan", help="Run a full table scan and report throughput statistics.")
def scan(
    project: ProjectArg,
) -> None:
    p = state.spiral.project(project)
    name = _choose_table(p)
    table = p.table(name)

    CONSOLE.print("Scanning...")
    stats = full_scan(state.spiral, table)

    elapsed = stats["elapsed"]
    total_rows = stats["total_rows"]
    total_bytes = stats["total_bytes"]
    io_count = stats["io_count"]
    throughput = total_bytes / elapsed if elapsed > 0 else 0.0

    CONSOLE.print()
    CONSOLE.print("[bold]Scan Results[/bold]")
    CONSOLE.print(f"  Rows scanned:          {total_rows:,}")
    CONSOLE.print(f"  Batches returned:      {stats['batch_count']:,}")
    CONSOLE.print(f"  Wall clock time:       {elapsed:.3f}s")

    CONSOLE.print()
    CONSOLE.print("[bold]Network I/O[/bold]")
    CONSOLE.print(f"  Bytes transferred:     {_fmt_bytes(total_bytes)}")
    CONSOLE.print(f"  I/O operations:        {io_count:,}")
    if io_count > 0:
        CONSOLE.print(f"  Avg I/O latency:       {_fmt_duration(stats['avg_io_duration_ns'])}")
        CONSOLE.print(f"  P99 I/O latency:       {_fmt_duration(stats['p99_io_duration_ns'])}")

    CONSOLE.print()
    CONSOLE.print("[bold]Throughput[/bold]")
    CONSOLE.print(f"  Network throughput:    {_fmt_bytes(int(throughput))}/s")
    if total_rows > 0 and elapsed > 0:
        CONSOLE.print(f"  Rows/sec:              {total_rows / elapsed:,.0f}")
        CONSOLE.print(f"  Bytes/row:             {_fmt_bytes(total_bytes // max(total_rows, 1))}")
