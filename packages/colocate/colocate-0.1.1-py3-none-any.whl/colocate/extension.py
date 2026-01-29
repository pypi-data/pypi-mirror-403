"""Base accessor class using narwhals for DataFrame-agnostic operations."""

from __future__ import annotations
from typing import Literal

import narwhals as nw

from colocate.core import Between, calculate_column_order, expand_between


class BaseRelocateAccessor:
    """Base class for relocate accessor - works with any narwhals-supported DataFrame."""
    
    def __init__(self, obj):
        self._obj = obj
    
    def __call__(
        self,
        columns: str | list[str] | Between,
        after: str | None = None,
        to: Literal["first", "last"] | None = None,
    ):
        """
        Relocate columns in the DataFrame.
        
        Parameters
        ----------
        columns : str, list[str], or Between
            Column(s) to move. Use between("start", "end") for ranges.
        after : str, optional
            Anchor column - place columns after this column.
        to : {"first", "last"}, optional
            Position shortcut. Default (None) moves to first.
        
        Returns
        -------
        DataFrame
            Same type as input with reordered columns.
        
        Raises
        ------
        ValueError
            If both `after` and `to` are specified, or columns not found,
            or anchor is inside a between() range.
        
        Examples
        --------
        >>> df.relocate("id")                          # → first (default)
        >>> df.relocate(["id", "name"])                # multiple → first
        >>> df.relocate("score", to="last")           # → last
        >>> df.relocate(["age", "gender"], after="id") # → after id
        >>> df.relocate(between("Q1_1", "Q1_5"))      # range → first
        >>> df.relocate(between("Q1_1", "Q1_5"), after="uuid")
        
        Chain for complex reordering:
        >>> df.relocate("id").relocate("score", to="last")
        """
        # Validate: can't specify both after and to
        if after is not None and to is not None:
            raise ValueError("Cannot specify both 'after' and 'to'")
        
        frame = nw.from_native(self._obj)
        current_cols = frame.columns
        
        # Expand columns based on type
        if isinstance(columns, Between):
            cols_to_move = expand_between(columns, current_cols)
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
        
        return frame.select(new_order).to_native()
