"""KPI card layout used on the Overview page."""
from __future__ import annotations

import streamlit as st


def render_kpi_row(kpis: dict[str, float]) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("總營收 / Total Revenue", f"${kpis['total_revenue_usd']:,.0f}")
    c2.metric("總毛利 / Gross Profit", f"${kpis['total_gross_profit_usd']:,.0f}")
    c3.metric("平均毛利率 / Avg GM%", f"{kpis['avg_gross_margin_pct']:.1f}%")
    c4.metric("活躍產品數 / Active SKUs", f"{kpis['active_products']:,}")
