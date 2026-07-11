from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import FAMILY_COLORS, margin_distribution, margin_histogram_overlay
from src.analytics.dimension_analysis import by_family, by_process_node, by_product
from src.analytics.metrics import iqr_filter


def render_product(fact: pd.DataFrame) -> None:
    st.markdown("### 毛利率分布 / Margin distribution")

    # Options follow the sidebar-filtered fact so a family the sidebar removed
    # never shows up here as a dead button.
    families = [f for f in FAMILY_COLORS if f in fact["product_family"].unique()]
    selected = st.pills(
        "顯示系列 / Families shown",
        options=families,
        default=families,
        selection_mode="multi",
    )

    mode = st.radio(
        "顯示方式 / Display",
        ["疊圖直方圖 / Overlay", "分面直方圖 / Facet", "箱型圖 / Box"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if not selected:
        st.info("請至少選擇一個系列 / Select at least one family.")
    else:
        shown = fact[fact["product_family"].isin(selected)]
        if mode.startswith("箱型圖"):
            # Same Tukey-fence policy as the histograms, but at product level
            # since each box point is one product.
            product_df = by_product(shown)
            cleaned_products = iqr_filter(product_df, "gross_margin_pct", group_col="product_family")
            st.plotly_chart(
                margin_distribution(cleaned_products), use_container_width=True
            )
            st.caption(
                f"已依 IQR 檢定移除 {len(product_df) - len(cleaned_products):,} 顆離群料號 / "
                f"outlier products removed (1.5×IQR, per family)"
            )
        else:
            # Tukey fence per family: an extreme margin for a volatile family
            # may be normal for another, so fences are group-wise.
            cleaned = iqr_filter(shown, "gross_margin_pct", group_col="product_family")
            st.plotly_chart(
                margin_histogram_overlay(
                    cleaned,
                    group_col="product_family",
                    color_map=FAMILY_COLORS,
                    facet=mode.startswith("分面"),
                ),
                use_container_width=True,
            )
            st.caption(
                f"已依 IQR 檢定移除 {len(shown) - len(cleaned):,} 筆離群交易 / "
                f"outliers removed by Tukey fence (1.5×IQR, per family)"
            )

    st.markdown("### 明細 / Tables")
    tab_family, tab_node, tab_sku = st.tabs(
        ["產品系列 / Family", "製程節點 / Node", "料號排行 / SKU"]
    )

    with tab_family:
        st.dataframe(by_family(fact), use_container_width=True)

    with tab_node:
        st.dataframe(by_process_node(fact), use_container_width=True)

    with tab_sku:
        product_df = by_product(fact).sort_values("gross_profit_usd", ascending=False)
        st.dataframe(product_df, use_container_width=True, height=500)

# TODO: drill-down into a single product (cost/price trend, top customers)
