from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.permissions import require_role  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import sidebar_filters  # noqa: E402
from app.components.views.customer import render_customer  # noqa: E402
from app.components.views.product import render_product  # noqa: E402
from app.components.views.trend import render_trend  # noqa: E402

require_role("viewer")

st.title("業績分析 · Performance")
st.caption("誰在賺？賣什麼賺？什麼時候賺？")

fact = sidebar_filters(get_fact_table())
if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

tab_product, tab_customer, tab_trend = st.tabs(
    [":microchip: 產品維度 / Product", ":handshake: 客戶維度 / Customer", ":chart_with_upwards_trend: 趨勢分析 / Trend"]
)

with tab_product:
    render_product(fact)

with tab_customer:
    render_customer(fact)

with tab_trend:
    render_trend(fact)
