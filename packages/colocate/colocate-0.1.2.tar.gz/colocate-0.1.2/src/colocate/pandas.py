"""Pandas DataFrame accessor registration."""

import pandas as pd

from colocate.extension import BaseRelocateAccessor


@pd.api.extensions.register_dataframe_accessor("relocate")
class RelocateAccessor(BaseRelocateAccessor):
    """
    Pandas DataFrame accessor for column relocation.
    
    Examples
    --------
    >>> import pandas as pd
    >>> import colocate  # noqa: F401
    >>> 
    >>> df = pd.DataFrame({
    ...     "age": [25, 30],
    ...     "id": [1, 2],
    ...     "name": ["Alice", "Bob"],
    ... })
    >>> 
    >>> df.relocate(first=["id", "name"])
    """
