from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.authenticator import require_login  # noqa: E402
from app.auth.permissions import require_role  # noqa: E402
from app.components.charts import margin_distribution  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import sidebar_filters  # noqa: E402
from src.analytics.dimension_analysis import by_family, by_process_node, by_product  # noqa: E402

st.set_page_config(page_title="Product Analysis", page_icon=":microchip:", layout="wide")
require_login()
require_role("viewer")

st.title("Product Analysis · 產品分析")

fact = sidebar_filters(get_fact_table())
if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

tab_family, tab_node, tab_product, tab_distribution = st.tabs(
    ["產品系列 / Family", "製程節點 / Node", "料號排行 / SKU", "毛利率分布 / Distribution"]
)

with tab_family:
    st.dataframe(by_family(fact), use_container_width=True)

with tab_node:
    st.dataframe(by_process_node(fact), use_container_width=True)

with tab_product:
    product_df = by_product(fact).sort_values("gross_profit_usd", ascending=False)
    st.dataframe(product_df, use_container_width=True, height=500)

with tab_distribution:
    st.plotly_chart(margin_distribution(by_product(fact)), use_container_width=True)

# TODO: drill-down into a single product (cost/price trend, top customers)
