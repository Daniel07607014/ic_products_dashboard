from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.authenticator import require_login  # noqa: E402
from app.auth.permissions import require_role  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import sidebar_filters  # noqa: E402

st.set_page_config(page_title="Detail Query", page_icon=":mag:", layout="wide")
require_login()
require_role("viewer")

st.title("Detail Query · 明細查詢")

fact = sidebar_filters(get_fact_table())

col1, col2 = st.columns(2)
with col1:
    product_filter = st.text_input("料號關鍵字 / Product ID contains")
with col2:
    customer_filter = st.text_input("客戶關鍵字 / Customer name contains")

df = fact
if product_filter:
    df = df[df["product_id"].str.contains(product_filter, case=False, na=False)]
if customer_filter:
    df = df[df["customer_name"].str.contains(customer_filter, case=False, na=False)]

st.caption(f"{len(df):,} 筆交易 / rows")
st.dataframe(df, use_container_width=True, height=500)

st.download_button(
    "下載 CSV / Download CSV",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="ic_dashboard_detail.csv",
    mime="text/csv",
)
