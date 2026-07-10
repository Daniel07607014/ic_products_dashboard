"""Create MySQL tables and load ``data/raw/*.csv`` into them.

Non-interactive by design (interactive prompts hang in this environment).

Usage:
    python scripts/init_db.py                  # load the five data tables
    python scripts/init_db.py --migrate-users  # also copy users from auth_config.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml
from sqlalchemy import DateTime, Float, Integer, SmallInteger, String, text
from sqlalchemy.types import TypeEngine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import AUTH_CONFIG_PATH  # noqa: E402
from src.data.db import get_engine  # noqa: E402
from src.data.loader import load_all  # noqa: E402
from src.data.users import ensure_users_table, upsert_user_with_hash  # noqa: E402

TABLE_NAMES = {
    "products": "product_master",
    "customers": "customer_master",
    "sales": "sales_transactions",
    "costs": "cost_data",
    "fx": "fx_rates",
}

_PANDAS_TO_SQL: dict[str, TypeEngine] = {
    "string": String(255),
    "Int16": SmallInteger(),
    "Int64": Integer(),
    "float64": Float(),
    "datetime64[ns]": DateTime(),
}


def _sql_dtypes(columns: dict[str, str]) -> dict[str, TypeEngine]:
    return {col: _PANDAS_TO_SQL[dtype] for col, dtype in columns.items()}


def load_data_tables() -> None:
    from src.data import schema

    schema_by_key = {
        "products": schema.PRODUCT_COLUMNS,
        "customers": schema.CUSTOMER_COLUMNS,
        "sales": schema.SALES_COLUMNS,
        "costs": schema.COST_COLUMNS,
        "fx": schema.FX_COLUMNS,
    }

    # Read via the CSV loader so dtype coercion stays in one place;
    # force the csv path regardless of .env since we're seeding the DB.
    tables = load_all(backend="csv")

    engine = get_engine()
    for key, df in tables.items():
        table = TABLE_NAMES[key]
        df.to_sql(
            table,
            engine,
            if_exists="replace",
            index=False,
            dtype=_sql_dtypes(schema_by_key[key]),
            chunksize=1000,
        )
        print(f"loaded {len(df):>6,} rows -> {table}")


def migrate_users() -> None:
    ensure_users_table()
    if not AUTH_CONFIG_PATH.exists():
        print(f"skip user migration: {AUTH_CONFIG_PATH} not found")
        return
    with AUTH_CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    usernames = (config or {}).get("credentials", {}).get("usernames", {})
    for username, info in usernames.items():
        roles = info.get("roles", ["viewer"])
        inserted = upsert_user_with_hash(
            username=username,
            name=info.get("name", username),
            email=info.get("email", ""),
            password_hash=info["password"],
            role=roles[0] if roles else "viewer",
        )
        print(f"user {username}: {'migrated' if inserted else 'already exists, skipped'}")


def verify() -> None:
    engine = get_engine()
    with engine.connect() as conn:
        for table in [*TABLE_NAMES.values(), "users"]:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"verify: {table} = {n:,} rows")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--migrate-users", action="store_true", help="copy users from auth_config.yaml")
    args = ap.parse_args()

    ensure_users_table()
    load_data_tables()
    if args.migrate_users:
        migrate_users()
    verify()


if __name__ == "__main__":
    main()
