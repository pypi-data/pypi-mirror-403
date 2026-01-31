from typing import Any

from pydantic import BaseModel

from ..types_ import Timestamp
from .client import _Client


class Transaction(BaseModel):
    """Represents a committed transaction in SpiralDB."""

    txn_idx: int
    committed_at: Timestamp
    # TODO(marko): Define a proper Operation model
    operations: list[dict[str, Any]]


class TransactionsListResponse(BaseModel):
    """Response for listing transactions."""

    items: list[Transaction]
    next_page_token: Timestamp | None = None


class TablesService:
    """Service for managing table transactions."""

    def __init__(self, client: _Client):
        self.client = client

    def list_transactions(
        self,
        table_id: str,
        *,
        since: Timestamp | None = None,
    ) -> list[Transaction]:
        """List transactions for a table.

        Args:
            table_id: The ID of the table
            since: Only return transactions committed after this timestamp (microseconds since epoch)

        Returns:
            List of transactions
        """
        params = {"ordering": "asc"}
        if since is not None:
            params["page_token"] = str(since)

        all_transactions = []

        while True:
            response = self.client.get(
                f"/v1/tables/{table_id}/transactions-list",
                TransactionsListResponse,
                params=params,
            )

            # Parse transactions from the API response
            all_transactions.extend(response.items)

            # Check for next page
            if response.next_page_token is None:
                break

            params["page_token"] = str(response.next_page_token)

        return all_transactions

    def revert_transaction(self, table_id: str, txn_idx: int) -> None:
        """Revert a transaction by marking it as reverted.

        Args:
            table_id: The ID of the table
            txn_idx: The index of the transaction to revert
        """
        self.client.delete(f"/v1/tables/{table_id}/transactions/{txn_idx}", type[None])
