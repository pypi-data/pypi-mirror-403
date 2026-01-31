from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import pyarrow as pa
import ray
from ray.data.block import Block
from ray.data.datasource.datasink import WriteResult

from spiral import Spiral, Transaction
from spiral.core.config import ClientSettings
from spiral.core.table.spec import TransactionOps
from spiral.types_ import Timestamp

if TYPE_CHECKING:
    from ray.data._internal.execution.interfaces import TaskContext


# TODO(DK): we should just ship the serde bytes not JSON-serialized strings.
class Datasink(ray.data.Datasink[tuple[Timestamp, list[str]]]):
    def __init__(self, txn: Transaction):
        super().__init__()
        self._table_id: str = txn.table.table_id
        self._spiral_config_json = txn.table.spiral.config.to_json()
        self._txn = txn

    def __getstate__(self):
        state = dict(self.__dict__)
        state["_txn"] = None  # do not serialize the transaction
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def on_write_complete(self, write_result: WriteResult[TransactionOps]):
        assert self._txn is not None  # on_write_complete happens on the driver

        for tx_ops in write_result.write_returns:
            self._txn.include(tx_ops)

    def on_write_failed(self, error: Exception):
        pass

    def on_write_start(self, schema: pa.Schema | None = None):
        pass

    def write(
        self,
        blocks: Iterable[Block],
        ctx: TaskContext,
    ) -> TransactionOps:
        assert self._txn is None  # writes happen on workers

        import pyarrow

        sp = Spiral(config=ClientSettings.from_json(self._spiral_config_json))

        # Do *not* use a context manager and do *not* call commit/abort.
        # We instead `take` and send the operations to the driver node.
        txn = sp.table(self._table_id).txn()

        for block in blocks:
            if not isinstance(block, pyarrow.Table):
                try:
                    import pandas as pd

                    assert isinstance(block, pd.DataFrame)
                    block = pyarrow.Table.from_pandas(block)
                except ImportError:
                    raise TypeError(f"Expected block to be a pyarrow.Table or pandas.DataFrame, got {type(block)}")

            txn.write(block)

        return txn.take()
