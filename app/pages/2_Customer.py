from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.permissions import require_role  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import sidebar_filters  # noqa: E402
from app.components.views.customer import render_customer  # noqa: E402

require_role("viewer")

st.title("客戶分析 · Customer")
st.caption("誰在賺？大客戶跟小客戶的毛利率差多少？")

fact = sidebar_filters(get_fact_table())
if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

render_customer(fact)
