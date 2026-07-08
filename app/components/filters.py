"""Common sidebar filters shared across pages."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def sidebar_filters(fact: pd.DataFrame) -> pd.DataFrame:
    """Render date / family / tier filters in the sidebar and return the filtered fact table."""
    st.sidebar.markdown("### 篩選 / Filters")

    min_date = fact["order_date"].min()
    max_date = fact["order_date"].max()
    date_range = st.sidebar.date_input(
        "日期區間 / Date range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )

    families = sorted(fact["product_family"].dropna().unique().tolist())
    selected_families = st.sidebar.multiselect(
        "產品系列 / Product family", families, default=families
    )

    tiers = sorted(fact["customer_tier"].dropna().unique().tolist())
    selected_tiers = st.sidebar.multiselect(
        "客戶分級 / Customer tier", tiers, default=tiers
    )

    mask = fact["product_family"].isin(selected_families) & fact["customer_tier"].isin(selected_tiers)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        mask &= (fact["order_date"] >= pd.Timestamp(start)) & (fact["order_date"] <= pd.Timestamp(end))

    return fact.loc[mask].copy()
