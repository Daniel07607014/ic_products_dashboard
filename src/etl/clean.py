"""Data cleaning helpers. Keep all null-handling and coercion policy here."""
from __future__ import annotations

import pandas as pd


def drop_invalid_sales(sales: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with non-positive quantity or price — likely returns / errors."""
    mask = (sales["quantity"] > 0) & (sales["unit_price_usd"] > 0)
    return sales.loc[mask].copy()


def fill_yield_rate(costs: pd.DataFrame, default: float = 0.95) -> pd.DataFrame:
    """Missing yield defaults to 95%. Rare in real data but seen in NPI stage."""
    out = costs.copy()
    out["yield_rate"] = out["yield_rate"].fillna(default).clip(lower=0.01, upper=1.0)
    return out


def add_period_column(sales: pd.DataFrame) -> pd.DataFrame:
    """Add a `period` (YYYY-MM) column derived from order_date, for joining to cost/FX."""
    out = sales.copy()
    out["period"] = out["order_date"].dt.strftime("%Y-%m")
    return out
