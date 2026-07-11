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
from app.auth.permissions import has_role  # noqa: E402

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
    product = st.Page(
        "pages/1_Product.py",
        title="產品分析 / Product",
        icon=":material/memory:",
    )
    customer = st.Page(
        "pages/2_Customer.py",
        title="客戶分析 / Customer",
        icon=":material/handshake:",
    )
    key_accounts = st.Page(
        "pages/6_Key_Accounts.py",
        title="重點客戶 / Key Accounts",
        icon=":material/star:",
    )
    trend = st.Page(
        "pages/3_Trend.py",
        title="趨勢分析 / Trend",
        icon=":material/trending_up:",
    )
    cost = st.Page(
        "pages/4_Cost.py",
        title="成本與體質 / Cost",
        icon=":material/paid:",
    )
    nav: dict[str, list[st.Page]] = {
        "🏠 首頁": [overview],
        "📊 分析": [product, customer, key_accounts, trend, cost],
    }
    if has_role("admin"):
        admin = st.Page(
            "pages/5_Admin.py",
            title="權限管理 / Admin",
            icon=":material/admin_panel_settings:",
        )
        nav["⚙️ 管理"] = [admin]
    pg = st.navigation(nav)

pg.run()
