"""Sanity checks for the gross-margin formulas.

Kept intentionally small — enough to prove the module wires up and the
zero-revenue edge case is handled. Expand as real formulas are added.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.analytics.metrics import (
    effective_cost,
    gross_margin_pct,
    gross_profit,
    iqr_filter,
    portfolio_kpis,
    weighted_avg_margin,
)


def test_gross_profit_scalar() -> None:
    assert gross_profit(100.0, 60.0) == pytest.approx(40.0)


def test_gross_margin_scalar() -> None:
    assert gross_margin_pct(100.0, 60.0) == pytest.approx(40.0)


def test_gross_margin_zero_revenue() -> None:
    assert gross_margin_pct(0.0, 10.0) == 0.0


def test_gross_margin_series_handles_zero_rows() -> None:
    revenue = pd.Series([100.0, 0.0, 200.0])
    cogs = pd.Series([60.0, 5.0, 150.0])
    result = gross_margin_pct(revenue, cogs)
    assert result.iloc[0] == pytest.approx(40.0)
    assert result.iloc[1] == 0.0
    assert result.iloc[2] == pytest.approx(25.0)


def test_effective_cost_penalises_low_yield() -> None:
    assert effective_cost(1.0, 0.8) == pytest.approx(1.25)


def test_weighted_avg_margin_matches_portfolio() -> None:
    fact = pd.DataFrame({
        "revenue_usd":     [100.0, 900.0],
        "gross_profit_usd":[80.0,  90.0],
        "product_id":      ["A",   "B"],
    })
    # revenue-weighted: (80 + 90) / (100 + 900) = 17%
    assert weighted_avg_margin(fact) == pytest.approx(17.0)


def test_iqr_filter_drops_extreme_value() -> None:
    df = pd.DataFrame({"v": [10.0, 11.0, 12.0, 11.5, 10.5, 500.0]})
    result = iqr_filter(df, "v")
    assert 500.0 not in result["v"].values
    assert len(result) == 5


def test_iqr_filter_keeps_normal_data() -> None:
    df = pd.DataFrame({"v": [10.0, 11.0, 12.0, 13.0, 14.0]})
    assert len(iqr_filter(df, "v")) == 5


def test_iqr_filter_groupwise_fences() -> None:
    # 100 is an outlier for group a (tight around 10) but normal for group b.
    df = pd.DataFrame({
        "g": ["a"] * 5 + ["b"] * 5,
        "v": [10.0, 10.5, 11.0, 10.2, 100.0, 90.0, 100.0, 110.0, 95.0, 105.0],
    })
    result = iqr_filter(df, "v", group_col="g")
    assert len(result[result["g"] == "a"]) == 4          # 100 dropped from a
    assert len(result[result["g"] == "b"]) == 5          # b untouched


def test_portfolio_kpis_shape() -> None:
    fact = pd.DataFrame({
        "revenue_usd":     [100.0, 200.0],
        "gross_profit_usd":[20.0,  60.0],
        "product_id":      ["A",   "B"],
    })
    kpis = portfolio_kpis(fact)
    assert set(kpis) == {
        "total_revenue_usd",
        "total_gross_profit_usd",
        "avg_gross_margin_pct",
        "active_products",
    }
    assert kpis["active_products"] == 2
    assert kpis["total_revenue_usd"] == 300.0
