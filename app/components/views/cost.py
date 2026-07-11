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
    # Median, not (weighted) mean: cost is right-skewed by a few advanced-node
    # parts, and the question here is "expensive vs peers", not portfolio mix.
    median_cost = float(plot_df["unit_cost_usd"].median())
    # Label only the bottom-right quadrant (expensive AND low-yield) — the
    # priority group; everything else is identifiable on hover.
    in_bad_quadrant = (plot_df["yield_rate"] < 0.90) & (plot_df["unit_cost_usd"] > median_cost)
    plot_df["label"] = plot_df["product_id"].where(in_bad_quadrant, "")
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
    fig.add_vline(x=median_cost, line_dash="dash", line_color=CRITICAL_COLOR,
                  annotation_text=f"中位數 ${median_cost:.2f}", annotation_position="top")
    fig.add_shape(  # bottom-right quadrant = expensive & low-yield
        type="rect",
        x0=median_cost, x1=float(plot_df["unit_cost_usd"].max()) * 1.02,
        y0=float(plot_df["yield_rate"].min()) * 0.99, y1=0.90,
        fillcolor=CRITICAL_COLOR, opacity=0.07, line_width=0, layer="below",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("右下淡紅區＝成本高於中位數且良率 <90% 的優先改善族群，僅此區標註料號。")

    low_yield = latest[latest["yield_rate"] < 0.90].sort_values("yield_rate")
    if not low_yield.empty:
        st.markdown("**⚠️ 良率低於 90% 的零件 / Parts below 90% yield**")
        st.dataframe(
            low_yield[["product_id", "product_name", "product_family", "yield_rate", "unit_cost_usd"]]
            .reset_index(drop=True),
            use_container_width=True,
        )

    # TODO: cost vs price scatter — needs the fact table (join with sales)
