from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.permissions import require_role  # noqa: E402
from app.components.data_loader import get_raw_tables  # noqa: E402
from app.components.views.cost import render_cost  # noqa: E402

require_role("viewer")

st.title("成本與體質 · Cost")
st.caption("為什麼是這個毛利？")

tab_breakdown, = st.tabs([":money_with_wings: 成本結構 / Breakdown"])

with tab_breakdown:
    render_cost(get_raw_tables())

# 未來擴充：PVM waterfall、良率分析、單品 drill-down 都新增 tab 加在這裡
