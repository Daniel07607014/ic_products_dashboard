"""build_fact_table join integrity — mismatches must fail loudly, because a
silent NaN in COGS drops out of sums and overstates margin with no error."""
from __future__ import annotations

import pandas as pd
import pytest

from src.etl.join import build_fact_table


def _products() -> pd.DataFrame:
    return pd.DataFrame({
        "product_id": ["P1"],
        "product_family": ["MCU"],
        "process_node": [40],
        "package_type": ["QFN"],
        "product_status": ["Active"],
    })


def _customers() -> pd.DataFrame:
    return pd.DataFrame({
        "customer_id": ["C1"],
        "customer_name": ["Acme"],
        "customer_tier": ["A"],
        "industry": ["Consumer"],
        "country": ["Taiwan"],
    })


def _sales() -> pd.DataFrame:
    return pd.DataFrame({
        "order_id": ["O1"],
        "order_date": pd.to_datetime(["2026-01-15"]),
        "product_id": ["P1"],
        "customer_id": ["C1"],
        "region": ["Taiwan"],
        "quantity": [100],
        "unit_price_usd": [2.0],
        "revenue_usd": [200.0],
        "currency": ["USD"],
    })


def _costs() -> pd.DataFrame:
    return pd.DataFrame({
        "product_id": ["P1"],
        "period": ["2026-01"],
        "unit_cost_usd": [1.0],
        "yield_rate": [0.95],
    })


def test_build_fact_table_computes_margin() -> None:
    fact = build_fact_table(_products(), _customers(), _sales(), _costs())
    assert len(fact) == 1
    assert fact.loc[0, "cogs_usd"] == pytest.approx(100.0)
    assert fact.loc[0, "gross_profit_usd"] == pytest.approx(100.0)
    assert fact.loc[0, "gross_margin_pct"] == pytest.approx(50.0)


def test_missing_cost_key_raises() -> None:
    costs = _costs().assign(period=["2025-12"])  # no cost row for the 2026-01 sale
    with pytest.raises(ValueError, match="no matching cost record"):
        build_fact_table(_products(), _customers(), _sales(), costs)


def test_duplicate_cost_key_raises() -> None:
    costs = pd.concat([_costs(), _costs()], ignore_index=True)
    with pytest.raises(pd.errors.MergeError):
        build_fact_table(_products(), _customers(), _sales(), costs)


def test_duplicate_product_master_raises() -> None:
    products = pd.concat([_products(), _products()], ignore_index=True)
    with pytest.raises(pd.errors.MergeError):
        build_fact_table(products, _customers(), _sales(), _costs())
