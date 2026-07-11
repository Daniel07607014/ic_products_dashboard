from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.permissions import require_role  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import render_filters  # noqa: E402
from app.components.views.industry import render_industry  # noqa: E402

require_role("viewer")

st.title("產業別分析 · Industry")
st.caption("哪個市場的生意品質好？車用、工業、消費性、通訊的毛利率結構。")

fact = render_filters(get_fact_table(), show=("date", "industry"))
if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

render_industry(fact)
