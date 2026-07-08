"""Merge the five raw tables into one analysis-ready DataFrame.

The result of :func:`build_fact_table` is what every analytics function
should start from — it already carries cost, margin, customer and product
attributes per transaction row.
"""
from __future__ import annotations

import pandas as pd

from src.etl.clean import add_period_column, drop_invalid_sales, fill_yield_rate


def build_fact_table(
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sales: pd.DataFrame,
    costs: pd.DataFrame,
) -> pd.DataFrame:
    """Return one row per sales transaction, enriched with cost & margin.

    Columns added:
        - unit_cost_usd, cogs_usd, gross_profit_usd, gross_margin_pct
        - product attributes (family, node, package)
        - customer attributes (tier, industry, country)
        - period (YYYY-MM)
    """
    sales = drop_invalid_sales(sales)
    sales = add_period_column(sales)
    costs = fill_yield_rate(costs)

    fact = sales.merge(
        costs[["product_id", "period", "unit_cost_usd", "yield_rate"]],
        on=["product_id", "period"],
        how="left",
    )

    fact = fact.merge(
        products[["product_id", "product_family", "process_node", "package_type", "product_status"]],
        on="product_id",
        how="left",
    )

    fact = fact.merge(
        customers[["customer_id", "customer_name", "customer_tier", "industry", "country"]],
        on="customer_id",
        how="left",
    )

    fact["cogs_usd"] = fact["unit_cost_usd"] * fact["quantity"]
    fact["gross_profit_usd"] = fact["revenue_usd"] - fact["cogs_usd"]
    fact["gross_margin_pct"] = (fact["gross_profit_usd"] / fact["revenue_usd"] * 100).where(
        fact["revenue_usd"] > 0, 0.0
    )
    return fact
