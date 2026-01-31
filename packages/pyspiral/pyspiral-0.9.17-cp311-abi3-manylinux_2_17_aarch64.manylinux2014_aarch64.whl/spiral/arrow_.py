from functools import reduce
from typing import TypeVar

import pyarrow as pa
from pyarrow import compute as pc

T = TypeVar("T")


def flatten_struct_table(table: pa.Table, separator=".") -> pa.Table:
    """Turn a nested struct table into a flat table with dot-separated names."""
    data = []
    names = []

    def _unfold(array: pa.Array, prefix: str):
        if pa.types.is_struct(array.type):
            if isinstance(array, pa.ChunkedArray):
                array = array.combine_chunks()
            for f in array.type:
                _unfold(array.field(f.name), f"{prefix}{separator}{f.name}")
        else:
            data.append(array)
            names.append(prefix)

    for col in table.column_names:
        _unfold(table[col], col)

    return pa.Table.from_arrays(data, names=names)


def struct_array(fields: list[tuple[str, bool, pa.Array]], /, mask: list[bool] | None = None) -> pa.StructArray:
    """Helper to create struct arrays from field definitions."""
    return pa.StructArray.from_arrays(
        arrays=[x[2] for x in fields],
        fields=[pa.field(x[0], type=x[2].type, nullable=x[1]) for x in fields],
        mask=pa.array(mask) if mask else mask,
    )


def table(fields: list[tuple[str, bool, pa.Array]], /) -> pa.Table:
    return pa.Table.from_struct_array(struct_array(fields))


def dict_to_struct_array(data: dict[str, dict | pa.Array], propagate_nulls: bool = False) -> pa.StructArray:
    """Convert a nested dictionary of arrays to a table with nested structs."""
    arrays = [value if not isinstance(value, dict) else dict_to_struct_array(value) for value in data.values()]
    return pa.StructArray.from_arrays(
        arrays,
        names=list(data.keys()),
        mask=reduce(pc.and_, [pc.is_null(array) for array in arrays]) if propagate_nulls else None,
    )
