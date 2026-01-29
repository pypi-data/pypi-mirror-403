"""
colocate - DataFrame column reordering made simple.

Just import to register df.relocate() on pandas and polars DataFrames.
Also registers pl.between() for column range selection.

Usage
-----
>>> import polars as pl
>>> import colocate  # Registers df.relocate() and pl.between()
>>> 
>>> df = pl.DataFrame({
...     "age": [25, 30],
...     "city": ["NYC", "LA"],
...     "id": [1, 2],
...     "name": ["Alice", "Bob"],
... })
>>> 
>>> df.relocate("id")                          # → first (default)
>>> df.relocate(["id", "name"])                # multiple → first
>>> df.relocate("score", to="last")            # → last
>>> df.relocate("name", after="id")            # → after anchor
>>> df.relocate(pl.between("Q1_1", "Q1_5"))    # range → first
"""

import importlib.util

from colocate.core import Between, between, calculate_column_order


if importlib.util.find_spec("pandas") is not None:
    import colocate.pandas  # noqa: F401

if importlib.util.find_spec("polars") is not None:
    import colocate.polars  # noqa: F401


from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("colocate")
except PackageNotFoundError:
    __version__ = "0.0.0"  # fallback for editable/dev installs

__all__ = [
    "between",
    "Between",
    "calculate_column_order",
]
