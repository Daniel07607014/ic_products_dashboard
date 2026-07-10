from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import TIER_COLORS, heatmap, margin_histogram_overlay
from src.analytics.dimension_analysis import by_customer, by_industry, product_customer_matrix


def render_customer(fact: pd.DataFrame) -> None:
    st.markdown("### 毛利率分布（依客戶分級）/ Margin distribution by tier")

    tiers = [t for t in TIER_COLORS if t in fact["customer_tier"].unique()]
    selected = st.pills(
        "顯示分級 / Tiers shown",
        options=tiers,
        default=tiers,
        selection_mode="multi",
    )

    mode = st.radio(
        "顯示方式 / Display",
        ["疊圖直方圖 / Overlay", "分面直方圖 / Facet"],
        horizontal=True,
        label_visibility="collapsed",
        key="customer_display_mode",
    )

    if not selected:
        st.info("請至少選擇一個分級 / Select at least one tier.")
    else:
        shown = fact[fact["customer_tier"].isin(selected)]
        nbins = st.slider("直方圖分箱數 / Bins", 10, 60, 30, step=5, key="customer_bins")
        st.plotly_chart(
            margin_histogram_overlay(
                shown,
                group_col="customer_tier",
                color_map=TIER_COLORS,
                nbins=nbins,
                facet=mode.startswith("分面"),
            ),
            use_container_width=True,
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
