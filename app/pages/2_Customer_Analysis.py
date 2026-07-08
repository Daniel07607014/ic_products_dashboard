from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.authenticator import require_login  # noqa: E402
from app.auth.permissions import require_role  # noqa: E402
from app.components.charts import heatmap  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import sidebar_filters  # noqa: E402
from src.analytics.dimension_analysis import by_customer, by_industry, product_customer_matrix  # noqa: E402

st.set_page_config(page_title="Customer Analysis", page_icon=":handshake:", layout="wide")
require_login()
require_role("viewer")

st.title("Customer Analysis · 客戶分析")

fact = sidebar_filters(get_fact_table())
if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

st.markdown("### Top 客戶 / Top customers")
st.dataframe(
    by_customer(fact).sort_values("gross_profit_usd", ascending=False).head(20),
    use_container_width=True,
)

st.markdown("### 產業別 / Industry breakdown")
st.dataframe(by_industry(fact), use_container_width=True)

st.markdown("### 系列 × 客戶分級 毛利率熱力圖 / Family × Tier margin heatmap")
st.plotly_chart(heatmap(product_customer_matrix(fact)), use_container_width=True)
