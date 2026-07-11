from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import customer_pareto_curve, revenue_margin_trend
from src.analytics.dimension_analysis import by_customer, by_product
from src.analytics.ranking import abc_analysis
from src.analytics.trend_analysis import monthly_trend


def render_key_accounts(fact: pd.DataFrame) -> None:
    customers = by_customer(fact)

    st.markdown("### 營收集中度 / Revenue concentration (Pareto)")
    abc = abc_analysis(fact, dimension="customer_id")
    abc["rank"] = range(1, len(abc) + 1)
    abc = abc.merge(
        customers[["customer_id", "customer_name"]], on="customer_id", how="left"
    )
    st.plotly_chart(customer_pareto_curve(abc), use_container_width=True)
    n_a = int((abc["abc_class"] == "A").sum())
    st.caption(
        f"前 {n_a} 家客戶貢獻了 80% 營收——這就是「A 級」的定義依據。"
        f"曲線越陡＝依賴越集中，任一家 A 級流失的衝擊越大。"
    )

    st.markdown("### 單一客戶檢視 / Account drill-down")
    show_all = st.toggle("顯示全部客戶（含 B/C 級）/ Show all tiers", value=False)
    ordered = customers.sort_values("revenue_usd", ascending=False)
    if not show_all:
        ordered = ordered[ordered["customer_tier"] == "A"]
    if ordered.empty:
        st.info("目前篩選條件下沒有 A 級客戶 / No A-tier customers under current filters.")
        return
    target = st.selectbox(
        "選擇客戶（依營收排序）/ Customer",
        options=ordered["customer_id"].tolist(),
        format_func=lambda cid: (
            f"{ordered.set_index('customer_id').loc[cid, 'customer_name']}"
            f"（{ordered.set_index('customer_id').loc[cid, 'customer_tier']} 級）"
        ),
    )
    row = ordered.set_index("customer_id").loc[target]
    total_revenue = fact["revenue_usd"].sum()
    share = row["revenue_usd"] / total_revenue * 100 if total_revenue > 0 else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("營收 / Revenue", f"${row['revenue_usd']:,.0f}")
    c2.metric("佔總營收 / Share", f"{share:.1f}%")
    c3.metric("毛利率 / GM%", f"{row['gross_margin_pct']:.1f}%")
    c4.metric("分級 / Tier", str(row["customer_tier"]))
    c5.metric("產業 / Industry", str(row["industry"]))

    account_fact = fact[fact["customer_id"] == target]
    st.markdown("**月度營收與毛利率 / Monthly revenue & GM%**")
    st.plotly_chart(revenue_margin_trend(monthly_trend(account_fact)), use_container_width=True)

    st.markdown("**該客戶 Top 10 料號 / Top products bought**")
    st.dataframe(
        by_product(account_fact)
        .sort_values("revenue_usd", ascending=False)
        .head(10)[["product_id", "product_family", "revenue_usd", "gross_margin_pct", "quantity"]]
        .reset_index(drop=True),
        use_container_width=True,
    )
