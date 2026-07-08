"""Margin-risk detection: below-threshold products/customers, declining
trends, and NPI ramp health — the things a BU head actually watches for.
"""
from __future__ import annotations

import pandas as pd

from src.analytics.dimension_analysis import by_customer, by_product


def low_margin_products(fact: pd.DataFrame, threshold_pct: float = 10.0) -> pd.DataFrame:
    df = by_product(fact)
    return df[df["gross_margin_pct"] < threshold_pct].sort_values("gross_margin_pct").reset_index(drop=True)


def low_margin_customers(fact: pd.DataFrame, threshold_pct: float = 10.0) -> pd.DataFrame:
    df = by_customer(fact)
    return df[df["gross_margin_pct"] < threshold_pct].sort_values("gross_margin_pct").reset_index(drop=True)


def _margin_by_product(fact: pd.DataFrame, periods: list[str]) -> pd.Series:
    sub = fact[fact["period"].isin(periods)]
    grouped = sub.groupby("product_id").agg(
        revenue_usd=("revenue_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
    )
    return (grouped["gross_profit_usd"] / grouped["revenue_usd"].where(grouped["revenue_usd"] > 0) * 100).fillna(0.0)


def declining_margin_products(
    fact: pd.DataFrame, recent_months: int = 3, min_drop_pct: float = 5.0
) -> pd.DataFrame:
    """Products whose revenue-weighted margin dropped by at least
    `min_drop_pct` percentage points in the most recent N months vs the
    N months before that.
    """
    periods = sorted(fact["period"].dropna().unique().tolist())
    columns = ["product_id", "product_family", "prior_margin_pct", "recent_margin_pct", "drop_pct_pt"]
    if len(periods) < recent_months * 2:
        return pd.DataFrame(columns=columns)

    recent_periods = periods[-recent_months:]
    prior_periods = periods[-recent_months * 2 : -recent_months]

    recent_margin = _margin_by_product(fact, recent_periods).rename("recent_margin_pct")
    prior_margin = _margin_by_product(fact, prior_periods).rename("prior_margin_pct")

    merged = pd.concat([prior_margin, recent_margin], axis=1).dropna()
    merged["drop_pct_pt"] = merged["prior_margin_pct"] - merged["recent_margin_pct"]
    merged = merged[merged["drop_pct_pt"] >= min_drop_pct].reset_index()

    families = fact[["product_id", "product_family"]].drop_duplicates()
    merged = merged.merge(families, on="product_id", how="left")
    return merged[columns].sort_values("drop_pct_pt", ascending=False).reset_index(drop=True)


def npi_health(fact: pd.DataFrame) -> pd.DataFrame:
    """Revenue, margin and yield for products still in NPI (new product introduction)."""
    columns = ["product_id", "product_family", "revenue_usd", "gross_margin_pct", "avg_yield_rate"]
    npi = fact[fact["product_status"] == "NPI"]
    if npi.empty:
        return pd.DataFrame(columns=columns)

    grouped = npi.groupby(["product_id", "product_family"], dropna=False).agg(
        revenue_usd=("revenue_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
        avg_yield_rate=("yield_rate", "mean"),
    ).reset_index()
    grouped["gross_margin_pct"] = (
        grouped["gross_profit_usd"] / grouped["revenue_usd"].where(grouped["revenue_usd"] > 0) * 100
    ).fillna(0.0)
    return grouped[columns].sort_values("gross_margin_pct").reset_index(drop=True)
