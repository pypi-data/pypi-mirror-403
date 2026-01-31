from datetime import UTC
from typing import Annotated

import questionary
import rich
import rich.table
import typer
from typer import Option

from spiral.cli import CONSOLE, AsyncTyper, state
from spiral.cli.tables import get_table
from spiral.cli.types_ import ProjectArg

app = AsyncTyper(short_help="Table Transactions.")


@app.command("ls", help="List transactions for a table.")
def ls(
    project: ProjectArg,
    table: Annotated[str | None, Option(help="Table name.")] = None,
    dataset: Annotated[str | None, Option(help="Dataset name.")] = None,
    since: Annotated[
        int | None, Option(help="List transactions committed after this timestamp (microseconds).")
    ] = None,
):
    from datetime import datetime

    identifier, t = get_table(project, table, dataset)

    # Get transactions from the API
    transactions = state.spiral.api.tables.list_transactions(
        table_id=t.table_id,
        since=since,
    )

    if not transactions:
        CONSOLE.print("No transactions found.")
        return

    # Create a rich table to display transactions
    rich_table = rich.table.Table(
        "Table ID", "Tx Index", "Committed At", "Operations", title=f"Transactions for {identifier}"
    )

    for txn in transactions:
        # Convert timestamp to readable format
        dt = datetime.fromtimestamp(txn.committed_at / 1_000_000, tz=UTC)
        committed_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Count operations by type
        op_counts: dict[str, int] = {}
        for op in txn.operations:
            # Operation is a dict with a single key indicating the type
            op_type = op["type"]
            op_counts[op_type] = op_counts.get(op_type, 0) + 1

        op_summary = ", ".join(f"{count}x {op_type}" for op_type, count in op_counts.items())

        rich_table.add_row(t.table_id, str(txn.txn_idx), committed_str, op_summary)

    CONSOLE.print(rich_table)


@app.command("revert", help="Revert a transaction by table ID and transaction index.")
def revert(
    table_id: str,
    txn_idx: int,
):
    # Ask for confirmation
    CONSOLE.print(
        "[yellow]Only transactions still in WAL can be reverted. "
        "It is recommended to only revert the latest transaction. "
        "Reverting historical transactions may break a table.[/yellow]"
    )
    confirm = questionary.confirm(
        f"Are you sure you want to revert transaction {txn_idx} for table '{table_id}'?\n"
    ).ask()
    if not confirm:
        CONSOLE.print("Aborted.")
        raise typer.Exit(0)

    # Revert the transaction
    state.spiral.api.tables.revert_transaction(table_id=table_id, txn_idx=txn_idx)
    CONSOLE.print(f"Successfully reverted transaction {txn_idx} for table {table_id}.")
