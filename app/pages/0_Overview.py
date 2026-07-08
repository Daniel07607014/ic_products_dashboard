from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.authenticator import require_login  # noqa: E402
from app.auth.permissions import require_role  # noqa: E402
from app.components.charts import revenue_margin_trend, top_products_bar  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import sidebar_filters  # noqa: E402
from app.components.kpi_cards import render_kpi_row  # noqa: E402
from src.analytics.metrics import portfolio_kpis  # noqa: E402
from src.analytics.ranking import top_n_products  # noqa: E402
from src.analytics.trend_analysis import monthly_trend  # noqa: E402

st.set_page_config(page_title="Overview", page_icon=":bar_chart:", layout="wide")
require_login()
require_role("viewer")

st.title("Overview · 總覽")

fact = sidebar_filters(get_fact_table())

if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

render_kpi_row(portfolio_kpis(fact))

st.markdown("### 月度營收與毛利率 / Monthly revenue & GM%")
st.plotly_chart(revenue_margin_trend(monthly_trend(fact)), use_container_width=True)

st.markdown("### Top 10 產品毛利貢獻 / Top 10 gross-profit contributors")
st.plotly_chart(
    top_products_bar(top_n_products(fact, n=10, by="gross_profit_usd")),
    use_container_width=True,
)
