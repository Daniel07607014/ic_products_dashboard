from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.charts import CRITICAL_COLOR, FAMILY_COLORS


def render_cost(raw_tables: dict[str, pd.DataFrame]) -> None:
    costs = raw_tables["costs"].copy()
    products = raw_tables["products"][["product_id", "product_name", "product_family"]]
    costs = costs.merge(products, on="product_id", how="left")

    latest_period = costs["period"].max()
    st.caption(f"最新月份 / Latest period: **{latest_period}**")
    latest = costs[costs["period"] == latest_period]

    st.markdown("### 各系列平均單位成本組成 / Avg unit cost composition by family")
    family_avg = latest.groupby("product_family")[
        ["wafer_cost_usd", "packaging_cost_usd", "testing_cost_usd", "overhead_cost_usd", "royalty_cost_usd"]
    ].mean().reset_index()
    long = family_avg.melt(id_vars="product_family", var_name="cost_type", value_name="usd")
    st.plotly_chart(
        px.bar(long, x="product_family", y="usd", color="cost_type", height=420),
        use_container_width=True,
    )

    st.markdown("### 良率 vs 單位成本 / Yield vs unit cost")
    plot_df = latest.copy()
    # Only the problem parts get an on-chart label — labelling all 80 dots
    # would be unreadable; the rest are identifiable on hover.
    plot_df["label"] = plot_df["product_id"].where(plot_df["yield_rate"] < 0.90, "")
    fig = px.scatter(
        plot_df,
        x="unit_cost_usd",
        y="yield_rate",
        color="product_family",
        color_discrete_map=FAMILY_COLORS,
        text="label",
        hover_name="product_id",
        hover_data={"product_name": True, "yield_rate": ":.1%", "unit_cost_usd": ":.3f", "label": False},
        height=460,
    )
    fig.update_traces(textposition="top center", textfont_size=10)
    # 90% 是良率健康線：線下的產品該優先追良率改善
    fig.add_hline(y=0.90, line_dash="dash", line_color=CRITICAL_COLOR,
                  annotation_text="90%", annotation_position="right")
    st.plotly_chart(fig, use_container_width=True)

    low_yield = latest[latest["yield_rate"] < 0.90].sort_values("yield_rate")
    if not low_yield.empty:
        st.markdown("**⚠️ 良率低於 90% 的零件 / Parts below 90% yield**")
        st.dataframe(
            low_yield[["product_id", "product_name", "product_family", "yield_rate", "unit_cost_usd"]]
            .reset_index(drop=True),
            use_container_width=True,
        )

    # TODO: cost vs price scatter — needs the fact table (join with sales)
