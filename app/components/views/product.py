from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import margin_distribution
from src.analytics.dimension_analysis import by_family, by_process_node, by_product


def render_product(fact: pd.DataFrame) -> None:
    sub_family, sub_node, sub_sku, sub_dist = st.tabs(
        ["產品系列 / Family", "製程節點 / Node", "料號排行 / SKU", "毛利率分布 / Distribution"]
    )

    with sub_family:
        st.dataframe(by_family(fact), use_container_width=True)

    with sub_node:
        st.dataframe(by_process_node(fact), use_container_width=True)

    with sub_sku:
        product_df = by_product(fact).sort_values("gross_profit_usd", ascending=False)
        st.dataframe(product_df, use_container_width=True, height=500)

    with sub_dist:
        st.plotly_chart(margin_distribution(by_product(fact)), use_container_width=True)
