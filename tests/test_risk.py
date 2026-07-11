"""Sanity checks for margin-risk detection (low margin, decline, NPI health)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.analytics.risk import declining_margin_products, low_margin_customers, low_margin_products, npi_health


def _fact(rows: list[dict]) -> pd.DataFrame:
    defaults = {
        "order_id": None,
        "product_family": "MCU",
        "customer_name": "Acme",
        "customer_tier": "A",
        "industry": "Consumer",
        "product_status": "Active",
        "yield_rate": 0.95,
        "cogs_usd": 0.0,
    }
    out = []
    for i, row in enumerate(rows):
        merged = {**defaults, **row}
        if merged["order_id"] is None:
            merged["order_id"] = f"ORD{i:04d}"
        out.append(merged)
    return pd.DataFrame(out)


def test_low_margin_products_filters_below_threshold() -> None:
    fact = _fact([
        {"product_id": "A", "revenue_usd": 100.0, "gross_profit_usd": 5.0, "quantity": 10},
        {"product_id": "B", "revenue_usd": 100.0, "gross_profit_usd": 40.0, "quantity": 10},
    ])
    result = low_margin_products(fact, threshold_pct=10.0)
    assert result["product_id"].tolist() == ["A"]


def test_low_margin_customers_filters_below_threshold() -> None:
    fact = _fact([
        {"product_id": "A", "customer_id": "C1", "revenue_usd": 100.0, "gross_profit_usd": 5.0, "quantity": 10},
        {"product_id": "A", "customer_id": "C2", "revenue_usd": 100.0, "gross_profit_usd": 40.0, "quantity": 10},
    ])
    result = low_margin_customers(fact, threshold_pct=10.0)
    assert result["customer_id"].tolist() == ["C1"]


def test_declining_margin_products_detects_drop() -> None:
    rows = []
    # Product A: 40% margin in months 1-3, 20% margin in months 4-6 -> 20pt drop
    for period in ["2026-01", "2026-02", "2026-03"]:
        rows.append({
            "product_id": "A", "period": period, "revenue_usd": 100.0, "gross_profit_usd": 40.0, "quantity": 10,
        })
    for period in ["2026-04", "2026-05", "2026-06"]:
        rows.append({
            "product_id": "A", "period": period, "revenue_usd": 100.0, "gross_profit_usd": 20.0, "quantity": 10,
        })
    # Product B: stable 30% margin throughout -> no drop
    for period in ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]:
        rows.append({
            "product_id": "B", "period": period, "revenue_usd": 100.0, "gross_profit_usd": 30.0, "quantity": 10,
        })
    fact = _fact(rows)

    result = declining_margin_products(fact, recent_months=3, min_drop_pct=5.0)
    assert result["product_id"].tolist() == ["A"]
    assert result.loc[0, "drop_pct_pt"] == pytest.approx(20.0)


def test_declining_margin_products_insufficient_history_returns_empty() -> None:
    fact = _fact([
        {"product_id": "A", "period": "2026-01", "revenue_usd": 100.0, "gross_profit_usd": 40.0, "quantity": 10},
    ])
    result = declining_margin_products(fact, recent_months=3)
    assert result.empty


def test_npi_health_only_includes_npi_products() -> None:
    fact = _fact([
        {
            "product_id": "A", "product_status": "NPI", "revenue_usd": 100.0,
            "gross_profit_usd": 30.0, "quantity": 10, "yield_rate": 0.80,
        },
        {
            "product_id": "B", "product_status": "Active", "revenue_usd": 100.0,
            "gross_profit_usd": 30.0, "quantity": 10, "yield_rate": 0.95,
        },
    ])
    result = npi_health(fact)
    assert result["product_id"].tolist() == ["A"]
    assert result.loc[0, "avg_yield_rate"] == pytest.approx(0.80)


def test_npi_health_empty_when_no_npi_products() -> None:
    fact = _fact([
        {"product_id": "A", "product_status": "Active", "revenue_usd": 100.0, "gross_profit_usd": 30.0, "quantity": 10},
    ])
    result = npi_health(fact)
    assert result.empty
