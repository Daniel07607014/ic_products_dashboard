"""Top-N and Pareto/ABC ranking helpers."""
from __future__ import annotations

import pandas as pd


def top_n_products(fact: pd.DataFrame, n: int = 10, by: str = "gross_profit_usd") -> pd.DataFrame:
    grouped = fact.groupby(["product_id", "product_family"], dropna=False).agg(
        revenue_usd=("revenue_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
    ).reset_index()
    grouped["gross_margin_pct"] = (
        grouped["gross_profit_usd"] / grouped["revenue_usd"].where(grouped["revenue_usd"] > 0) * 100
    ).fillna(0.0)
    return grouped.sort_values(by, ascending=False).head(n).reset_index(drop=True)


def bottom_n_products(fact: pd.DataFrame, n: int = 10, by: str = "gross_margin_pct") -> pd.DataFrame:
    grouped = fact.groupby(["product_id", "product_family"], dropna=False).agg(
        revenue_usd=("revenue_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
    ).reset_index()
    grouped["gross_margin_pct"] = (
        grouped["gross_profit_usd"] / grouped["revenue_usd"].where(grouped["revenue_usd"] > 0) * 100
    ).fillna(0.0)
    return grouped.sort_values(by, ascending=True).head(n).reset_index(drop=True)


def abc_analysis(fact: pd.DataFrame, dimension: str = "product_id") -> pd.DataFrame:
    """Pareto (80/20) classification.

    A = top items contributing to 80% of revenue
    B = next 15% (up to 95%)
    C = remaining tail
    """
    grouped = fact.groupby(dimension, dropna=False)["revenue_usd"].sum().reset_index()
    grouped = grouped.sort_values("revenue_usd", ascending=False).reset_index(drop=True)
    total = grouped["revenue_usd"].sum()
    grouped["cum_pct"] = grouped["revenue_usd"].cumsum() / total * 100

    def classify(pct: float) -> str:
        if pct <= 80:
            return "A"
        if pct <= 95:
            return "B"
        return "C"

    grouped["abc_class"] = grouped["cum_pct"].apply(classify)
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
