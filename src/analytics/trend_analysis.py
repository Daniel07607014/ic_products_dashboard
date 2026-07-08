"""Time-series aggregation and period-over-period comparisons."""
from __future__ import annotations

import pandas as pd


def monthly_trend(fact: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the fact table to a monthly series (period × metrics)."""
    monthly = fact.groupby("period").agg(
        revenue_usd=("revenue_usd", "sum"),
        cogs_usd=("cogs_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
        quantity=("quantity", "sum"),
    ).reset_index()
    monthly["gross_margin_pct"] = (
        monthly["gross_profit_usd"] / monthly["revenue_usd"].where(monthly["revenue_usd"] > 0) * 100
    ).fillna(0.0)
    monthly = monthly.sort_values("period").reset_index(drop=True)
    return monthly


def add_period_over_period(monthly: pd.DataFrame) -> pd.DataFrame:
    """Add MoM / YoY growth columns for revenue and gross profit."""
    out = monthly.copy()
    for col in ("revenue_usd", "gross_profit_usd"):
        out[f"{col}_mom_pct"] = out[col].pct_change() * 100
        out[f"{col}_yoy_pct"] = out[col].pct_change(periods=12) * 100
    return out


def rolling_avg(monthly: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Simple rolling average — TODO: expose in Trend page as a smoothing toggle."""
    out = monthly.copy()
    out[f"revenue_usd_ma{window}"] = out["revenue_usd"].rolling(window).mean()
    out[f"gross_margin_pct_ma{window}"] = out["gross_margin_pct"].rolling(window).mean()
    return out


def pvm_decomposition(fact_prev: pd.DataFrame, fact_curr: pd.DataFrame) -> dict[str, float]:
    """Price-Volume-Mix decomposition of gross-profit change between two periods.

    TODO: implement the full PVM waterfall. For now returns totals so the page
    can show something. Expected effects (rough sketch):
        Price effect  = Σ (P1 - P0) × Q1
        Volume effect = Σ (Q1 - Q0) × P0
        Mix effect    = residual
    """
    return {
        "revenue_prev": float(fact_prev["revenue_usd"].sum()),
        "revenue_curr": float(fact_curr["revenue_usd"].sum()),
        "gross_profit_prev": float(fact_prev["gross_profit_usd"].sum()),
        "gross_profit_curr": float(fact_curr["gross_profit_usd"].sum()),
    }
