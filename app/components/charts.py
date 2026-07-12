"""Plotly chart helpers. Keep chart config here so pages stay short."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.settings import INDUSTRIES, PRODUCT_FAMILIES

# Fixed color assignments so the same entity is the same color on every chart.
# Values come from the dataviz-validated categorical palette (slots 1-5, fixed
# order — worst adjacent CVD dE 24.2) — do not reorder or cycle.
_FAMILY_SLOTS = ("#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7")
FAMILY_COLORS: dict[str, str] = dict(zip(PRODUCT_FAMILIES, _FAMILY_SLOTS))

# Industries are unordered categories too — first four validated slots,
# assigned in the fixed settings.INDUSTRIES order.
INDUSTRY_COLORS: dict[str, str] = dict(zip(INDUSTRIES, _FAMILY_SLOTS[:4]))

# Status red for threshold lines — reserved, never used as a series color.
CRITICAL_COLOR = "#d03b3b"

# Cost stack components: display names + palette slots (fixed order = stack order).
COST_TYPES: dict[str, str] = {
    "wafer_cost_usd": "晶圓 / Wafer",
    "packaging_cost_usd": "封裝 / Packaging",
    "testing_cost_usd": "測試 / Testing",
    "overhead_cost_usd": "製造費用 / Overhead",
    "royalty_cost_usd": "權利金 / Royalty",
}
COST_TYPE_COLORS: dict[str, str] = dict(zip(COST_TYPES.values(), _FAMILY_SLOTS))


def cost_composition_bar(family_avg_long: pd.DataFrame) -> go.Figure:
    """Stacked avg unit-cost composition per family. Expects columns
    product_family / cost_type (raw column names) / usd."""
    df = family_avg_long.copy()
    df["cost_type"] = df["cost_type"].map(COST_TYPES)
    fig = px.bar(
        df,
        x="product_family",
        y="usd",
        color="cost_type",
        color_discrete_map=COST_TYPE_COLORS,
        category_orders={"cost_type": list(COST_TYPES.values())},
        height=420,
    )
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="平均單位成本 (USD) / Avg unit cost",
        legend_title=None,
        legend=dict(orientation="h", y=1.12),
    )
    return fig


def customer_pareto_curve(abc_df: pd.DataFrame) -> go.Figure:
    """Cumulative revenue share, customers ranked biggest-first, with the
    80% / 95% ABC boundaries."""
    fig = px.line(
        abc_df,
        x="rank",
        y="cum_pct",
        markers=True,
        hover_name="customer_name",
        hover_data={"revenue_usd": ":,.0f", "abc_class": True, "rank": False},
        height=420,
    )
    fig.update_traces(line_width=2, marker_size=6, line_color="#2a78d6")
    fig.add_hline(y=80, line_dash="dash", line_color="#898781",
                  annotation_text="80% (A)", annotation_position="right")
    fig.add_hline(y=95, line_dash="dash", line_color="#898781",
                  annotation_text="95% (B)", annotation_position="right")
    fig.update_layout(
        xaxis_title="客戶排名（依營收）/ Customer rank by revenue",
        yaxis_title="累積營收佔比 % / Cumulative revenue share",
        yaxis_range=[0, 105],
    )
    return fig


def revenue_margin_trend(monthly: pd.DataFrame, ma_window: int | None = None) -> go.Figure:
    """Monthly revenue bars + GM% line; optionally overlay rolling means.

    `ma_window` expects the columns produced by
    :func:`src.analytics.trend_analysis.rolling_avg` (``*_ma{window}``).
    """
    fig = go.Figure()
    fig.add_bar(
        x=monthly["period"], y=monthly["revenue_usd"], name="Revenue (USD)",
        marker_color="#9ec5f4",  # light sequential step so the GM% line stays dominant
    )
    fig.add_scatter(
        x=monthly["period"],
        y=monthly["gross_margin_pct"],
        name="Gross Margin %",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#104281", width=2),
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
    # Auto-range the GM% axis: a fixed [0,100] squashed a ~±3pp swing into a
    # visually flat line, hiding exactly the movement this chart exists to show.
    fig.update_layout(
        yaxis=dict(title="Revenue (USD)"),
        yaxis2=dict(title="Gross Margin %", overlaying="y", side="right"),
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


def pvm_waterfall(pvm: dict[str, float], base_label: str, curr_label: str) -> go.Figure:
    """Gross-profit PVM waterfall: two absolute anchors + four signed effects.

    Polarity colors match growth_bars (green up / red down); the anchors use
    the recessive revenue-bar blue so the effects stay visually dominant.
    """
    effects = [
        ("價格 / Price", pvm["price_effect"]),
        ("成本 / Cost", pvm["cost_effect"]),
        ("數量 / Volume", pvm["volume_effect"]),
        ("組合 / Mix", pvm["mix_effect"]),
    ]
    x = [f"{base_label}<br>期初毛利"] + [name for name, _ in effects] + [f"{curr_label}<br>期末毛利"]
    y = [pvm["gross_profit_prev"]] + [v for _, v in effects] + [pvm["gross_profit_curr"]]
    fig = go.Figure(
        go.Waterfall(
            x=x,
            y=y,
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            text=[f"${v:,.0f}" for v in y],
            textposition="outside",
            increasing=dict(marker_color="#0ca30c"),
            decreasing=dict(marker_color="#d03b3b"),
            totals=dict(marker_color="#9ec5f4"),
            connector=dict(line=dict(color="#c3c2b7", width=1)),
        )
    )
    fig.update_layout(
        yaxis_title="毛利 (USD) / Gross profit",
        showlegend=False,
        height=440,
        # Outside-positioned labels on the tallest bar need headroom.
        margin=dict(t=48),
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
    # px orders categories by trace (= family), which visually clumps bars by
    # color; a ranking chart must rank, so force order by value.
    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
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
    fig.update_layout(
        showlegend=False,
        yaxis_title="毛利率 % / Gross Margin %",
        xaxis_title=None,
    )
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
    fig = px.imshow(
        matrix,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale="Oranges",  # warm single-hue sequential: light = low, dark = high
        height=420,
        title=title,
    )
    return fig
