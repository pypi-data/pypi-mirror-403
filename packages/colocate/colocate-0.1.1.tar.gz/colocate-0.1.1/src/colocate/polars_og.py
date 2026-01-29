"""Polars DataFrame namespace registration."""

from __future__ import annotations
from typing import Literal, TYPE_CHECKING

import polars as pl
import polars.selectors as cs

from colocate.core import Between, between, expand_between, calculate_column_order

if TYPE_CHECKING:
    from polars._typing import SelectorType


# Register pl.between for convenient access (no separate import needed)
pl.between = between


class PolarsRelocateAccessor:
    """
    Polars DataFrame/LazyFrame accessor for column relocation.
    
    Supports polars selectors in addition to column names.
    """
    
    def __init__(self, obj):
        self._obj = obj
    
    def __call__(
        self,
        columns: str | list[str] | Between | SelectorType,
        after: str | None = None,
        to: Literal["first", "last"] | None = None,
    ):
        """
        Relocate columns in the DataFrame.
        
        Parameters
        ----------
        columns : str, list[str], Between, or Selector
            Column(s) to move. Supports:
            - Column name: "id"
            - List of names: ["id", "name"]
            - Range: pl.between("Q1_1", "Q1_5")
            - Selectors: cs.numeric(), cs.last(), cs.matches("^Q1_")
        after : str, optional
            Anchor column - place columns after this column.
        to : {"first", "last"}, optional
            Position shortcut. Default (None) moves to first.
        
        Returns
        -------
        DataFrame or LazyFrame
            Same type as input with reordered columns.
        
        Examples
        --------
        >>> import polars.selectors as cs
        >>> df.relocate("id")                          # → first
        >>> df.relocate(cs.last(), after="id")         # last col after id
        >>> df.relocate(cs.numeric(), to="last")       # all numeric to end
        >>> df.relocate(cs.matches("^Q1_"))            # regex match → first
        >>> df.relocate(pl.between("Q1_1", "Q1_5"))    # range → first
        """
        if after is not None and to is not None:
            raise ValueError("Cannot specify both 'after' and 'to'")
        
        current_cols = self._obj.columns
        
        # Expand columns based on type
        if isinstance(columns, Between):
            cols_to_move = expand_between(columns, current_cols)
        elif cs.is_selector(columns):
            cols_to_move = list(cs.expand_selector(self._obj, columns))
        elif isinstance(columns, str):
            cols_to_move = [columns]
        else:
            cols_to_move = list(columns)
        
        # Validate: anchor cannot be inside the range being moved
        if after is not None and after in cols_to_move:
            raise ValueError(
                f"Anchor column '{after}' cannot be inside the columns being moved"
            )
        
        # Calculate new order
        new_order = calculate_column_order(current_cols, cols_to_move, after, to)
        
        return self._obj.select(new_order)


@pl.api.register_dataframe_namespace("relocate")
class DataFrameRelocateAccessor(PolarsRelocateAccessor):
    """Polars DataFrame accessor for column relocation."""


@pl.api.register_lazyframe_namespace("relocate")
class LazyFrameRelocateAccessor(PolarsRelocateAccessor):
    """Polars LazyFrame accessor for column relocation."""
