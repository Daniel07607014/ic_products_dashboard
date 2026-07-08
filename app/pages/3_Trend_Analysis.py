from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.authenticator import require_login  # noqa: E402
from app.auth.permissions import require_role  # noqa: E402
from app.components.charts import revenue_margin_trend  # noqa: E402
from app.components.data_loader import get_fact_table  # noqa: E402
from app.components.filters import sidebar_filters  # noqa: E402
from src.analytics.trend_analysis import add_period_over_period, monthly_trend, rolling_avg  # noqa: E402

st.set_page_config(page_title="Trend Analysis", page_icon=":chart_with_upwards_trend:", layout="wide")
require_login()
require_role("viewer")

st.title("Trend Analysis · 趨勢分析")

fact = sidebar_filters(get_fact_table())
if fact.empty:
    st.warning("目前篩選條件下沒有資料 / No data under current filters.")
    st.stop()

monthly = monthly_trend(fact)

st.markdown("### 月度趨勢 / Monthly trend")
st.plotly_chart(revenue_margin_trend(monthly), use_container_width=True)

window = st.slider("移動平均視窗 / Rolling window (months)", 2, 12, 3)
st.markdown(f"### {window} 個月移動平均 / {window}-month rolling average")
st.dataframe(rolling_avg(monthly, window=window), use_container_width=True)

st.markdown("### MoM / YoY")
st.dataframe(add_period_over_period(monthly), use_container_width=True)

# TODO: PVM waterfall — src.analytics.trend_analysis.pvm_decomposition
