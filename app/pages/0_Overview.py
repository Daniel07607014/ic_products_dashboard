from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.permissions import require_role  # noqa: E402
from app.components.charts import revenue_margin_trend, top_products_bar  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import sidebar_filters  # noqa: E402
from app.components.kpi_cards import render_concentration_kpis, render_kpi_row  # noqa: E402
from src.analytics.dimension_analysis import by_customer, by_product  # noqa: E402
from src.analytics.metrics import portfolio_kpis  # noqa: E402
from src.analytics.ranking import concentration_index, top_n_products, top_n_share  # noqa: E402
from src.analytics.risk import (  # noqa: E402
    declining_margin_products,
    low_margin_customers,
    low_margin_products,
    npi_health,
)
from src.analytics.trend_analysis import monthly_trend  # noqa: E402

require_role("viewer")

st.title("Overview · 總覽")

fact = sidebar_filters(get_fact_table(), show=("date",))

if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

render_kpi_row(portfolio_kpis(fact))

render_concentration_kpis(
    customer_hhi=concentration_index(fact, dimension="customer_id"),
    product_hhi=concentration_index(fact, dimension="product_id"),
    top5_customer_share_pct=top_n_share(fact, dimension="customer_id", n=5),
    top5_product_share_pct=top_n_share(fact, dimension="product_id", n=5),
)

st.markdown("### 月度營收與毛利率 / Monthly revenue & GM%")
st.plotly_chart(revenue_margin_trend(monthly_trend(fact)), use_container_width=True)

st.markdown("### Top 10 產品毛利貢獻 / Top 10 gross-profit contributors")
st.plotly_chart(
    top_products_bar(top_n_products(fact, n=10, by="gross_profit_usd")),
    use_container_width=True,
)

st.markdown("### 🔎 常用分析 / Quick views")
tab_low_margin, tab_declining, tab_top_sellers, tab_concentration, tab_npi = st.tabs(
    ["⚠️ 毛利率過低", "📉 毛利率下滑", "🏆 主力產品排行", "👥 客戶集中度 Top 5", "🆕 NPI 產品體質"]
)

with tab_low_margin:
    threshold = st.number_input("毛利率門檻 % / Margin threshold %", min_value=0.0, max_value=100.0, value=10.0)
    col_p, col_c = st.columns(2)
    with col_p:
        st.markdown("**低毛利產品 / Low-margin products**")
        st.dataframe(low_margin_products(fact, threshold_pct=threshold), use_container_width=True)
    with col_c:
        st.markdown("**低毛利客戶 / Low-margin customers**")
        st.dataframe(low_margin_customers(fact, threshold_pct=threshold), use_container_width=True)

with tab_declining:
    st.markdown("**毛利率下滑產品 / Products with declining margin (recent 3mo vs prior 3mo)**")
    st.dataframe(declining_margin_products(fact), use_container_width=True)

with tab_top_sellers:
    SORT_OPTIONS = {
        "銷量 / Quantity": "quantity",
        "營收 / Revenue": "revenue_usd",
        "毛利 / Gross Profit": "gross_profit_usd",
        "毛利率 / Gross Margin %": "gross_margin_pct",
    }
    col_sort, col_n = st.columns([3, 1])
    with col_sort:
        sort_choice = st.radio("排序依據 / Sort by", list(SORT_OPTIONS), horizontal=True)
    with col_n:
        top_n = st.slider("顯示前 N 名 / Top N", 5, 50, 10, step=5)

    sort_col = SORT_OPTIONS[sort_choice]
    st.dataframe(
        by_product(fact)
        .sort_values(sort_col, ascending=False)
        .head(top_n)[["product_id", "product_family", sort_col]]
        .reset_index(drop=True),
        use_container_width=True,
    )

with tab_concentration:
    top5 = by_customer(fact).sort_values("revenue_usd", ascending=False).head(5).copy()
    total_revenue = fact["revenue_usd"].sum()
    top5["revenue_share_pct"] = (top5["revenue_usd"] / total_revenue * 100) if total_revenue > 0 else 0.0
    st.dataframe(top5, use_container_width=True)

with tab_npi:
    st.dataframe(npi_health(fact), use_container_width=True)
