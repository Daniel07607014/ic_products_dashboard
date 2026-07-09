from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_cost(raw_tables: dict[str, pd.DataFrame]) -> None:
    costs = raw_tables["costs"].copy()
    products = raw_tables["products"][["product_id", "product_family"]]
    costs = costs.merge(products, on="product_id", how="left")

    latest_period = costs["period"].max()
    st.caption(f"最新月份 / Latest period: **{latest_period}**")
    latest = costs[costs["period"] == latest_period]

    st.markdown("### 各系列平均單顆成本組成 / Avg unit cost composition by family")
    family_avg = latest.groupby("product_family")[
        ["wafer_cost_usd", "packaging_cost_usd", "testing_cost_usd", "overhead_cost_usd", "royalty_cost_usd"]
    ].mean().reset_index()
    long = family_avg.melt(id_vars="product_family", var_name="cost_type", value_name="usd")
    st.plotly_chart(
        px.bar(long, x="product_family", y="usd", color="cost_type", height=420),
        use_container_width=True,
    )

    st.markdown("### 良率 vs 單顆總成本 / Yield vs unit cost")
    st.plotly_chart(
        px.scatter(latest, x="yield_rate", y="unit_cost_usd", color="product_family", height=420),
        use_container_width=True,
    )

    # TODO: cost vs price scatter — needs the fact table (join with sales)
