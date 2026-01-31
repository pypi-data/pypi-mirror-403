import warnings
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from spiral.core.client import Shard, ShuffleConfig
from spiral.core.table import Scan as CoreScan
from spiral.core.table.spec import Schema
from spiral.input import TableLike, evaluate

if TYPE_CHECKING:
    import dask.dataframe as dd
    import datasets.iterable_dataset as hf  # noqa
    import pandas as pd
    import polars as pl
    import ray.data
    import streaming  # noqa
    import torch.utils.data as torchdata  # noqa

    from spiral.client import Spiral
    from spiral.dataloader import SpiralDataLoader, World  # noqa


class Scan:
    """Scan object."""

    def __init__(self, spiral: "Spiral", core: CoreScan):
        self.spiral = spiral
        self.core = core

    @property
    def limit(self) -> int | None:
        """Returns the limit set on this scan, if any."""
        return self.core.plan_context().limit()

    @property
    def metrics(self) -> dict[str, Any]:
        """Returns metrics about the scan."""
        return self.core.metrics()

    @property
    def schema(self) -> Schema:
        """Returns the schema of the scan."""
        return self.core.schema()

    @property
    def key_schema(self) -> Schema:
        """Returns the key schema of the scan."""
        return self.core.key_schema()

    def is_empty(self) -> bool:
        """Check if the Spiral is empty for the given key range.

        False negatives are possible, but false positives are not,
            i.e. is_empty can return False and scan can return zero rows.
        """
        return self.core.is_empty()

    def to_record_batches(
        self,
        *,
        shards: list[Shard] | None = None,
        key_table: TableLike | None = None,
        batch_readahead: int | None = None,
        batch_aligned: bool | None = None,
        hide_progress_bar: bool | None = None,
    ) -> pa.RecordBatchReader:
        """Read as a stream of RecordBatches.

        Args:
            shards: Optional list of shards to evaluate.
                If provided, only the specified shards will be read.
                Must not be provided together with key_table.
            key_table: a table of keys to "take" (including aux columns for cell-push-down).
                Key table must be either a table or a stream of table-like objects
                (e.g. Arrow's RecordBatchReader). For optimal performance, each batch should
                contain sorted and unique keys. Unsorted and duplicate keys are still supported,
                but performance is less predictable. If None, the scan will be executed without
                a key table.
            batch_readahead: the number of batches to prefetch in the background.
            batch_aligned: if True, ensures that batches are aligned with key_table batches.
                The stream will yield batches that correspond exactly to the batches in key_table,
                but may be less efficient and use more memory (aligning batches requires buffering and maybe a copy).
                Must only be used when key_table is provided.
            hide_progress_bar: If True, disables the progress bar during reading.
        """
        batch_aligned = False if batch_aligned is None else batch_aligned
        hide_progress_bar = False if hide_progress_bar is None else hide_progress_bar

        if key_table is not None:
            key_table = evaluate(key_table)

        # NOTE(marko): Uncomment for better debuggability.
        # rb: pa.RecordBatch = self.core.to_record_batch(shards=shards, key_table=key_table)
        # return pa.RecordBatchReader.from_batches(rb.schema, [rb])

        return self.core.to_record_batches(
            shards=shards,
            key_table=key_table,
            batch_readahead=batch_readahead,
            batch_aligned=batch_aligned,
            hide_progress_bar=hide_progress_bar,
        )

    def to_unordered_record_batches(
        self,
        *,
        shards: list[Shard] | None = None,
        key_table: TableLike | None = None,
        batch_readahead: int | None = None,
        hide_progress_bar: bool | None = None,
    ) -> pa.RecordBatchReader:
        """Read as a stream of RecordBatches, NOT ordered by key.

        Args:
            shards: Optional list of shards to evaluate.
                If provided, only the specified shards will be read.
                Must not be provided together with key_table.
            key_table: a table of keys to "take" (including aux columns for cell-push-down).
                Key table must be either a table or a stream of table-like objects
                (e.g. Arrow's RecordBatchReader). For optimal performance, each batch should
                contain sorted and unique keys. Unsorted and duplicate keys are still supported,
                but performance is less predictable. If None, the scan will be executed without
                a key table.
            batch_readahead: the number of batches to prefetch in the background.
            hide_progress_bar: If True, disables the progress bar during reading.
        """
        hide_progress_bar = False if hide_progress_bar is None else hide_progress_bar

        if key_table is not None:
            key_table = evaluate(key_table)

        return self.core.to_unordered_record_batches(
            shards=shards,
            key_table=key_table,
            batch_readahead=batch_readahead,
            hide_progress_bar=hide_progress_bar,
        )

    def to_table(
        self,
        *,
        shards: list[Shard] | None = None,
        key_table: TableLike | None = None,
        batch_readahead: int | None = None,
        hide_progress_bar: bool | None = None,
    ) -> pa.Table:
        """Read into a single PyArrow Table.

        Warnings:
            This downloads the entire Spiral Table into memory on this machine.

        Args:
            shards: Optional list of shards to evaluate.
                If provided, only the specified shards will be read.
                Must not be provided together with key_table.
            key_table: a table of keys to "take" (including aux columns for cell-push-down).
                If None, the scan will be executed without a key table.
            batch_readahead: the number of batches to prefetch in the background.
            hide_progress_bar: If True, disables the progress bar during reading.

        Returns:
            pyarrow.Table

        """
        return self.to_record_batches(
            shards=shards,
            key_table=key_table,
            batch_readahead=batch_readahead,
            hide_progress_bar=hide_progress_bar,
        ).read_all()

    def to_dask(
        self,
        *,
        shards: list[Shard] | None = None,
        batch_readahead: int | None = None,
        hide_progress_bar: bool | None = None,
    ) -> "dd.DataFrame":
        """Read into a Dask DataFrame.

        Requires the `dask` package to be installed.

        Dask execution has some limitations, e.g. UDFs are not currently supported. These limitations
        usually manifest as serialization errors when Dask workers attempt to serialize the state. If you are
        encountering such issues, please reach out to the support for assistance.

        Args:
            shards: Optional list of shards to evaluate.
                If provided, only the specified shards will be read.
            batch_readahead: the number of batches to prefetch in the background.
                Applies to each shard read task.
            hide_progress_bar: If True, disables the progress bar during reading.

        Returns:
            dask.dataframe.DataFrame

        """
        import dask.dataframe as dd

        if self.limit is not None:
            warnings.warn(
                f"Scan has limit={self.limit} set. In distributed execution, the limit will be "
                "applied to each worker independently, not globally. This may return more rows "
                "than the specified limit.",
                stacklevel=2,
            )

        config_json = self.spiral.config.to_json()
        state_bytes = self.core.plan_context().to_bytes_compressed()

        shards = shards or self.shards()

        def _read_shard(shard: Shard) -> "pd.DataFrame":
            arrow_table = _read_shard_task(
                shard,
                config_json=config_json,
                state_bytes=state_bytes,
                batch_readahead=batch_readahead,
                hide_progress_bar=hide_progress_bar,
            )
            return arrow_table.to_pandas()

        return dd.from_map(_read_shard, shards)

    def to_ray_dataset(
        self,
        *,
        shards: list[Shard] | None = None,
        batch_readahead: int | None = None,
        hide_progress_bar: bool | None = None,
    ) -> "ray.data.Dataset":
        """Read into a Ray Dataset.

        Requires the `ray` package to be installed.

        Warnings:
            If the Scan returns zero rows, the resulting Ray Dataset will have [an empty
            schema](https://github.com/ray-project/ray/issues/59946).

        Args:
            shards: Optional list of shards to evaluate.
                If provided, only the specified shards will be read.
            batch_readahead: the number of batches to prefetch in the background.
            hide_progress_bar: If True, disables the progress bar during reading.

        Returns:
            ray.data.Dataset: A Ray Dataset distributed across shards.

        """
        import ray

        if self.limit is not None:
            warnings.warn(
                f"Scan has limit={self.limit} set. In distributed execution, the limit will be "
                "applied to each worker independently, not globally. This may return more rows "
                "than the specified limit.",
                stacklevel=2,
            )

        config_json = self.spiral.config.to_json()
        state_bytes = self.core.plan_context().to_bytes_compressed()

        shards = shards or self.shards()

        read_shard_remote = ray.remote(_read_shard_task)
        refs = [
            read_shard_remote.remote(
                shard,
                config_json=config_json,
                state_bytes=state_bytes,
                batch_readahead=batch_readahead,
                hide_progress_bar=hide_progress_bar,
            )
            for shard in shards
        ]

        return ray.data.from_arrow_refs(refs)

    def to_pandas(
        self,
        *,
        shards: list[Shard] | None = None,
        key_table: TableLike = None,
        batch_readahead: int | None = None,
        hide_progress_bar: bool | None = None,
    ) -> "pd.DataFrame":
        """Read into a Pandas DataFrame.

        Requires the `pandas` package to be installed.

        Warnings:
            This downloads the entire Spiral Table into memory on this machine.

        Args:
            shards: Optional list of shards to evaluate.
                If provided, only the specified shards will be read.
                Must not be provided together with key_table.
            key_table: a table of keys to "take" (including aux columns for cell-push-down).
                If None, the scan will be executed without a key table.
            batch_readahead: the number of batches to prefetch in the background.
            hide_progress_bar: If True, disables the progress bar during reading.

        Returns:
            pandas.DataFrame

        """
        return (
            self.to_record_batches(
                shards=shards,
                key_table=key_table,
                batch_readahead=batch_readahead,
                hide_progress_bar=hide_progress_bar,
            )
            .read_all()
            .to_pandas()
        )

    def to_polars(
        self,
        *,
        shards: list[Shard] | None = None,
        key_table: TableLike = None,
        batch_readahead: int | None = None,
        hide_progress_bar: bool | None = None,
    ) -> "pl.DataFrame":
        """Read into a Polars DataFrame.

        Requires the `polars` package to be installed.

        Warnings:
            This downloads the entire Spiral Table into memory on this machine. To lazily interact
            with a Spiral Table try Table.to_polars_lazy_frame.

        Args:
            shards: Optional list of shards to evaluate.
                If provided, only the specified shards will be read.
                Must not be provided together with key_table.
            key_table: a table of keys to "take" (including aux columns for cell-push-down).
                If None, the scan will be executed without a key table.
            batch_readahead: the number of batches to prefetch in the background.
            hide_progress_bar: If True, disables the progress bar during reading.

        Returns:
            polars.DataFrame

        """
        import polars as pl

        return pl.DataFrame(
            self.to_record_batches(
                shards=shards,
                key_table=key_table,
                batch_readahead=batch_readahead,
                hide_progress_bar=hide_progress_bar,
            )
        )

    def to_data_loader(
        self, seed: int = 42, shuffle_buffer_size: int = 0, batch_size: int = 32, **kwargs
    ) -> "SpiralDataLoader":
        """Read into a Torch-compatible DataLoader for single-node training.

        Args:
            seed: Random seed for reproducibility.
            shuffle_buffer_size: Size of shuffle buffer.
                Zero means no shuffling.
            batch_size: Batch size.
            **kwargs: Additional arguments passed to SpiralDataLoader constructor.

        Returns:
            SpiralDataLoader with shuffled shards.
        """
        from spiral.dataloader import SpiralDataLoader

        return SpiralDataLoader(
            self, seed=seed, shuffle_buffer_size=shuffle_buffer_size, batch_size=batch_size, **kwargs
        )

    def to_distributed_data_loader(
        self,
        world: "World | None" = None,
        shards: list[Shard] | None = None,
        seed: int = 42,
        shuffle_buffer_size: int = 0,
        batch_size: int = 32,
        **kwargs,
    ) -> "SpiralDataLoader":
        """Read into a Torch-compatible DataLoader for distributed training.

        Args:
            world: World configuration with rank and world_size.
                If None, auto-detects from torch.distributed.
            shards: Optional sharding. Sharding is global, i.e. the world will be used to select
                the shards for this rank. If None, uses scan's natural sharding.
            seed: Random seed for reproducibility.
            shuffle_buffer_size: Size of shuffle buffer.
                Zero means no shuffling.
            batch_size: Batch size.
            **kwargs: Additional arguments passed to SpiralDataLoader constructor.

        Returns:
            SpiralDataLoader with shards partitioned for this rank.

        Auto-detect from PyTorch distributed:

        ```python
        import spiral
        from spiral.dataloader import SpiralDataLoader, World
        from spiral.demo import fineweb

        sp = spiral.Spiral()
        fineweb_table = fineweb(sp)

        scan = sp.scan(fineweb_table[["text"]])

        loader: SpiralDataLoader = scan.to_distributed_data_loader(batch_size=32)
        ```

        Explicit world configuration:
        ```python
        world = World(rank=0, world_size=4)
        loader: SpiralDataLoader = scan.to_distributed_data_loader(world=world, batch_size=32)
        ```
        """
        from spiral.dataloader import SpiralDataLoader, World

        if self.limit is not None:
            warnings.warn(
                f"Scan has limit={self.limit} set. In distributed execution, the limit will be "
                "applied to each worker independently, not globally. This may return more rows "
                "than the specified limit.",
                stacklevel=2,
            )

        if world is None:
            world = World.from_torch()

        shards = shards or self.shards()
        # Apply world partitioning to shards.
        shards = world.shards(shards, seed)

        return SpiralDataLoader(
            self,
            shards=shards,
            shuffle_shards=False,  # Shards are shuffled before selected for the world.
            seed=seed,
            shuffle_buffer_size=shuffle_buffer_size,
            batch_size=batch_size,
            **kwargs,
        )

    def resume_data_loader(self, state: dict[str, Any], **kwargs) -> "SpiralDataLoader":
        """Create a DataLoader from checkpoint state, resuming from where it left off.

        This is the recommended way to resume training from a checkpoint. It extracts
        the seed, samples_yielded, and shards from the state dict and creates a new
        DataLoader that will skip the already-processed samples.

        Args:
            state: Checkpoint state from state_dict().
            **kwargs: Additional arguments to pass to SpiralDataLoader constructor.
                These will override values in the state dict where applicable.

        Returns:
            New SpiralDataLoader instance configured to resume from the checkpoint.

        Save checkpoint during training:

        ```python
        import spiral
        from spiral.dataloader import SpiralDataLoader, World
        from spiral.demo import images, fineweb

        sp = spiral.Spiral()
        table = images(sp)
        fineweb_table = fineweb(sp)

        scan = sp.scan(fineweb_table[["text"]])

        loader = scan.to_distributed_data_loader(batch_size=32, seed=42)
        checkpoint = loader.state_dict()
        ```

        Resume later - uses same shards from checkpoint:

        ```python
        resumed_loader = scan.resume_data_loader(
            checkpoint,
            batch_size=32,
            # An optional transform_fn may be provided:
            # transform_fn=my_transform,
        )
        ```
        """
        from spiral.dataloader import SpiralDataLoader

        return SpiralDataLoader.from_state_dict(self, state, **kwargs)

    def to_iterable_dataset(
        self,
        shards: list[Shard] | None = None,
        shuffle: ShuffleConfig | None = None,
        batch_readahead: int | None = None,
        infinite: bool = False,
    ) -> "hf.IterableDataset":
        """Returns a Huggingface's IterableDataset.

        Requires `datasets` package to be installed.

        Note: For new code, consider using SpiralDataLoader instead.

        Args:
            shards: Optional list of shards to read. If None, uses scan's natural sharding.
            shuffle: Optional ShuffleConfig for configuring within-shard sample shuffling.
                If None, no shuffling is performed.
            batch_readahead: Controls how many batches to read ahead concurrently.
                If pipeline includes work after reading (e.g. decoding, transforming, ...) this can be set higher.
                Otherwise, it should be kept low to reduce next batch latency.
                Defaults to min(number of CPU cores, 64) or to shuffle.buffer_size/16 if shuffle is not None.
            infinite: If True, the returned IterableDataset will loop infinitely over the data,
                re-shuffling ranges after exhausting all data.
        """
        stream = self.core.to_shuffled_record_batches(
            shards=shards,
            shuffle=shuffle,
            batch_readahead=batch_readahead,
            infinite=infinite,
        )

        from spiral.huggingface import to_iterable_dataset

        return to_iterable_dataset(stream)

    def shards(self) -> list[Shard]:
        """Get list of shards for this scan.

        The shards are based on the scan's physical data layout (file fragments).
        Each shard contains a key range and cardinality (set to None when unknown).

        Returns:
            List of Shard objects with key range and cardinality (if known).

        """
        return self.core.shards()

    def state_bytes(self) -> bytes:
        """Get the scan state as bytes.

        This state can be used to resume the scan later using Spiral.resume_scan().

        Returns:
            Compressed bytes representing the internal scan state.
        """
        return self.core.plan_context().to_bytes_compressed()

    def __getstate__(self) -> bytes:
        """Serialize scan for pickling.

        Enables seamless integration with distributed systems like Ray, Dask, and
        Python's multiprocessing without requiring manual serialization.

        Returns:
            Zstd-compressed bytes containing JSON-serialized config and scan state.
        """
        import orjson
        import zstandard as zstd

        state = {
            "config": self.spiral.config.to_json(),
            "overrides": self.spiral._overrides,
            "context": self.core.plan_context().to_json(),
        }
        json_bytes = orjson.dumps(state)
        return zstd.compress(json_bytes)

    def __setstate__(self, state: bytes) -> None:
        """Deserialize scan from pickled state.

        Args:
            state: Zstd-compressed bytes from __getstate__.
        """
        import orjson
        import zstandard as zstd

        from spiral import Spiral
        from spiral.core.config import ClientSettings
        from spiral.core.table import ScanContext

        json_bytes = zstd.decompress(state)
        data = orjson.loads(json_bytes)

        config = ClientSettings.from_json(data["config"])
        self.spiral = Spiral(config=config, overrides=data["overrides"])

        context = ScanContext.from_json(data["context"])
        self.core = self.spiral.core.load_scan(context)

    def _debug(self):
        # Visualizes the scan, mainly for debugging purposes.
        from spiral.debug.scan import show_scan

        show_scan(self.core)

    def _dump_metrics(self):
        # Print metrics in a human-readable format.
        from spiral.debug.metrics import display_metrics

        display_metrics(self.metrics)


# NOTE(marko): This function must be picklable!
def _read_shard_task(
    shard: Shard,
    *,
    config_json: str,
    state_bytes: bytes,
    key_table: TableLike = None,
    batch_readahead: int | None = None,
    hide_progress_bar: bool | None = None,
) -> pa.Table:
    """Worker function to read a single shard as Arrow table.

    Args:
        shard: The shard to read
        config_json: Serialized ClientSettings
        state_bytes: Serialized scan state
        key_table: a table of keys to "take" (including aux columns for cell-push-down).
            If None, the scan will be executed without a key table.
        batch_readahead: the number of batches to prefetch in the background.
        hide_progress_bar: If True, disables the progress bar during reading.

    Returns:
        PyArrow Table containing the shard data
    """
    from spiral import Spiral
    from spiral.settings import ClientSettings

    config = ClientSettings.from_json(config_json)
    sp = Spiral(config=config)
    task_scan = sp.resume_scan(state_bytes)

    return task_scan.to_table(
        shards=[shard],
        key_table=key_table,
        hide_progress_bar=hide_progress_bar,
    )
