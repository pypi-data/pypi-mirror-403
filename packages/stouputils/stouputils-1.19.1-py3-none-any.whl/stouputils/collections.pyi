import polars as pl
import zarr
from collections.abc import Callable as Callable, Iterable
from numpy.typing import NDArray as NDArray
from typing import Any, Literal

def unique_list[T](list_to_clean: Iterable[T], method: Literal['id', 'hash', 'str'] = 'str') -> list[T]:
    ''' Remove duplicates from the list while keeping the order using ids, hash, or str

\tArgs:
\t\tlist_to_clean\t(Iterable[T]):\t\t\t\t\tThe list to clean
\t\tmethod\t\t\t(Literal["id", "hash", "str"]):\tThe method to use to identify duplicates
\tReturns:
\t\tlist[T]: The cleaned list

\tExamples:
\t\t>>> unique_list([1, 2, 3, 2, 1], method="id")
\t\t[1, 2, 3]

\t\t>>> s1 = {1, 2, 3}
\t\t>>> s2 = {2, 3, 4}
\t\t>>> s3 = {1, 2, 3}
\t\t>>> unique_list([s1, s2, s1, s1, s3, s2, s3], method="id")
\t\t[{1, 2, 3}, {2, 3, 4}, {1, 2, 3}]

\t\t>>> s1 = {1, 2, 3}
\t\t>>> s2 = {2, 3, 4}
\t\t>>> s3 = {1, 2, 3}
\t\t>>> unique_list([s1, s2, s1, s1, s3, s2, s3], method="str")
\t\t[{1, 2, 3}, {2, 3, 4}]
\t'''
def at_least_n[T](iterable: Iterable[T], predicate: Callable[[T], bool], n: int) -> bool:
    """ Return True if at least n elements in iterable satisfy predicate.
\tIt's like the built-in any() but for at least n matches.

\tStops iterating as soon as n matches are found (short-circuit evaluation).

\tArgs:
\t\titerable\t(Iterable[T]):\t\t\tThe iterable to check.
\t\tpredicate\t(Callable[[T], bool]):\tThe predicate to apply to items.
\t\tn\t\t\t(int):\t\t\t\t\tMinimum number of matches required.

\tReturns:
\t\tbool: True if at least n elements satisfy predicate, otherwise False.

\tExamples:
\t\t>>> at_least_n([1, 2, 3, 4, *[i for i in range(5, int(1e5))]], lambda x: x % 2 == 0, 2)
\t\tTrue
\t\t>>> at_least_n([1, 3, 5, 7], lambda x: x % 2 == 0, 1)
\t\tFalse
\t"""
def sort_dict_keys[T](dictionary: dict[T, Any], order: list[T], reverse: bool = False) -> dict[T, Any]:
    ''' Sort dictionary keys using a given order list (reverse optional)

\tArgs:
\t\tdictionary\t(dict[T, Any]):\tThe dictionary to sort
\t\torder\t\t(list[T]):\t\tThe order list
\t\treverse\t\t(bool):\t\t\tWhether to sort in reverse order (given to sorted function which behaves differently than order.reverse())
\tReturns:
\t\tdict[T, Any]: The sorted dictionary

\tExamples:
\t\t>>> sort_dict_keys({\'b\': 2, \'a\': 1, \'c\': 3}, order=["a", "b", "c"])
\t\t{\'a\': 1, \'b\': 2, \'c\': 3}

\t\t>>> sort_dict_keys({\'b\': 2, \'a\': 1, \'c\': 3}, order=["a", "b", "c"], reverse=True)
\t\t{\'c\': 3, \'b\': 2, \'a\': 1}

\t\t>>> sort_dict_keys({\'b\': 2, \'a\': 1, \'c\': 3, \'d\': 4}, order=["c", "b"])
\t\t{\'c\': 3, \'b\': 2, \'a\': 1, \'d\': 4}
\t'''
def upsert_in_dataframe(df: pl.DataFrame, new_entry: dict[str, Any], primary_keys: list[str] | dict[str, Any] | None = None) -> pl.DataFrame:
    ''' Insert or update a row in the Polars DataFrame based on primary keys.

\tArgs:
\t\tdf\t\t\t\t(pl.DataFrame):\t\tThe Polars DataFrame to update.
\t\tnew_entry\t\t(dict[str, Any]):\tThe new entry to insert or update.
\t\tprimary_keys\t(list[str] | dict[str, Any] | None):\tThe primary keys to identify the row (for updates).
\tReturns:
\t\tpl.DataFrame: The updated Polars DataFrame.
\tExamples:
\t\t>>> import polars as pl
\t\t>>> df = pl.DataFrame({"id": [1, 2], "value": ["a", "b"]})
\t\t>>> new_entry = {"id": 2, "value": "updated"}
\t\t>>> updated_df = upsert_in_dataframe(df, new_entry, primary_keys=["id"])
\t\t>>> print(updated_df)
\t\tshape: (2, 2)
\t\t┌─────┬─────────┐
\t\t│ id  ┆ value   │
\t\t│ --- ┆ ---     │
\t\t│ i64 ┆ str     │
\t\t╞═════╪═════════╡
\t\t│ 1   ┆ a       │
\t\t│ 2   ┆ updated │
\t\t└─────┴─────────┘

\t\t>>> new_entry = {"id": 3, "value": "new"}
\t\t>>> updated_df = upsert_in_dataframe(updated_df, new_entry, primary_keys=["id"])
\t\t>>> print(updated_df)
\t\tshape: (3, 2)
\t\t┌─────┬─────────┐
\t\t│ id  ┆ value   │
\t\t│ --- ┆ ---     │
\t\t│ i64 ┆ str     │
\t\t╞═════╪═════════╡
\t\t│ 1   ┆ a       │
\t\t│ 2   ┆ updated │
\t\t│ 3   ┆ new     │
\t\t└─────┴─────────┘
\t'''
def array_to_disk(data: NDArray[Any] | zarr.Array, delete_input: bool = True, more_data: NDArray[Any] | zarr.Array | None = None) -> tuple['zarr.Array', str, int]:
    """ Easily handle large numpy arrays on disk using zarr for efficient storage and access.

\tZarr provides a simpler and more efficient alternative to np.memmap with better compression
\tand chunking capabilities.

\tArgs:
\t\tdata\t\t\t(NDArray | zarr.Array):\tThe data to save/load as a zarr array
\t\tdelete_input\t(bool):\tWhether to delete the input data after creating the zarr array
\t\tmore_data\t\t(NDArray | zarr.Array | None): Additional data to append to the zarr array
\tReturns:
\t\ttuple[zarr.Array, str, int]: The zarr array, the directory path, and the total size in bytes

\tExamples:
\t\t>>> import numpy as np
\t\t>>> data = np.random.rand(1000, 1000)
\t\t>>> zarr_array = array_to_disk(data)[0]
\t\t>>> zarr_array.shape
\t\t(1000, 1000)

\t\t>>> more_data = np.random.rand(500, 1000)
\t\t>>> longer_array, dir_path, total_size = array_to_disk(zarr_array, more_data=more_data)
\t"""
