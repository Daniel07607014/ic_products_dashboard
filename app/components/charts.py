"""Plotly chart helpers. Keep chart config here so pages stay short."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.settings import PRODUCT_FAMILIES

# Fixed color assignments so the same entity is the same color on every chart.
# Values come from the dataviz-validated categorical palette (slots 1-5, fixed
# order — worst adjacent CVD dE 24.2) — do not reorder or cycle.
_FAMILY_SLOTS = ("#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7")
FAMILY_COLORS: dict[str, str] = dict(zip(PRODUCT_FAMILIES, _FAMILY_SLOTS))

# Status colors (good/warning/critical) — tiers are colored by margin
# performance rank, not identity: best margin = green, middle = yellow,
# worst = red. See tier_performance_colors().
_PERFORMANCE_STEPS = ("#0ca30c", "#fab219", "#d03b3b")

# Status red for threshold lines — reserved, never used as a series color.
CRITICAL_COLOR = "#d03b3b"


def tier_performance_colors(fact: pd.DataFrame) -> dict[str, str]:
    """Map each customer tier to green/yellow/red by revenue-weighted margin rank."""
    grouped = fact.groupby("customer_tier")[["revenue_usd", "gross_profit_usd"]].sum()
    margin = grouped["gross_profit_usd"] / grouped["revenue_usd"].where(grouped["revenue_usd"] > 0)
    ranked = margin.sort_values(ascending=False).index.tolist()
    return {tier: _PERFORMANCE_STEPS[i] for i, tier in enumerate(ranked[: len(_PERFORMANCE_STEPS)])}


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
        color_discrete_map=FAMILY_COLORS,
        orientation="h",
        height=420,
    )
    return fig


def margin_distribution(product_df: pd.DataFrame) -> go.Figure:
    fig = px.box(
        product_df,
        x="product_family",
        y="gross_margin_pct",
        color="product_family",
        color_discrete_map=FAMILY_COLORS,
        points="all",
        height=420,
    )
    fig.update_layout(showlegend=False)
    return fig


def margin_histogram_overlay(
    df: pd.DataFrame,
    group_col: str,
    color_map: dict[str, str],
    nbins: int = 30,
    facet: bool = False,
) -> go.Figure:
    """Transaction-level gross-margin distributions, one trace per group.

    histnorm='percent' so groups with very different transaction counts stay
    comparable — raw counts would just show which group has more orders.
    """
    # Keep the legend/facet order stable (= color_map order), not data order.
    order = [g for g in color_map if g in df[group_col].unique()]
    fig = px.histogram(
        df,
        x="gross_margin_pct",
        color=group_col,
        color_discrete_map=color_map,
        category_orders={group_col: order},
        nbins=nbins,
        histnorm="percent",
        barmode="overlay",
        facet_col=group_col if facet else None,
        height=420,
    )
    fig.update_traces(opacity=1.0 if facet else 0.55)
    if facet:
        # Panels are self-labelling: each x-title carries the group name, so
        # the legend and the "group_col=value" strip annotations are noise.
        fig.update_layout(showlegend=False, yaxis_title="占比 % / Share of group")
        fig.layout.annotations = ()
        for i, group in enumerate(order):
            axis = "xaxis" if i == 0 else f"xaxis{i + 1}"
            fig.layout[axis].title.text = f"{group} Gross Margin %"
    else:
        fig.update_layout(
            xaxis_title="Gross Margin %",
            yaxis_title="占比 % / Share of group",
            legend=dict(orientation="h", y=1.12),
        )
    return fig


def heatmap(matrix: pd.DataFrame, title: str = "") -> go.Figure:
    fig = px.imshow(matrix, text_auto=".1f", aspect="auto", height=420, title=title)
    return fig
