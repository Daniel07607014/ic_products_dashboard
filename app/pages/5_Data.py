from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.permissions import has_role, require_role  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import render_filters  # noqa: E402
from app.components.views.admin import render_admin  # noqa: E402
from app.components.views.detail import render_detail  # noqa: E402

require_role("viewer")

st.title("資料與管理 · Data")

show_admin = has_role("admin")
tab_labels = [":mag: 明細查詢 / Detail"]
if show_admin:
    tab_labels.append(":lock: 使用者管理 / Admin")

tabs = st.tabs(tab_labels)

with tabs[0]:
    fact = render_filters(get_fact_table())
    render_detail(fact)

if show_admin:
    with tabs[1]:
        render_admin()
