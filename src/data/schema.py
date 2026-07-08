"""Column definitions and dtype maps for the five input CSVs.

Anything that needs to know the shape of the raw data should import from here,
so a column rename or type change happens in exactly one place.
"""
from __future__ import annotations

PRODUCT_COLUMNS: dict[str, str] = {
    "product_id": "string",
    "product_name": "string",
    "product_family": "string",
    "process_node": "Int16",
    "package_type": "string",
    "pin_count": "Int16",
    "launch_date": "datetime64[ns]",
    "product_status": "string",
}

CUSTOMER_COLUMNS: dict[str, str] = {
    "customer_id": "string",
    "customer_name": "string",
    "customer_tier": "string",
    "industry": "string",
    "country": "string",
}

SALES_COLUMNS: dict[str, str] = {
    "order_id": "string",
    "order_date": "datetime64[ns]",
    "product_id": "string",
    "customer_id": "string",
    "region": "string",
    "quantity": "Int64",
    "unit_price_usd": "float64",
    "revenue_usd": "float64",
    "currency": "string",
}

COST_COLUMNS: dict[str, str] = {
    "product_id": "string",
    "period": "string",  # YYYY-MM
    "wafer_cost_usd": "float64",
    "packaging_cost_usd": "float64",
    "testing_cost_usd": "float64",
    "yield_rate": "float64",
    "overhead_cost_usd": "float64",
    "royalty_cost_usd": "float64",
    "unit_cost_usd": "float64",
}

FX_COLUMNS: dict[str, str] = {
    "period": "string",
    "currency": "string",
    "rate_to_usd": "float64",
}

DATE_COLUMNS: dict[str, list[str]] = {
    "products": ["launch_date"],
    "sales": ["order_date"],
}
