"""Time-series aggregation and period-over-period comparisons."""
from __future__ import annotations

import pandas as pd

from src.analytics.metrics import margin_pct_of


def monthly_trend(fact: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the fact table to a monthly series (period × metrics)."""
    monthly = fact.groupby("period").agg(
        revenue_usd=("revenue_usd", "sum"),
        cogs_usd=("cogs_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
        quantity=("quantity", "sum"),
    ).reset_index()
    monthly["gross_margin_pct"] = margin_pct_of(monthly["gross_profit_usd"], monthly["revenue_usd"])
    monthly = monthly.sort_values("period").reset_index(drop=True)
    return monthly


def monthly_unit_cost_by_family(fact: pd.DataFrame) -> pd.DataFrame:
    """Quantity-weighted average unit cost per family per month.

    total COGS / total units, so one big order counts as much as it should —
    a plain mean over transactions would over-weight small orders.
    """
    grouped = fact.groupby(["period", "product_family"], dropna=False).agg(
        cogs_usd=("cogs_usd", "sum"),
        quantity=("quantity", "sum"),
    ).reset_index()
    grouped["unit_cost_usd"] = (
        grouped["cogs_usd"] / grouped["quantity"].where(grouped["quantity"] > 0)
    ).fillna(0.0)
    return grouped[["period", "product_family", "unit_cost_usd"]].sort_values(
        ["period", "product_family"]
    ).reset_index(drop=True)


def _monthly_margin_by(fact: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Revenue-weighted gross margin % per group per month."""
    grouped = fact.groupby(["period", group_col], dropna=False).agg(
        revenue_usd=("revenue_usd", "sum"),
        gross_profit_usd=("gross_profit_usd", "sum"),
    ).reset_index()
    grouped["gross_margin_pct"] = margin_pct_of(grouped["gross_profit_usd"], grouped["revenue_usd"])
    return grouped[["period", group_col, "gross_margin_pct"]].sort_values(
        ["period", group_col]
    ).reset_index(drop=True)


def monthly_margin_by_family(fact: pd.DataFrame) -> pd.DataFrame:
    return _monthly_margin_by(fact, "product_family")


def monthly_margin_by_industry(fact: pd.DataFrame) -> pd.DataFrame:
    return _monthly_margin_by(fact, "industry")


def add_period_over_period(monthly: pd.DataFrame) -> pd.DataFrame:
    """Add MoM / YoY growth columns for revenue and gross profit.

    Comparisons are calendar-aware: the series is reindexed to a complete
    monthly range first, because ``pct_change`` counts rows, not months — a
    missing month would silently shift YoY onto the wrong period.
    """
    out = monthly.copy()
    idx = pd.PeriodIndex(out["period"], freq="M")
    full = pd.period_range(idx.min(), idx.max(), freq="M")
    out = out.set_index(idx).reindex(full)
    for col in ("revenue_usd", "gross_profit_usd"):
        # fill_method=None: a gap month must yield NaN growth, not a padded fake.
        out[f"{col}_mom_pct"] = out[col].pct_change(fill_method=None) * 100
        out[f"{col}_yoy_pct"] = out[col].pct_change(periods=12, fill_method=None) * 100
    out["period"] = out.index.strftime("%Y-%m")
    # Drop the filler months again — callers only want rows that had data.
    return out[out["revenue_usd"].notna()].reset_index(drop=True)


def rolling_avg(monthly: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Simple rolling average — TODO: expose in Trend page as a smoothing toggle."""
    out = monthly.copy()
    out[f"revenue_usd_ma{window}"] = out["revenue_usd"].rolling(window).mean()
    out[f"gross_margin_pct_ma{window}"] = out["gross_margin_pct"].rolling(window).mean()
    return out


def _per_product_pq(fact: pd.DataFrame) -> pd.DataFrame:
    """Quantity-weighted unit price / unit cost per product for one period."""
    g = fact.groupby("product_id").agg(
        revenue_usd=("revenue_usd", "sum"),
        cogs_usd=("cogs_usd", "sum"),
        quantity=("quantity", "sum"),
    )
    g = g[g["quantity"] > 0]
    g["price"] = g["revenue_usd"] / g["quantity"]
    g["cost"] = g["cogs_usd"] / g["quantity"]
    return g


def pvm_decomposition(fact_prev: pd.DataFrame, fact_curr: pd.DataFrame) -> dict[str, float]:
    """Price / Cost / Volume / Mix decomposition of the gross-profit change.

    Over products present in both periods (P/C = weighted-avg unit price/cost,
    Q = quantity, m = P − C):
        price_effect  = Σ (P1 − P0) × Q1
        cost_effect   = −Σ (C1 − C0) × Q1
        volume_effect = Σ (Q1 − Q0) × m0
    These three sum exactly to the common products' gross-profit change, so
        mix_effect    = total ΔGP − (price + cost + volume)
    is the contribution of products that entered or left the portfolio —
    the four effects always reconcile to gross_profit_curr − gross_profit_prev.
    """
    prev, curr = _per_product_pq(fact_prev), _per_product_pq(fact_curr)
    gp_prev = float(fact_prev["gross_profit_usd"].sum())
    gp_curr = float(fact_curr["gross_profit_usd"].sum())

    common = prev.join(curr, lsuffix="_0", rsuffix="_1", how="inner")
    price_effect = float(((common["price_1"] - common["price_0"]) * common["quantity_1"]).sum())
    cost_effect = float(-((common["cost_1"] - common["cost_0"]) * common["quantity_1"]).sum())
    volume_effect = float(
        ((common["quantity_1"] - common["quantity_0"]) * (common["price_0"] - common["cost_0"])).sum()
    )
    mix_effect = (gp_curr - gp_prev) - (price_effect + cost_effect + volume_effect)

    return {
        "revenue_prev": float(fact_prev["revenue_usd"].sum()),
        "revenue_curr": float(fact_curr["revenue_usd"].sum()),
        "gross_profit_prev": gp_prev,
        "gross_profit_curr": gp_curr,
        "price_effect": price_effect,
        "cost_effect": cost_effect,
        "volume_effect": volume_effect,
        "mix_effect": mix_effect,
    }
