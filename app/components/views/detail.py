from __future__ import annotations

import pandas as pd
import streamlit as st


def render_detail(fact: pd.DataFrame) -> None:
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
