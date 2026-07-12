from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import INDUSTRY_COLORS, family_trend_lines, growth_bars, pvm_waterfall
from src.analytics.trend_analysis import (
    add_period_over_period,
    monthly_margin_by_family,
    monthly_margin_by_industry,
    monthly_trend,
    pvm_decomposition,
)


def render_trend(fact: pd.DataFrame) -> None:
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

    st.markdown("### 各產業別毛利率趨勢 / Gross margin trend by industry")
    st.plotly_chart(
        family_trend_lines(
            monthly_margin_by_industry(fact),
            y_col="gross_margin_pct",
            y_title="毛利率 % / Gross Margin %",
            group_col="industry",
            color_map=INDUSTRY_COLORS,
        ),
        use_container_width=True,
    )
    st.caption("配色與客戶分析頁的產業別一致 / Same industry colors as the Customer page.")

    st.markdown("### 毛利成長率 / Gross profit growth")
    pop = add_period_over_period(monthly_trend(fact))
    col_mom, col_yoy = st.columns(2)
    with col_mom:
        st.plotly_chart(growth_bars(pop, "gross_profit_usd_mom_pct", "MoM"), use_container_width=True)
    with col_yoy:
        st.plotly_chart(growth_bars(pop, "gross_profit_usd_yoy_pct", "YoY"), use_container_width=True)

    st.markdown("### 毛利變化拆解 / Gross-profit PVM waterfall")
    periods = sorted(fact["period"].dropna().unique().tolist())
    if len(periods) < 2:
        st.info("需要至少兩個月份的資料才能拆解 / Needs at least two periods.")
        return
    col_base, col_curr = st.columns(2)
    with col_base:
        base = st.selectbox("基期 / Base period", periods, index=len(periods) - 2)
    with col_curr:
        curr = st.selectbox("當期 / Current period", periods, index=len(periods) - 1)
    if base == curr:
        st.info("請選擇兩個不同月份 / Pick two different periods.")
        return
    pvm = pvm_decomposition(fact[fact["period"] == base], fact[fact["period"] == curr])
    st.plotly_chart(pvm_waterfall(pvm, base, curr), use_container_width=True)
    st.caption(
        "**價格**＝售價變動 × 當期量；**成本**＝單位成本變動 × 當期量（成本上漲為負）；"
        "**數量**＝量變動 × 基期單位毛利；**組合**＝新進/退出料號的貢獻。"
        "四項加總恆等於期末 − 期初毛利。"
    )
