"""Central project configuration.

All paths and defaults live here so the rest of the code can just do
``from config.settings import RAW_DATA_DIR`` without hard-coding paths.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"

CONFIG_DIR: Path = PROJECT_ROOT / "config"
AUTH_CONFIG_PATH: Path = CONFIG_DIR / "auth_config.yaml"

RAW_FILES: dict[str, Path] = {
    "products": RAW_DATA_DIR / "product_master.csv",
    "customers": RAW_DATA_DIR / "customer_master.csv",
    "sales": RAW_DATA_DIR / "sales_transactions.csv",
    "costs": RAW_DATA_DIR / "cost_data.csv",
    "fx": RAW_DATA_DIR / "fx_rates.csv",
}

BASE_CURRENCY: str = "USD"
SUPPORTED_CURRENCIES: tuple[str, ...] = ("USD", "TWD", "JPY", "EUR", "CNY")

PRODUCT_FAMILIES: tuple[str, ...] = ("MCU", "PMIC", "DriverIC", "RF", "Sensor")
PROCESS_NODES_NM: tuple[int, ...] = (28, 40, 55, 90, 130)
PACKAGE_TYPES: tuple[str, ...] = ("QFN", "BGA", "SOP", "DFN")
CUSTOMER_TIERS: tuple[str, ...] = ("A", "B", "C")
INDUSTRIES: tuple[str, ...] = ("Consumer", "Industrial", "Automotive", "Communication")
REGIONS: tuple[str, ...] = ("Taiwan", "China", "Japan", "Korea", "US", "Europe")

COOKIE_KEY: str = os.getenv("COOKIE_KEY", "dev-only-change-me-in-production")
COOKIE_NAME: str = os.getenv("COOKIE_NAME", "ic_dashboard_auth")
COOKIE_EXPIRY_DAYS: int = int(os.getenv("COOKIE_EXPIRY_DAYS", "7"))
