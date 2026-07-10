"""Common sidebar filters shared across pages."""
from __future__ import annotations

import pandas as pd
import streamlit as st

# Which filter widgets a page shows. Pages pass a subset so each page only
# exposes the dimensions it actually analyses (Overview: date only).
ALL_FILTERS = ("date", "family", "tier")


def sidebar_filters(fact: pd.DataFrame, show: tuple[str, ...] = ALL_FILTERS) -> pd.DataFrame:
    """Render the requested filters in the sidebar and return the filtered fact table."""
    st.sidebar.markdown("### 篩選 / Filters")

    mask = pd.Series(True, index=fact.index)

    if "date" in show:
        min_date = fact["order_date"].min()
        max_date = fact["order_date"].max()
        date_range = st.sidebar.date_input(
            "日期區間 / Date range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            mask &= (fact["order_date"] >= pd.Timestamp(start)) & (fact["order_date"] <= pd.Timestamp(end))

    if "family" in show:
        families = sorted(fact["product_family"].dropna().unique().tolist())
        selected_families = st.sidebar.multiselect(
            "產品系列 / Product family", families, default=families
        )
        mask &= fact["product_family"].isin(selected_families)

    if "tier" in show:
        tiers = sorted(fact["customer_tier"].dropna().unique().tolist())
        selected_tiers = st.sidebar.multiselect(
            "客戶分級 / Customer tier", tiers, default=tiers
        )
        mask &= fact["customer_tier"].isin(selected_tiers)

    return fact.loc[mask].copy()
