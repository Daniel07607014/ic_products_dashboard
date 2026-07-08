"""Slice the fact table by product / customer / geographic dimensions."""
from __future__ import annotations

import pandas as pd

from src.analytics.metrics import weighted_avg_margin


def _agg(fact: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    grouped = fact.groupby(by, dropna=False).agg(
        revenue_usd=("revenue_usd", "sum"),
        cogs_usd=("cogs_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
        quantity=("quantity", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index()
    grouped["gross_margin_pct"] = (
        grouped["gross_profit_usd"] / grouped["revenue_usd"].where(grouped["revenue_usd"] > 0) * 100
    ).fillna(0.0)
    return grouped


def by_product(fact: pd.DataFrame) -> pd.DataFrame:
    return _agg(fact, ["product_id", "product_family"])


def by_family(fact: pd.DataFrame) -> pd.DataFrame:
    return _agg(fact, ["product_family"])


def by_process_node(fact: pd.DataFrame) -> pd.DataFrame:
    return _agg(fact, ["process_node"])


def by_customer(fact: pd.DataFrame) -> pd.DataFrame:
    return _agg(fact, ["customer_id", "customer_name", "customer_tier"])


def by_industry(fact: pd.DataFrame) -> pd.DataFrame:
    return _agg(fact, ["industry"])


def by_region(fact: pd.DataFrame) -> pd.DataFrame:
    return _agg(fact, ["region"])


def product_customer_matrix(fact: pd.DataFrame, value: str = "gross_margin_pct") -> pd.DataFrame:
    """Pivot the fact table into a Product × Customer matrix suitable for a heatmap."""
    pivot = fact.pivot_table(
        index="product_family",
        columns="customer_tier",
        values="gross_profit_usd" if value != "gross_margin_pct" else None,
        aggfunc="sum",
    )
    if value == "gross_margin_pct":
        revenue = fact.pivot_table(
            index="product_family", columns="customer_tier",
            values="revenue_usd", aggfunc="sum",
        )
        profit = fact.pivot_table(
            index="product_family", columns="customer_tier",
            values="gross_profit_usd", aggfunc="sum",
        )
        pivot = (profit / revenue.where(revenue > 0) * 100).fillna(0.0)
    return pivot
