from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.permissions import require_role  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import render_filters  # noqa: E402
from app.components.views.key_accounts import render_key_accounts  # noqa: E402

require_role("viewer")

st.title("重點客戶 · Key Accounts")
st.caption("誰是我們的衣食父母？他們的表現配得上這個地位嗎？")

fact = render_filters(get_fact_table(), show=("date",))
if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

render_key_accounts(fact)
