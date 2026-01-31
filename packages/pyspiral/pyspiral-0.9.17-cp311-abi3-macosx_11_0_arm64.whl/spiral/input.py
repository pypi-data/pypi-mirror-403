import builtins
from typing import TYPE_CHECKING, TypeAlias, Union

import pyarrow as pa

from spiral import arrow_

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd
    import polars as pl

ArrayLike: TypeAlias = Union[pa.Array, pa.ChunkedArray, builtins.list, "np.ndarray", "pd.Series"]
TableLike: TypeAlias = Union[
    pa.Table,
    pa.RecordBatch,
    pa.RecordBatchReader,
    pa.StructArray,
    pa.ChunkedArray,  # must be of struct type
    builtins.list[dict],  # list of objects, each element is a row
    dict[str, ArrayLike],  # dot-separated field names are nested
    "pd.DataFrame",
    "pl.DataFrame",
]
LazyTableLike: TypeAlias = Union[
    TableLike,
    "pl.LazyFrame",
]


def evaluate(table: TableLike) -> pa.RecordBatchReader:
    if isinstance(table, pa.RecordBatchReader):
        return table

    if isinstance(table, pa.Table):
        return table.to_reader()
    if isinstance(table, pa.RecordBatch):
        return pa.RecordBatchReader.from_batches(table.schema, [table])

    if isinstance(table, pa.StructArray):
        return pa.Table.from_struct_array(table).to_reader()
    if isinstance(table, pa.ChunkedArray):
        if not pa.types.is_struct(table.type):
            raise ValueError(f"Arrow ChunkedArray must have a struct type, got {table.type}.")
        struct_type: pa.StructType = table.type  # type: ignore[assignment]

        def _iter_batches():
            for chunk in table.chunks:
                chunk: pa.StructArray
                yield pa.RecordBatch.from_struct_array(chunk)

        return pa.RecordBatchReader.from_batches(pa.schema(struct_type.fields), _iter_batches())
    if isinstance(table, pa.Array):
        raise ValueError(f"Arrow Array must be a struct array, got {type(table)}.")

    if isinstance(table, builtins.list):
        # Handle empty array case
        if len(table) == 0:
            return pa.RecordBatchReader.from_batches(pa.schema([]), [])
        return evaluate(pa.array(table))

    if isinstance(table, dict):
        table: dict = dot_separated_dict_to_nested(table)

        return evaluate(_evaluate_dict(table))

    try:
        import pandas as pd

        if isinstance(table, pd.DataFrame):
            return evaluate(pa.Table.from_pandas(table))
    except ImportError:
        pass

    try:
        import polars as pl

        if isinstance(table, pl.DataFrame):
            return evaluate(table.to_arrow())
    except ImportError:
        pass

    raise TypeError(f"Unsupported table-like type: {type(table)}")


def _evaluate_dict(table: dict) -> pa.StructArray:
    """Handle dot-separated field names as nested dictionaries."""
    table = dot_separated_dict_to_nested(table)
    return _dict_to_struct_array(table)


def _dict_to_struct_array(table) -> pa.StructArray:
    data = {}
    for key, value in table.items():
        data[key] = _evaluate_array_like(value) if not isinstance(value, dict) else _dict_to_struct_array(value)
    return arrow_.dict_to_struct_array(data)


def _evaluate_array_like(array: ArrayLike) -> pa.Array:
    if isinstance(array, pa.Array):
        return array
    if isinstance(array, pa.ChunkedArray):
        return array.combine_chunks()

    if isinstance(array, builtins.list):
        return _evaluate_array_like(pa.array(array))

    try:
        import numpy as np

        if isinstance(array, np.ndarray):
            return _evaluate_array_like(pa.array(array))
    except ImportError:
        pass

    try:
        import pandas as pd

        if isinstance(array, pd.Series):
            return _evaluate_array_like(pa.Array.from_pandas(array))
    except ImportError:
        pass

    raise TypeError(f"Unsupported array-like type: {type(array)}")


def dot_separated_dict_to_nested(expr: dict) -> dict:
    """Handle dot-separated field names as nested dictionaries."""
    data = {}

    for name in expr.keys():
        if "." not in name:
            if name in data:
                raise KeyError(f"Conflicting field name: {name}")
            data[name] = expr[name]
            continue

        parts = name.split(".")
        child_data = data
        for part in parts[:-1]:
            if part not in child_data:
                child_data[part] = {}
            if not isinstance(child_data[part], dict):
                raise KeyError(f"Conflicting field name: {name}")
            child_data = child_data[part]

        if parts[-1] in child_data:
            raise KeyError(f"Conflicting field name: {name}")
        child_data[parts[-1]] = expr[name]

    return data
