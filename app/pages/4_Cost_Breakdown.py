from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.authenticator import require_login  # noqa: E402
from app.auth.permissions import require_role  # noqa: E402
from app.components.data_loader import get_raw_tables  # noqa: E402

st.set_page_config(page_title="Cost Breakdown", page_icon=":money_with_wings:", layout="wide")
require_login()
require_role("viewer")

st.title("Cost Breakdown · 成本結構")

tables = get_raw_tables()
costs = tables["costs"].copy()
products = tables["products"][["product_id", "product_family"]]
costs = costs.merge(products, on="product_id", how="left")

latest_period = costs["period"].max()
st.caption(f"最新月份 / Latest period: **{latest_period}**")
latest = costs[costs["period"] == latest_period]

st.markdown("### 各系列平均單顆成本組成 / Avg unit cost composition by family")
family_avg = latest.groupby("product_family")[
    ["wafer_cost_usd", "packaging_cost_usd", "testing_cost_usd", "overhead_cost_usd", "royalty_cost_usd"]
].mean().reset_index()
long = family_avg.melt(id_vars="product_family", var_name="cost_type", value_name="usd")
st.plotly_chart(
    px.bar(long, x="product_family", y="usd", color="cost_type", height=420),
    use_container_width=True,
)

st.markdown("### 良率 vs 單顆總成本 / Yield vs unit cost")
st.plotly_chart(
    px.scatter(latest, x="yield_rate", y="unit_cost_usd", color="product_family", height=420),
    use_container_width=True,
)

# TODO: cost vs price scatter — needs the fact table (join with sales)
