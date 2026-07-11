from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import FAMILY_COLORS, margin_distribution, margin_histogram_overlay
from src.analytics.dimension_analysis import by_family, by_process_node, by_product
from src.analytics.metrics import iqr_filter


def render_product(fact: pd.DataFrame) -> None:
    st.markdown("### 毛利率分布 / Margin distribution")

    # Which families appear is controlled by the page's Product-family
    # filter — no second in-chart selector.
    mode = st.radio(
        "顯示方式 / Display",
        ["分面直方圖 / Facet", "箱型圖 / Box"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if mode.startswith("箱型圖"):
        # Raw data on purpose — the box's whiskers already summarise spread,
        # and hiding outlier products here would hide real problem SKUs.
        st.plotly_chart(
            margin_distribution(by_product(fact)), use_container_width=True
        )
    else:
        # Tukey fence per family: an extreme margin for a volatile family
        # may be normal for another, so fences are group-wise.
        cleaned = iqr_filter(fact, "gross_margin_pct", group_col="product_family")
        st.plotly_chart(
            margin_histogram_overlay(
                cleaned,
                group_col="product_family",
                color_map=FAMILY_COLORS,
                facet=True,
            ),
            use_container_width=True,
        )
        st.caption(
            f"已依 IQR 檢定移除 {len(fact) - len(cleaned):,} 筆離群交易 / "
            f"outliers removed by Tukey fence (1.5×IQR, per family)"
        )

    st.markdown("### 明細 / Tables")
    tab_family, tab_node, tab_sku = st.tabs(
        ["產品系列 / Family", "製程節點 / Node", "料號排行 / SKU"]
    )

    with tab_family:
        st.caption(
            "**看什麼**：產品組合的體質。哪個系列是營收主力（revenue_usd 最大）、"
            "哪個是毛利率優等生（gross_margin_pct 最高）——兩者通常不是同一個。"
            "「量大毛利低」的系列扛規模、「量小毛利高」的系列扛獲利，組合失衡就是警訊。"
        )
        st.dataframe(by_family(fact), use_container_width=True)

    with tab_node:
        st.caption(
            "**看什麼**：製程世代的獲利結構。成熟製程（130/90nm）成本低但單價也低、"
            "先進製程（28/40nm）成本高但應該賺更多——如果先進製程的毛利率反而更差，"
            "代表定價沒把成本轉嫁出去，是產品定價策略的檢查點。"
        )
        st.dataframe(by_process_node(fact), use_container_width=True)

    with tab_sku:
        st.caption(
            "**看什麼**：單顆料號的毛利貢獻排行（由高到低）。最上面幾顆是金牛，"
            "要保護產能與交期；拉到最下面看毛利貢獻墊底甚至為負的料號——"
            "該漲價、該 cost-down、還是該 EOL，逐顆檢討。"
        )
        product_df = by_product(fact).sort_values("gross_profit_usd", ascending=False)
        st.dataframe(product_df, use_container_width=True, height=500)

# TODO: drill-down into a single product (cost/price trend, top customers)
