from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import revenue_margin_trend
from src.analytics.trend_analysis import add_period_over_period, monthly_trend, rolling_avg


def render_trend(fact: pd.DataFrame) -> None:
    monthly = monthly_trend(fact)

    st.markdown("### 月度趨勢 / Monthly trend")
    st.plotly_chart(revenue_margin_trend(monthly), use_container_width=True)

    window = st.slider("移動平均視窗 / Rolling window (months)", 2, 12, 3)
    st.markdown(f"### {window} 個月移動平均 / {window}-month rolling average")
    st.dataframe(rolling_avg(monthly, window=window), use_container_width=True)

    st.markdown("### MoM / YoY")
    st.dataframe(add_period_over_period(monthly), use_container_width=True)

    # TODO: PVM waterfall — src.analytics.trend_analysis.pvm_decomposition
