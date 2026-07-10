from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import heatmap, margin_histogram_overlay, tier_performance_colors
from config.settings import CUSTOMER_TIERS
from src.analytics.dimension_analysis import by_customer, by_industry, product_customer_matrix
from src.analytics.metrics import iqr_filter


def render_customer(fact: pd.DataFrame) -> None:
    st.markdown("### 毛利率分布（依客戶分級）/ Margin distribution by tier")

    tiers = [t for t in CUSTOMER_TIERS if t in fact["customer_tier"].unique()]
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
        # Colors follow margin performance across ALL tiers in view (green =
        # best margin, red = worst), so deselecting a tier doesn't repaint
        # the survivors.
        color_map = tier_performance_colors(fact)
        shown = fact[fact["customer_tier"].isin(selected)]
        cleaned = iqr_filter(shown, "gross_margin_pct", group_col="customer_tier")
        st.plotly_chart(
            margin_histogram_overlay(
                cleaned,
                group_col="customer_tier",
                color_map=color_map,
                facet=mode.startswith("分面"),
            ),
            use_container_width=True,
        )
        st.caption(
            f"顏色＝毛利率表現：🟢 最高、🟡 次高、🔴 最低（以營收加權毛利率排名）。"
            f"已依 IQR 檢定移除 {len(shown) - len(cleaned):,} 筆離群交易。"
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
