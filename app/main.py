"""Entrypoint: ``streamlit run app/main.py``.

Handles login and shows a landing page. Real dashboards live under app/pages/.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.auth.authenticator import require_login  # noqa: E402

st.set_page_config(
    page_title="IC 產品毛利率 Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

name, username, roles = require_login()

st.title(":bar_chart: IC 產品毛利率 Dashboard")
st.markdown(
    f"歡迎 **{name}**！請從左側選單選擇分析頁面 / Welcome — pick a page from the sidebar."
)

st.markdown("---")
st.subheader("頁面導覽 / Pages")
st.markdown(
    """
    | 頁面 | 說明 |
    |---|---|
    | **0 · Overview** | 總覽 KPI、毛利率趨勢、Top 產品 |
    | **1 · Product Analysis** | 產品/系列/製程毛利分析 |
    | **2 · Customer Analysis** | 客戶、產業、地區維度 |
    | **3 · Trend Analysis** | 時間序列、MoM/YoY、PVM |
    | **4 · Cost Breakdown** | 成本結構、良率影響 |
    | **5 · Detail Query** | 明細查詢與下載 |
    | **9 · Admin** *(admin only)* | 使用者管理 |
    """
)
