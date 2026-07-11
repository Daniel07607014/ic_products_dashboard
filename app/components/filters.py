"""Common in-page filters shared across pages, rendered as one row above the charts."""
from __future__ import annotations

import pandas as pd
import streamlit as st

# Which filter widgets a page shows. Pages pass a subset so each page only
# exposes the dimensions it actually analyses (Overview: date only).
ALL_FILTERS = ("date", "family", "tier", "industry")


def render_filters(fact: pd.DataFrame, show: tuple[str, ...] = ALL_FILTERS) -> pd.DataFrame:
    """Render the requested filters at the top of the page and return the filtered fact table."""
    mask = pd.Series(True, index=fact.index)

    cols = st.columns(len(show)) if show else []
    slots = dict(zip(show, cols))

    if "date" in slots:
        with slots["date"]:
            min_date = fact["order_date"].min()
            max_date = fact["order_date"].max()
            date_range = st.date_input(
                "日期區間 / Date range",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date(),
            )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            mask &= (fact["order_date"] >= pd.Timestamp(start)) & (fact["order_date"] <= pd.Timestamp(end))

    if "family" in slots:
        with slots["family"]:
            families = sorted(fact["product_family"].dropna().unique().tolist())
            selected_families = st.multiselect(
                "產品系列 / Product family", families, default=families
            )
        mask &= fact["product_family"].isin(selected_families)

    if "tier" in slots:
        with slots["tier"]:
            tiers = sorted(fact["customer_tier"].dropna().unique().tolist())
            selected_tiers = st.multiselect(
                "客戶分級 / Customer tier", tiers, default=tiers
            )
        mask &= fact["customer_tier"].isin(selected_tiers)

    if "industry" in slots:
        with slots["industry"]:
            industries = sorted(fact["industry"].dropna().unique().tolist())
            selected_industries = st.multiselect(
                "產業別 / Industry", industries, default=industries
            )
        mask &= fact["industry"].isin(selected_industries)

    return fact.loc[mask].copy()


# Backward-compat alias so older pages keep working during the transition.
sidebar_filters = render_filters
