"""Cached data access for Streamlit pages.

Wraps :mod:`src.data.loader` with ``@st.cache_data`` so re-runs of the
same page don't re-parse the CSVs.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data.loader import load_all
from src.etl.join import build_fact_table


@st.cache_data(ttl=600, show_spinner="讀取資料中 / Loading data...")
def get_raw_tables() -> dict[str, pd.DataFrame]:
    return load_all()


@st.cache_data(ttl=600, show_spinner="建構分析資料表 / Building fact table...")
def get_fact_table() -> pd.DataFrame:
    tables = get_raw_tables()
    return build_fact_table(
        products=tables["products"],
        customers=tables["customers"],
        sales=tables["sales"],
        costs=tables["costs"],
    )
