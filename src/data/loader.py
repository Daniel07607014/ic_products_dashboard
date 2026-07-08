"""Read the five raw CSVs into typed pandas DataFrames.

Callers should treat these functions as the single entry point into the data
layer. If we later switch from CSV to a database, only this module changes.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.settings import RAW_FILES
from src.data.schema import (
    COST_COLUMNS,
    CUSTOMER_COLUMNS,
    DATE_COLUMNS,
    FX_COLUMNS,
    PRODUCT_COLUMNS,
    SALES_COLUMNS,
)


def _read_csv(path: Path, dtypes: dict[str, str], parse_dates: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Expected raw file not found: {path}. "
            "Run `python scripts/generate_sample_data.py` first."
        )
    non_date_dtypes = {k: v for k, v in dtypes.items() if k not in (parse_dates or [])}
    df = pd.read_csv(path, dtype=non_date_dtypes, parse_dates=parse_dates or None)
    return df


def load_products() -> pd.DataFrame:
    return _read_csv(RAW_FILES["products"], PRODUCT_COLUMNS, DATE_COLUMNS["products"])


def load_customers() -> pd.DataFrame:
    return _read_csv(RAW_FILES["customers"], CUSTOMER_COLUMNS)


def load_sales() -> pd.DataFrame:
    return _read_csv(RAW_FILES["sales"], SALES_COLUMNS, DATE_COLUMNS["sales"])


def load_costs() -> pd.DataFrame:
    return _read_csv(RAW_FILES["costs"], COST_COLUMNS)


def load_fx() -> pd.DataFrame:
    return _read_csv(RAW_FILES["fx"], FX_COLUMNS)


def load_all() -> dict[str, pd.DataFrame]:
    return {
        "products": load_products(),
        "customers": load_customers(),
        "sales": load_sales(),
        "costs": load_costs(),
        "fx": load_fx(),
    }
