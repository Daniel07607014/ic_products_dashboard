from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import (
    heatmap,
    margin_distribution,
    margin_histogram_overlay,
    tier_performance_colors,
)
from src.analytics.dimension_analysis import by_customer, by_industry, product_customer_matrix
from src.analytics.metrics import iqr_filter


def render_customer(fact: pd.DataFrame) -> None:
    st.markdown("### 毛利率分布（依客戶分級）/ Margin distribution by tier")

    # Which tiers appear is controlled by the page's Customer-tier filter —
    # no second in-chart selector.
    mode = st.radio(
        "顯示方式 / Display",
        ["分面直方圖 / Facet", "箱型圖 / Box"],
        horizontal=True,
        label_visibility="collapsed",
        key="customer_display_mode",
    )

    color_map = tier_performance_colors(fact)
    if mode.startswith("箱型圖"):
        # Each box point is one customer, so fences apply at customer level.
        customer_df = by_customer(fact)
        cleaned_customers = iqr_filter(customer_df, "gross_margin_pct", group_col="customer_tier")
        st.plotly_chart(
            margin_distribution(cleaned_customers, group_col="customer_tier", color_map=color_map),
            use_container_width=True,
        )
        st.caption(
            f"顏色＝毛利率表現：🟢 最高、🟡 次高、🔴 最低（以營收加權毛利率排名）。"
            f"已依 IQR 檢定移除 {len(customer_df) - len(cleaned_customers):,} 家離群客戶。"
        )
    else:
        cleaned = iqr_filter(fact, "gross_margin_pct", group_col="customer_tier")
        st.plotly_chart(
            margin_histogram_overlay(
                cleaned,
                group_col="customer_tier",
                color_map=color_map,
                facet=True,
            ),
            use_container_width=True,
        )
        st.caption(
            f"顏色＝毛利率表現：🟢 最高、🟡 次高、🔴 最低（以營收加權毛利率排名）。"
            f"已依 IQR 檢定移除 {len(fact) - len(cleaned):,} 筆離群交易。"
        )

    st.markdown("### Top 客戶 / Top customers")
    st.dataframe(
        by_customer(fact).sort_values("gross_profit_usd", ascending=False).head(20),
        use_container_width=True,
    )

    st.markdown("### 產業別 / Industry breakdown")
    st.dataframe(by_industry(fact), use_container_width=True)

    st.markdown("### 系列 × 客戶分級 毛利率熱力圖 / Family × Tier margin heatmap")
    st.plotly_chart(heatmap(product_customer_matrix(fact)), use_container_width=True)
