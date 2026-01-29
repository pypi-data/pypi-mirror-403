"""Core column reordering logic - pure list manipulation, no DataFrame ops."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


@dataclass
class Between:
    """Marker for column range (inclusive)."""
    start: str
    end: str


def between(start: str, end: str) -> Between:
    """
    Select columns from start to end (inclusive).
    
    Parameters
    ----------
    start : str
        First column in range.
    end : str
        Last column in range.
    
    Returns
    -------
    Between
        Marker object to be expanded by relocate().
    
    Examples
    --------
    >>> df.relocate(between("Q1_1", "Q1_5"))
    >>> df.relocate(between("Age", "Income"), after="id")
    """
    return Between(start, end)


def expand_between(b: Between, columns: list[str]) -> list[str]:
    """
    Expand Between marker to list of columns.
    
    Validates:
    - Both start and end columns exist
    - Start column comes before or equals end column
    """
    col_set = set(columns)
    
    if b.start not in col_set:
        raise ValueError(f"Start column '{b.start}' not found")
    if b.end not in col_set:
        raise ValueError(f"End column '{b.end}' not found")
    
    start_idx = columns.index(b.start)
    end_idx = columns.index(b.end)
    
    if start_idx > end_idx:
        raise ValueError(
            f"Start column '{b.start}' (index {start_idx}) "
            f"must come before end column '{b.end}' (index {end_idx})"
        )
    
    return columns[start_idx:end_idx + 1]


def calculate_column_order(
    columns: list[str],
    cols_to_move: list[str],
    after: str | None = None,
    to: Literal["first", "last"] | None = None,
) -> list[str]:
    """
    Calculate new column order based on positioning specification.
    
    Parameters
    ----------
    columns : list[str]
        Current column order.
    cols_to_move : list[str]
        Column(s) to relocate. Already expanded (no slice notation).
    after : str, optional
        Anchor column - place cols_to_move after this column.
    to : {"first", "last"}, optional
        Position shortcut. Default behavior (None) is "first".
    
    Returns
    -------
    list[str]
        New column order.
    
    Raises
    ------
    ValueError
        If columns don't exist or invalid arguments.
    """
    col_set = set(columns)
    move_set = set(cols_to_move)
    
    # Validate columns to move exist
    for c in cols_to_move:
        if c not in col_set:
            raise ValueError(f"Column '{c}' not found")
    
    # Validate anchor exists
    if after is not None and after not in col_set:
        raise ValueError(f"Anchor column '{after}' not found")
    
    # Get remaining columns (preserving original order)
    remaining = [c for c in columns if c not in move_set]
    
    # Position: after anchor
    if after is not None:
        anchor_idx = remaining.index(after)
        return remaining[:anchor_idx + 1] + cols_to_move + remaining[anchor_idx + 1:]
    
    # Position: last
    if to == "last":
        return remaining + cols_to_move
    
    # Position: first (default)
    return cols_to_move + remaining
