from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import heatmap
from src.analytics.dimension_analysis import by_customer, by_industry, product_customer_matrix


def render_customer(fact: pd.DataFrame) -> None:
    st.markdown("### Top 客戶 / Top customers")
    st.dataframe(
        by_customer(fact).sort_values("gross_profit_usd", ascending=False).head(20),
        use_container_width=True,
    )

    st.markdown("### 產業別 / Industry breakdown")
    st.dataframe(by_industry(fact), use_container_width=True)

    st.markdown("### 系列 × 客戶分級 毛利率熱力圖 / Family × Tier margin heatmap")
    st.plotly_chart(heatmap(product_customer_matrix(fact)), use_container_width=True)
