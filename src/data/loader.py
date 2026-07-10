"""Read the five raw tables into typed pandas DataFrames.

Callers should treat these functions as the single entry point into the data
layer. Two backends, selected by ``DATA_BACKEND`` in ``.env``:

- ``csv``   — reads ``data/raw/*.csv`` (original behaviour)
- ``mysql`` — reads the tables loaded by ``scripts/init_db.py``

Both return identically-shaped DataFrames, so nothing above this module cares.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import settings
from src.data.schema import (
    COST_COLUMNS,
    CUSTOMER_COLUMNS,
    DATE_COLUMNS,
    FX_COLUMNS,
    PRODUCT_COLUMNS,
    SALES_COLUMNS,
)

_TABLES = {
    "products": ("product_master", PRODUCT_COLUMNS, DATE_COLUMNS.get("products")),
    "customers": ("customer_master", CUSTOMER_COLUMNS, None),
    "sales": ("sales_transactions", SALES_COLUMNS, DATE_COLUMNS.get("sales")),
    "costs": ("cost_data", COST_COLUMNS, None),
    "fx": ("fx_rates", FX_COLUMNS, None),
}


def _read_csv(path: Path, dtypes: dict[str, str], parse_dates: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Expected raw file not found: {path}. "
            "Run `python scripts/generate_sample_data.py` first."
        )
    non_date_dtypes = {k: v for k, v in dtypes.items() if k not in (parse_dates or [])}
    df = pd.read_csv(path, dtype=non_date_dtypes, parse_dates=parse_dates or None)
    return df


def _read_mysql(table: str, dtypes: dict[str, str], parse_dates: list[str] | None = None) -> pd.DataFrame:
    from src.data.db import get_engine  # local import so csv mode needs no sqlalchemy

    df = pd.read_sql_table(table, get_engine(), parse_dates=parse_dates or None)
    # Coerce to the same dtypes the CSV path produces, so downstream code
    # sees one shape regardless of backend.
    for col, dtype in dtypes.items():
        if col in (parse_dates or []):
            continue
        df[col] = df[col].astype(dtype)
    return df[list(dtypes.keys())]


def _load(key: str, backend: str | None = None) -> pd.DataFrame:
    table, dtypes, parse_dates = _TABLES[key]
    backend = (backend or settings.DATA_BACKEND).lower()
    if backend == "mysql":
        return _read_mysql(table, dtypes, parse_dates)
    return _read_csv(settings.RAW_FILES[key], dtypes, parse_dates)


def load_products(backend: str | None = None) -> pd.DataFrame:
    return _load("products", backend)


def load_customers(backend: str | None = None) -> pd.DataFrame:
    return _load("customers", backend)


def load_sales(backend: str | None = None) -> pd.DataFrame:
    return _load("sales", backend)


def load_costs(backend: str | None = None) -> pd.DataFrame:
    return _load("costs", backend)


def load_fx(backend: str | None = None) -> pd.DataFrame:
    return _load("fx", backend)


def load_all(backend: str | None = None) -> dict[str, pd.DataFrame]:
    return {key: _load(key, backend) for key in _TABLES}
