from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import (
    INDUSTRY_COLORS,
    heatmap,
    margin_distribution,
    margin_histogram_overlay,
)
from src.analytics.dimension_analysis import by_customer, by_industry, product_customer_matrix
from src.analytics.metrics import iqr_filter


def render_customer(fact: pd.DataFrame) -> None:
    st.markdown("### 毛利率分布（依產業別）/ Margin distribution by industry")

    mode = st.radio(
        "顯示方式 / Display",
        ["分面直方圖 / Facet", "箱型圖 / Box"],
        horizontal=True,
        label_visibility="collapsed",
        key="customer_display_mode",
    )

    if mode.startswith("箱型圖"):
        # Raw customer-level data (one box point per customer) — no outlier
        # trimming for box plots.
        st.plotly_chart(
            margin_distribution(by_customer(fact), group_col="industry", color_map=INDUSTRY_COLORS),
            use_container_width=True,
        )
    else:
        cleaned = iqr_filter(fact, "gross_margin_pct", group_col="industry")
        st.plotly_chart(
            margin_histogram_overlay(
                cleaned,
                group_col="industry",
                color_map=INDUSTRY_COLORS,
                facet=True,
            ),
            use_container_width=True,
        )
        st.caption(f"已依 IQR 檢定移除 {len(fact) - len(cleaned):,} 筆離群交易（各產業別各自計算圍籬）。")

    st.markdown("### Top 客戶 / Top customers")
    st.dataframe(
        by_customer(fact).sort_values("gross_profit_usd", ascending=False).head(20),
        use_container_width=True,
    )

    st.markdown("### 產業別 / Industry breakdown")
    st.dataframe(by_industry(fact), use_container_width=True)

    st.markdown("### 系列 × 產業別 毛利率熱力圖 / Family × Industry margin heatmap")
    st.plotly_chart(heatmap(product_customer_matrix(fact)), use_container_width=True)
