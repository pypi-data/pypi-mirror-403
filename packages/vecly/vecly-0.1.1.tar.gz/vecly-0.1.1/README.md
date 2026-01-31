# vecly

Lightweight, NumPy-backed building blocks for quick finance/research workflows.

`vecly` provides three small primitives:

- **`Vector`**: a thin wrapper around `numpy.ndarray` with operator overloading and basic stats.
- **`Column`**: a named 1D series-like object built on `Vector`.
- **`DataFrame`**: a minimal column container for quick prototyping and feature workflows.

The goal is **fast iteration**: get just enough structure for experiments (ML/finance/research) without pulling in a full dataframe framework.

## Install

From PyPI:

```bash
python -m pip install vecly
```

For local development:

```bash
python -m pip install -e .
```

## Quickstart

```python
import numpy as np
from vecly import Vector, Column, DataFrame

# Vector: NumPy-friendly wrapper
v = Vector([1, 2, 3])
print(v + 2)          # Vector([3 4 5])
print(v.mean())       # 2.0
print(np.log(v))      # works via NumPy interop

# Column: named vector
price = Column("price", [100, 101, 103, 102])

# Simple feature workflow (returns -> log-returns)
ret = price / price.shift(1) - 1
log_ret = ret.log()

df = DataFrame([price])
df.append(Column("ret", ret))
df.append(Column("log_ret", log_ret))

print(df)             # pretty preview
print(df["price"])    # -> 1D np.ndarray
print(df[["ret", "log_ret"]])  # -> 2D np.ndarray (n_rows, 2)
```

## Core API

### `Vector`

- **Construction**: `Vector(data)`
- **Underlying array**: `v.data` or `v.to_numpy()`
- **Math**: `+ - * / **` (elementwise; supports scalars, array-likes, other `Vector`)
- **Stats**: `v.sum()`, `v.mean()`, `v.var()`, `v.std()`
- **Transforms**:
  - `v.log()` → returns a new `Vector`
  - `v.shift(n=1, fill_value=np.nan)` → returns a new `Vector`
- **NumPy interop**:
  - `np.asarray(v)`, `np.log(v)`, `np.column_stack([v1, v2])`, etc.

### `Column`

- **Construction**: `Column(name, x)` where `x` can be list/ndarray/`Vector`
- **Name**: `col.name`
- **Data**: `col.vec` (`Vector`) or `col.to_numpy()` (`np.ndarray`)
- **Transforms**:
  - `col.shift(n=1)` → `Vector`
  - `col.log()` → `Vector`
- **Elementwise math**:
  - `col / other` (where `other` can be `Column`, `Vector`, scalar, array-like) → `Vector`

### `DataFrame`

`DataFrame` is intentionally minimal: it stores a list of `Column` objects.

- **Construction**: `DataFrame([Column(...), ...])`
- **Append/replace column**: `df.append(col)` (replaces if same `col.name`)
- **Add from raw data**: `df.add_col(name, data)`
- **Select**:
  - `df["x"]` → 1D `np.ndarray`
  - `df[["x", "y"]]` → 2D `np.ndarray` shaped `(n_rows, 2)`

## License

MIT. See `LICENSE`.
