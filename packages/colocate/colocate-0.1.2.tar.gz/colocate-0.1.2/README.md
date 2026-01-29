# colocate

DataFrame column reordering made simple. Works with pandas and polars.

## Installation

```bash
uv add colocate

or

pip install colocate
```

## Usage

Just import to register `df.relocate()`:

```python
import polars as pl
import colocate  # Registers df.relocate() and pl.between()

df = pl.DataFrame({
    "age": [25, 30, 35],
    "city": ["NYC", "LA", "Chicago"],
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "score": [85, 90, 78],
})
```

### Move to first (default)

```python
df.relocate("id")
# ['id', 'age', 'city', 'name', 'score']

df.relocate(["id", "name"])
# ['id', 'name', 'age', 'city', 'score']
```

### Move to last

```python
df.relocate("score", to="last")
# ['age', 'city', 'id', 'name', 'score']

df.relocate(["score", "age"], to="last")
# ['city', 'id', 'name', 'score', 'age']
```

### Move after anchor

```python
df.relocate("name", after="id")
# ['age', 'city', 'id', 'name', 'score']

df.relocate(["name", "age"], after="id")
# ['city', 'id', 'name', 'age', 'score']
```

### Chaining

For complex reordering, chain multiple calls:

```python
(df
    .relocate("id")
    .relocate("name", after="id")
    .relocate("score", to="last")
)
# ['id', 'name', 'age', 'city', 'score']
```

### Column Ranges with `pl.between()`

For sequential columns (common in survey data), use `pl.between()`:

```python
df = pl.DataFrame({
    "respondent_id": [1],
    "Q1_1": [1], "Q1_2": [2], "Q1_3": [3],
    "Q2_1": [4], "Q2_2": [5],
    "weight": [1.0],
})

df.relocate(pl.between("Q2_1", "Q2_2"))
# ['Q2_1', 'Q2_2', 'respondent_id', 'Q1_1', 'Q1_2', 'Q1_3', 'weight']

df.relocate(pl.between("Q2_1", "Q2_2"), after="respondent_id")
# ['respondent_id', 'Q2_1', 'Q2_2', 'Q1_1', 'Q1_2', 'Q1_3', 'weight']

df.relocate(pl.between("Q1_1", "Q1_3"), to="last")
# ['respondent_id', 'Q2_1', 'Q2_2', 'weight', 'Q1_1', 'Q1_2', 'Q1_3']
```

### Polars Selectors

Full support for [polars selectors](https://docs.pola.rs/api/python/stable/reference/selectors.html):

```python
import polars.selectors as cs

df.relocate(cs.last())                    # last column → first
df.relocate(cs.last(), after="id")        # last column → after id
df.relocate(cs.numeric(), to="last")      # all numeric → end
df.relocate(cs.string())                  # all string → first
df.relocate(cs.matches("^Q1_"))           # regex match → first
df.relocate(cs.starts_with("Q2"))         # prefix match → first
df.relocate(cs.by_name("score", "name"))  # specific cols → first
```

## Works with pandas too

```python
import pandas as pd
import colocate

df = pd.DataFrame({...})
df.relocate("id")
df.relocate(["score"], to="last")
df.relocate("name", after="id")
```

Note: `pl.between()` is polars-only. For pandas, use explicit column lists.

## API

```python
df.relocate(columns, after=None, to=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `columns` | `str \| list[str] \| Between` | Column(s) to move. Use `pl.between(start, end)` for ranges. |
| `after` | `str \| None` | Place columns after this anchor column. |
| `to` | `"first" \| "last" \| None` | Position shortcut. Default is `"first"`. |

**Note:** `after` and `to` are mutually exclusive.

```python
pl.between(start, end)  # Select columns from start to end (inclusive)
```

## How it works

Under the hood, `colocate` simply:

1. Computes the new column order (pure list manipulation)
2. Calls `df.select(new_order)` via [narwhals](https://narwhals-dev.github.io/narwhals/)

That's it. Clean and simple.

## License

MIT
