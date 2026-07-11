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


def revenue_margin_trend(monthly: pd.DataFrame, ma_window: int | None = None) -> go.Figure:
    """Monthly revenue bars + GM% line; optionally overlay rolling means.

    `ma_window` expects the columns produced by
    :func:`src.analytics.trend_analysis.rolling_avg` (``*_ma{window}``).
    """
    fig = go.Figure()
    fig.add_bar(x=monthly["period"], y=monthly["revenue_usd"], name="Revenue (USD)")
    fig.add_scatter(
        x=monthly["period"],
        y=monthly["gross_margin_pct"],
        name="Gross Margin %",
        yaxis="y2",
        mode="lines+markers",
    )
    if ma_window:
        fig.add_scatter(
            x=monthly["period"],
            y=monthly[f"revenue_usd_ma{ma_window}"],
            name=f"Revenue {ma_window}M MA",
            mode="lines",
            line=dict(dash="dash", width=2, color="#0b0b0b"),
        )
        fig.add_scatter(
            x=monthly["period"],
            y=monthly[f"gross_margin_pct_ma{ma_window}"],
            name=f"GM% {ma_window}M MA",
            yaxis="y2",
            mode="lines",
            line=dict(dash="dot", width=2, color="#52514e"),
        )
    fig.update_layout(
        yaxis=dict(title="Revenue (USD)"),
        yaxis2=dict(title="Gross Margin %", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", y=1.1),
        height=420,
    )
    return fig


def growth_bars(monthly: pd.DataFrame, col: str, title: str) -> go.Figure:
    """Period-over-period growth as zero-baseline bars, green up / red down."""
    values = monthly[col]
    fig = go.Figure(
        go.Bar(
            x=monthly["period"],
            y=values,
            marker_color=["#0ca30c" if v >= 0 else "#d03b3b" for v in values.fillna(0)],
        )
    )
    fig.add_hline(y=0, line_color="#c3c2b7")
    fig.update_layout(
        yaxis_title=f"{title} %",
        xaxis_title="月份 / Period",
        height=380,
        showlegend=False,
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


def margin_distribution(
    df: pd.DataFrame,
    group_col: str = "product_family",
    color_map: dict[str, str] | None = None,
) -> go.Figure:
    color_map = color_map or FAMILY_COLORS
    fig = px.box(
        df,
        x=group_col,
        y="gross_margin_pct",
        color=group_col,
        color_discrete_map=color_map,
        category_orders={group_col: list(color_map)},
        points=False,
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


def family_trend_lines(
    df: pd.DataFrame,
    y_col: str,
    y_title: str,
    group_col: str = "product_family",
    color_map: dict[str, str] | None = None,
) -> go.Figure:
    """Monthly series, one line per group, in fixed per-entity colors."""
    color_map = color_map or FAMILY_COLORS
    fig = px.line(
        df,
        x="period",
        y=y_col,
        color=group_col,
        color_discrete_map=color_map,
        category_orders={group_col: list(color_map)},
        markers=True,
        height=420,
    )
    fig.update_traces(line_width=2, marker_size=6)
    fig.update_layout(
        xaxis_title="月份 / Period",
        yaxis_title=y_title,
        legend=dict(orientation="h", y=1.12),
    )
    return fig


def heatmap(matrix: pd.DataFrame, title: str = "") -> go.Figure:
    fig = px.imshow(matrix, text_auto=".1f", aspect="auto", height=420, title=title)
    return fig
