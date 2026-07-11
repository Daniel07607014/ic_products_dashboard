from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import family_trend_lines, growth_bars, tier_performance_colors
from src.analytics.trend_analysis import (
    add_period_over_period,
    monthly_margin_by_family,
    monthly_margin_by_tier,
    monthly_trend,
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

    st.markdown("### 各分級毛利率趨勢 / Gross margin trend by customer tier")
    st.plotly_chart(
        family_trend_lines(
            monthly_margin_by_tier(fact),
            y_col="gross_margin_pct",
            y_title="毛利率 % / Gross Margin %",
            group_col="customer_tier",
            color_map=tier_performance_colors(fact),
        ),
        use_container_width=True,
    )
    st.caption("顏色＝毛利率表現：🟢 最高、🟡 次高、🔴 最低（與客戶分析頁一致）。")

    st.markdown("### 毛利成長率 / Gross profit growth")
    pop = add_period_over_period(monthly_trend(fact))
    col_mom, col_yoy = st.columns(2)
    with col_mom:
        st.plotly_chart(growth_bars(pop, "gross_profit_usd_mom_pct", "MoM"), use_container_width=True)
    with col_yoy:
        st.plotly_chart(growth_bars(pop, "gross_profit_usd_yoy_pct", "YoY"), use_container_width=True)

    # TODO: PVM waterfall — src.analytics.trend_analysis.pvm_decomposition
