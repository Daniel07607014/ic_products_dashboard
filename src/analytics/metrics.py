"""Core gross-margin formulas.

Every function takes a DataFrame (the "fact table" produced by
:func:`src.etl.join.build_fact_table`) and returns either a scalar or a
DataFrame — never touches Streamlit, so it is fully unit-testable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def gross_profit(revenue: float | pd.Series, cogs: float | pd.Series) -> float | pd.Series:
    return revenue - cogs


def gross_margin_pct(revenue: float | pd.Series, cogs: float | pd.Series) -> float | pd.Series:
    """Return gross margin as a percentage. Zero revenue → 0 to avoid div-by-zero."""
    if isinstance(revenue, pd.Series):
        gm = np.where(revenue > 0, (revenue - cogs) / revenue * 100.0, 0.0)
        return pd.Series(gm, index=revenue.index)
    if revenue == 0:
        return 0.0
    return (revenue - cogs) / revenue * 100.0


def unit_gross_profit(unit_price: float | pd.Series, unit_cost: float | pd.Series) -> float | pd.Series:
    return unit_price - unit_cost


def weighted_avg_margin(fact: pd.DataFrame) -> float:
    """Revenue-weighted average gross-margin percentage.

    Straight average would over-weight low-revenue, high-margin products
    and misrepresent the portfolio.
    """
    revenue = fact["revenue_usd"].sum()
    if revenue == 0:
        return 0.0
    profit = fact["gross_profit_usd"].sum()
    return profit / revenue * 100.0


def effective_cost(raw_cost: float | pd.Series, yield_rate: float | pd.Series) -> float | pd.Series:
    """Cost adjusted for yield loss: a die with 80% yield effectively costs 25% more."""
    return raw_cost / yield_rate


def iqr_filter(
    df: pd.DataFrame,
    value_col: str,
    group_col: str | None = None,
    k: float = 1.5,
) -> pd.DataFrame:
    """Drop rows outside the Tukey fence (Q1 - k*IQR, Q3 + k*IQR).

    With `group_col`, fences are computed per group — an outlier for a
    tight-margin family may be normal for a volatile one.
    """
    def _mask(s: pd.Series) -> pd.Series:
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        return (s >= q1 - k * iqr) & (s <= q3 + k * iqr)

    if group_col is None:
        return df.loc[_mask(df[value_col])].copy()
    keep = df.groupby(group_col, dropna=False)[value_col].transform(
        lambda s: _mask(s)
    )
    return df.loc[keep].copy()


def portfolio_kpis(fact: pd.DataFrame) -> dict[str, float]:
    """Return the four KPI numbers used on the Overview page."""
    return {
        "total_revenue_usd": float(fact["revenue_usd"].sum()),
        "total_gross_profit_usd": float(fact["gross_profit_usd"].sum()),
        "avg_gross_margin_pct": weighted_avg_margin(fact),
        "active_products": int(fact["product_id"].nunique()),
    }
