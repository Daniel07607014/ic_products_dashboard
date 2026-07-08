"""KPI card layout used on the Overview page."""
from __future__ import annotations

import streamlit as st


def render_kpi_row(kpis: dict[str, float]) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("總營收 / Total Revenue", f"${kpis['total_revenue_usd']:,.0f}")
    c2.metric("總毛利 / Gross Profit", f"${kpis['total_gross_profit_usd']:,.0f}")
    c3.metric("平均毛利率 / Avg GM%", f"{kpis['avg_gross_margin_pct']:.1f}%")
    c4.metric("活躍產品數 / Active SKUs", f"{kpis['active_products']:,}")


def _hhi_label(hhi: float) -> str:
    if hhi > 2500:
        return "高度集中"
    if hhi > 1500:
        return "中度集中"
    return "分散"


def render_concentration_kpis(
    customer_hhi: float,
    product_hhi: float,
    top5_customer_share_pct: float,
    top5_product_share_pct: float,
) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("客戶集中度 HHI", f"{customer_hhi:,.0f}", _hhi_label(customer_hhi), delta_color="off")
    c2.metric("產品集中度 HHI", f"{product_hhi:,.0f}", _hhi_label(product_hhi), delta_color="off")
    c3.metric("Top 5 客戶營收佔比", f"{top5_customer_share_pct:.1f}%")
    c4.metric("Top 5 產品營收佔比", f"{top5_product_share_pct:.1f}%")
