"""Plotly chart helpers. Keep chart config here so pages stay short."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def revenue_margin_trend(monthly: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=monthly["period"], y=monthly["revenue_usd"], name="Revenue (USD)")
    fig.add_scatter(
        x=monthly["period"],
        y=monthly["gross_margin_pct"],
        name="Gross Margin %",
        yaxis="y2",
        mode="lines+markers",
    )
    fig.update_layout(
        yaxis=dict(title="Revenue (USD)"),
        yaxis2=dict(title="Gross Margin %", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", y=1.1),
        height=420,
    )
    return fig


def top_products_bar(top_df: pd.DataFrame, value_col: str = "gross_profit_usd") -> go.Figure:
    fig = px.bar(
        top_df.sort_values(value_col),
        x=value_col,
        y="product_id",
        color="product_family",
        orientation="h",
        height=420,
    )
    return fig


def margin_distribution(product_df: pd.DataFrame) -> go.Figure:
    fig = px.box(product_df, x="product_family", y="gross_margin_pct", points="all", height=420)
    return fig


def heatmap(matrix: pd.DataFrame, title: str = "") -> go.Figure:
    fig = px.imshow(matrix, text_auto=".1f", aspect="auto", height=420, title=title)
    return fig
