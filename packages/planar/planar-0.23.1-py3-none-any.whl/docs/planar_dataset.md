# PlanarDataset

## Overview

PlanarDataset is a lightweight reference to a Ducklake-backed table. It lets
you persist tabular data between steps without passing large payloads around.
You create a named dataset, write data to it, and read it later from other
steps using a small, serializable reference.

## Quick Start

```python
from planar.data import PlanarDataset
from planar.workflows import step
import polars as pl

@step()
async def load_transactions(csv_path: str) -> PlanarDataset:
    df = pl.read_csv(csv_path)
    dataset = await PlanarDataset.create("transactions_2024_07")
    await dataset.write(df, mode="overwrite")
    return dataset

@step()
async def load_transactions_lazy(csv_path: str) -> PlanarDataset:
    # Use LazyFrame for better performance and to avoid blocking the event loop
    lf = pl.scan_csv(csv_path).with_columns(
        pl.col("amount").cast(pl.Float64),
        pl.col("date").str.to_date()
    )
    dataset = await PlanarDataset.create("transactions_2024_07")
    await dataset.write(lf, mode="overwrite")
    return dataset

@step()
async def aggregate_transactions(transactions: PlanarDataset) -> PlanarDataset:
    df = await transactions.to_polars()
    aggregated = df.group_by("merchant_id").sum()
    output = await PlanarDataset.create("merchant_aggregates")
    await output.write(aggregated, mode="overwrite")
    return output
```

## API Reference

- Class: PlanarDataset
  - name: str — dataset (table) name in Ducklake

- Classmethod `create(name: str, if_not_exists: bool = True) -> PlanarDataset`
  - Creates a dataset reference. The physical table is created on first write.
  - Raises `DatasetAlreadyExistsError` when the dataset exists and
    `if_not_exists` is False.

- `exists() -> bool`
  - Checks whether the dataset table exists.

- `write(data, mode: Literal["overwrite", "append"] = "append") -> None`
  - Writes data to the dataset. Creates the table if it does not exist.
  - Supported `data` types:
    - `polars.DataFrame`
    - `polars.LazyFrame`
    - `pyarrow.Table`
    - `ibis.Table`
    - Row-like Python data: `list[dict]` or `dict[str, list]`
  - Modes:
    - `overwrite`: replaces existing rows
    - `append`: adds rows to the existing table
  - Raises `DataError` on failures.

- `read(columns: list[str] | None = None, limit: int | None = None) -> ibis.Table`
  - Returns an `ibis.Table` for further filtering/aggregation.
  - Optional column projection and row limit.
  - Raises `DatasetNotFoundError` if the dataset does not exist.

- `to_polars() -> polars.DataFrame`
  - Reads the entire dataset into a Polars DataFrame.

- `to_pyarrow() -> pyarrow.Table`
  - Reads the entire dataset into a PyArrow Table.

- `delete() -> None`
  - Drops the dataset table. Raises `DataError` on failures.

## Behavior and Notes

- Reference semantics: steps pass around a compact reference, not the data.
- Lazy creation: the underlying table is created on the first successful write.
- Async-first: all operations are `async` to avoid blocking the event loop.
- Errors: operations raise `DataError`, `DatasetAlreadyExistsError`, or
  `DatasetNotFoundError` for common cases.
- Blocking operations: when doing CPU-bound or blocking work in steps
  (for example, Polars file IO or heavy transforms), wrap the call with
  `asyncio.to_thread`, or use the `@asyncify` decorator / `asyncify()` helper
  from `planar.utils`, to keep the event loop responsive.

```python
from asyncio import to_thread
import polars as pl

@step()
async def ingest_fast(csv_path: str) -> PlanarDataset:
    # Run blocking CSV parse off the event loop
    df = await to_thread(pl.read_csv, csv_path)
    ds = await PlanarDataset.create("raw_transactions")
    await ds.write(df, mode="overwrite")
    return ds
```

Alternatively, you can use the `asyncify` helper to convert a synchronous
function into an async one:

```python
from planar.utils import asyncify
import polars as pl

# Wrap a sync function as async
read_csv_async = asyncify(pl.read_csv)

@step()
async def ingest_fast(csv_path: str) -> PlanarDataset:
    df = await read_csv_async(csv_path)
    ds = await PlanarDataset.create("raw_transactions")
    await ds.write(df, mode="overwrite")
    return ds
```

## Configuration

PlanarDataset uses the app's `data` configuration to connect to Ducklake. In a
local dev setup, a typical configuration looks like this:

```yaml
data:
  catalog:
    type: duckdb
    path: .data/catalog.ducklake
  catalog_name: planar_data
  storage:
    backend: localdir
    directory: .data/ducklake_files
```

Other supported catalogs include `postgres` and `sqlite`; storage backends
include `localdir` and `s3`. Ensure `app.config.data` is set or data operations
will raise `DataError`.

## Examples

### Ingest and Clean

```python
from planar.workflows import step
import polars as pl

@step()
async def ingest_csv_to_dataset(csv_path: str) -> PlanarDataset:
    df = pl.read_csv(csv_path)
    dataset = await PlanarDataset.create("raw_transactions")
    await dataset.write(df, mode="overwrite")
    return dataset

@step()
async def clean_transactions(raw: PlanarDataset) -> PlanarDataset:
    df = await raw.to_polars()
    cleaned = df.filter(pl.col("amount") > 0).drop_nulls()
    output = await PlanarDataset.create("cleaned_transactions")
    await output.write(cleaned, mode="overwrite")
    return output
```

### Read with Ibis Filters

```python
from typing import Dict
from planar.workflows import step

@step()
async def analyze_high_value_transactions(transactions: PlanarDataset) -> Dict[str, float]:
    table = await transactions.read()
    high_value = table.filter(table.amount > 1000)
    summary = high_value.group_by("merchant_id").agg(
        total=high_value.amount.sum(),
        count=high_value.amount.count(),
    )
    result = summary.to_polars()
    return result.to_dict()
```

### Error Handling

```python
from typing import Optional
import polars as pl

@step()
async def safe_read_dataset(dataset_name: str) -> Optional[pl.DataFrame]:
    try:
        dataset = PlanarDataset(name=dataset_name)
        if not await dataset.exists():
            return None
        return await dataset.to_polars()
    except DatasetNotFoundError:
        logger.error("dataset not found", dataset_name=dataset_name)
        return None
    except DataError:
        logger.exception("failed to read dataset", dataset_name=dataset_name)
        raise
```

## Limitations

- No explicit snapshot/time-travel selection yet.
- No partitioning controls; write/append semantics are table-wide.


## Planned Features

- Snapshot versioning support
- Partition column support
- Schema evolution capabilities
- Data lineage tracking (e.g., set metadata on snapshot version during write)
- Data validation and quality checks
- Data transformation utilities (e.g., `@model` decorator)
