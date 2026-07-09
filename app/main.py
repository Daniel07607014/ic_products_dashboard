"""Entrypoint: ``streamlit run app/main.py``.

Uses ``st.navigation`` so the sidebar only reveals dashboard pages after
the user signs in. Unauthenticated users see a single Login page.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.auth.authenticator import (  # noqa: E402
    is_authenticated,
    render_login,
    render_sidebar_user_info,
)

st.set_page_config(
    page_title="IC 產品毛利率 Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not is_authenticated():
    login_page = st.Page(
        render_login,
        title="登入 / Login",
        icon=":material/lock:",
        default=True,
    )
    pg = st.navigation([login_page], position="hidden")
else:
    render_sidebar_user_info()

    overview = st.Page(
        "pages/0_Overview.py",
        title="Overview · 總覽",
        icon=":material/dashboard:",
        default=True,
    )
    performance = st.Page(
        "pages/1_Performance.py",
        title="業績分析 / Performance",
        icon=":material/trending_up:",
    )
    cost = st.Page(
        "pages/2_Cost.py",
        title="成本與體質 / Cost",
        icon=":material/paid:",
    )
    data = st.Page(
        "pages/3_Data.py",
        title="資料與管理 / Data",
        icon=":material/search:",
    )

    nav: dict[str, list[st.Page]] = {
        "🏠 首頁": [overview],
        "📊 分析": [performance, cost],
        "🔎 資料": [data],
    }
    pg = st.navigation(nav)

pg.run()
