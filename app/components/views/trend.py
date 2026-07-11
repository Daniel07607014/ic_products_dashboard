from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import family_trend_lines, growth_bars, revenue_margin_trend
from src.analytics.trend_analysis import (
    add_period_over_period,
    monthly_margin_by_family,
    monthly_trend,
    monthly_unit_cost_by_family,
    rolling_avg,
)


def render_trend(fact: pd.DataFrame) -> None:
    monthly = monthly_trend(fact)

    st.markdown("### 月度趨勢 / Monthly trend")
    window = st.slider("移動平均視窗 / Rolling window (months)", 2, 12, 3)
    smoothed = rolling_avg(monthly, window=window)
    st.plotly_chart(revenue_margin_trend(smoothed, ma_window=window), use_container_width=True)
    st.caption("虛線＝營收移動平均、點線＝毛利率移動平均 / Dashed = revenue MA, dotted = GM% MA.")

    st.markdown("### 各系列單位成本趨勢 / Unit cost trend by family")
    st.plotly_chart(
        family_trend_lines(
            monthly_unit_cost_by_family(fact),
            y_col="unit_cost_usd",
            y_title="加權平均單位成本 (USD) / Weighted avg unit cost",
        ),
        use_container_width=True,
    )
    st.caption("加權平均：總成本 ÷ 總出貨數量（月）/ Weighted by quantity, per month.")

    st.markdown("### 各系列毛利率趨勢 / Gross margin trend by family")
    st.plotly_chart(
        family_trend_lines(
            monthly_margin_by_family(fact),
            y_col="gross_margin_pct",
            y_title="毛利率 % / Gross Margin %",
        ),
        use_container_width=True,
    )
    st.caption("營收加權：總毛利 ÷ 總營收（月）/ Revenue-weighted, per month.")

    st.markdown("### 成長率 / MoM & YoY growth")
    pop = add_period_over_period(monthly)
    metric_choice = st.radio(
        "指標 / Metric",
        ["營收 / Revenue", "毛利 / Gross Profit"],
        horizontal=True,
        key="growth_metric",
    )
    base = "revenue_usd" if metric_choice.startswith("營收") else "gross_profit_usd"
    col_mom, col_yoy = st.columns(2)
    with col_mom:
        st.plotly_chart(growth_bars(pop, f"{base}_mom_pct", "MoM"), use_container_width=True)
    with col_yoy:
        st.plotly_chart(growth_bars(pop, f"{base}_yoy_pct", "YoY"), use_container_width=True)

    with st.expander("查看數字 / Underlying tables"):
        st.markdown(f"**{window} 個月移動平均 / {window}-month rolling average**")
        st.dataframe(smoothed, use_container_width=True)
        st.markdown("**MoM / YoY**")
        st.dataframe(pop, use_container_width=True)

    # TODO: PVM waterfall — src.analytics.trend_analysis.pvm_decomposition
