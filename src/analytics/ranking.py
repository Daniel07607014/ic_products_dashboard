"""Top-N and Pareto/ABC ranking helpers."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analytics.metrics import margin_pct_of


def top_n_products(fact: pd.DataFrame, n: int = 10, by: str = "gross_profit_usd") -> pd.DataFrame:
    grouped = fact.groupby(["product_id", "product_family"], dropna=False).agg(
        revenue_usd=("revenue_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
    ).reset_index()
    grouped["gross_margin_pct"] = margin_pct_of(grouped["gross_profit_usd"], grouped["revenue_usd"])
    return grouped.sort_values(by, ascending=False).head(n).reset_index(drop=True)


def bottom_n_products(fact: pd.DataFrame, n: int = 10, by: str = "gross_margin_pct") -> pd.DataFrame:
    grouped = fact.groupby(["product_id", "product_family"], dropna=False).agg(
        revenue_usd=("revenue_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
    ).reset_index()
    grouped["gross_margin_pct"] = margin_pct_of(grouped["gross_profit_usd"], grouped["revenue_usd"])
    return grouped.sort_values(by, ascending=True).head(n).reset_index(drop=True)


def abc_analysis(fact: pd.DataFrame, dimension: str = "product_id") -> pd.DataFrame:
    """Pareto (80/20) classification.

    A = items up to *and including* the one that crosses 80% cumulative revenue
    B = up to and including the 95% crossing
    C = remaining tail
    """
    grouped = fact.groupby(dimension, dropna=False)["revenue_usd"].sum().reset_index()
    grouped = grouped.sort_values("revenue_usd", ascending=False).reset_index(drop=True)
    total = grouped["revenue_usd"].sum()
    grouped["cum_pct"] = grouped["revenue_usd"].cumsum() / total * 100 if total > 0 else 0.0

    # Classify by where the item *starts* (cumulative share before it), so the
    # boundary-crossing item belongs to the class it completes — otherwise a
    # single customer carrying 100% of revenue would land in C.
    prev_cum = grouped["cum_pct"].shift(fill_value=0.0)
    grouped["abc_class"] = np.select([prev_cum < 80, prev_cum < 95], ["A", "B"], default="C")
    return grouped


def concentration_index(fact: pd.DataFrame, dimension: str = "customer_id", metric: str = "revenue_usd") -> float:
    """Herfindahl-Hirschman Index: sum of squared market shares (0-10000 scale).

    Conventional bands: <1500 diversified, 1500-2500 moderately concentrated,
    >2500 highly concentrated.
    """
    shares = fact.groupby(dimension, dropna=False)[metric].sum()
    total = shares.sum()
    if total == 0:
        return 0.0
    pct_shares = shares / total * 100
    return float((pct_shares ** 2).sum())


def top_n_share(fact: pd.DataFrame, dimension: str = "customer_id", n: int = 5, metric: str = "revenue_usd") -> float:
    """Percentage of `metric` contributed by the top N entities in `dimension`."""
    shares = fact.groupby(dimension, dropna=False)[metric].sum().sort_values(ascending=False)
    total = shares.sum()
    if total == 0:
        return 0.0
    return float(shares.head(n).sum() / total * 100)
