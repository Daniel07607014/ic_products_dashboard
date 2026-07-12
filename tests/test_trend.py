"""Period-over-period alignment and PVM decomposition."""
from __future__ import annotations

import pandas as pd
import pytest

from src.analytics.trend_analysis import add_period_over_period, pvm_decomposition


def _monthly(periods: list[str], revenue: list[float]) -> pd.DataFrame:
    return pd.DataFrame({
        "period": periods,
        "revenue_usd": revenue,
        "gross_profit_usd": [r * 0.4 for r in revenue],
    })


def test_yoy_is_calendar_aware_across_gap() -> None:
    # 2025-02 is missing: row-counting pct_change would compare 2026-01
    # against 2025-02's slot; calendar-aware must still hit 2025-01.
    periods = [f"2025-{m:02d}" for m in (1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)] + ["2026-01"]
    revenue = [100.0] * 11 + [150.0]
    out = add_period_over_period(_monthly(periods, revenue)).set_index("period")
    assert out.loc["2026-01", "revenue_usd_yoy_pct"] == pytest.approx(50.0)


def test_mom_after_gap_is_nan_not_padded() -> None:
    out = add_period_over_period(
        _monthly(["2026-01", "2026-03"], [100.0, 120.0])
    ).set_index("period")
    assert pd.isna(out.loc["2026-03", "revenue_usd_mom_pct"])


def test_filler_months_are_not_returned() -> None:
    out = add_period_over_period(_monthly(["2026-01", "2026-03"], [100.0, 120.0]))
    assert out["period"].tolist() == ["2026-01", "2026-03"]


def _fact(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["revenue_usd"] = df["price"] * df["quantity"]
    df["cogs_usd"] = df["cost"] * df["quantity"]
    df["gross_profit_usd"] = df["revenue_usd"] - df["cogs_usd"]
    return df


def test_pvm_isolates_each_effect() -> None:
    prev = _fact([{"product_id": "A", "price": 2.0, "cost": 1.0, "quantity": 100}])

    price_up = _fact([{"product_id": "A", "price": 2.5, "cost": 1.0, "quantity": 100}])
    pvm = pvm_decomposition(prev, price_up)
    assert pvm["price_effect"] == pytest.approx(50.0)
    assert pvm["cost_effect"] == pytest.approx(0.0)
    assert pvm["volume_effect"] == pytest.approx(0.0)
    assert pvm["mix_effect"] == pytest.approx(0.0)

    cost_up = _fact([{"product_id": "A", "price": 2.0, "cost": 1.2, "quantity": 100}])
    pvm = pvm_decomposition(prev, cost_up)
    assert pvm["cost_effect"] == pytest.approx(-20.0)
    assert pvm["price_effect"] == pytest.approx(0.0)

    volume_up = _fact([{"product_id": "A", "price": 2.0, "cost": 1.0, "quantity": 250}])
    pvm = pvm_decomposition(prev, volume_up)
    assert pvm["volume_effect"] == pytest.approx(150.0)  # +150 units × $1 base margin
    assert pvm["price_effect"] == pytest.approx(0.0)


def test_pvm_new_product_lands_in_mix() -> None:
    prev = _fact([{"product_id": "A", "price": 2.0, "cost": 1.0, "quantity": 100}])
    curr = _fact([
        {"product_id": "A", "price": 2.0, "cost": 1.0, "quantity": 100},
        {"product_id": "B", "price": 5.0, "cost": 3.0, "quantity": 10},  # new SKU, GP +20
    ])
    pvm = pvm_decomposition(prev, curr)
    assert pvm["mix_effect"] == pytest.approx(20.0)


def test_pvm_effects_reconcile_to_total_change() -> None:
    prev = _fact([
        {"product_id": "A", "price": 2.0, "cost": 1.0, "quantity": 100},
        {"product_id": "B", "price": 5.0, "cost": 3.0, "quantity": 50},
        {"product_id": "EOL", "price": 3.0, "cost": 2.9, "quantity": 30},
    ])
    curr = _fact([
        {"product_id": "A", "price": 2.2, "cost": 1.1, "quantity": 140},
        {"product_id": "B", "price": 4.8, "cost": 3.2, "quantity": 45},
        {"product_id": "NEW", "price": 6.0, "cost": 3.5, "quantity": 20},
    ])
    pvm = pvm_decomposition(prev, curr)
    total = pvm["price_effect"] + pvm["cost_effect"] + pvm["volume_effect"] + pvm["mix_effect"]
    assert total == pytest.approx(pvm["gross_profit_curr"] - pvm["gross_profit_prev"])
