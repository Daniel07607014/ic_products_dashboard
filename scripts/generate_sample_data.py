"""Generate synthetic IC-product data for local development.

Writes five CSVs into ``data/raw/`` matching the schema in
:mod:`src.data.schema`. The numbers are designed to LOOK realistic so
charts have interesting shapes to render: seasonality in Q4, learning
curves on new products, an 80/20 customer concentration, and a handful
of loss-leader / super-margin outliers.

Usage:
    python scripts/generate_sample_data.py --seed 42
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (  # noqa: E402
    CUSTOMER_TIERS,
    INDUSTRIES,
    PACKAGE_TYPES,
    PROCESS_NODES_NM,
    PRODUCT_FAMILIES,
    RAW_DATA_DIR,
    REGIONS,
    SUPPORTED_CURRENCIES,
)

FAMILY_TARGET_MARGIN = {
    "MCU": 0.30,
    "PMIC": 0.40,
    "DriverIC": 0.25,
    "RF": 0.50,
    "Sensor": 0.45,
}

# Smaller process node = pricier per-die wafer cost (advanced-node capacity is expensive).
NODE_WAFER_COST_PER_DIE = {130: 0.30, 90: 0.55, 55: 0.90, 40: 1.30, 28: 1.90}
# Packaging complexity by type (BGA costs more than a simple leadframe DFN/SOP).
PACKAGE_BASE_COST_USD = {"DFN": 0.04, "SOP": 0.06, "QFN": 0.10, "BGA": 0.22}

TIER_WEIGHTS = {"A": 0.50, "B": 0.35, "C": 0.15}
TIER_SIZE = {"A": 5, "B": 15, "C": 20}
# Strategic (A) accounts carry the best margin, C the worst — so the
# tier-performance coloring on the Customer page ranks A > B > C.
TIER_MARGIN_ADJ = {"A": 0.05, "B": 0.0, "C": -0.05}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    p.add_argument("--months", type=int, default=24)
    p.add_argument("--products", type=int, default=80)
    p.add_argument("--customers", type=int, default=40)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def generate_products(n: int, rng: np.random.Generator, faker: Faker) -> pd.DataFrame:
    rows = []
    for i in range(n):
        family = rng.choice(PRODUCT_FAMILIES)
        node = int(rng.choice(PROCESS_NODES_NM))
        package = rng.choice(PACKAGE_TYPES)
        launch_offset_days = int(rng.integers(30, 1500))
        launch = pd.Timestamp("2026-06-30") - pd.Timedelta(days=launch_offset_days)
        status = rng.choice(["Active", "Active", "Active", "NPI", "EOL"])
        rows.append({
            "product_id": f"IC{i + 1001:04d}",
            "product_name": f"{family}-{node}nm-{package}-{i + 1:03d}",
            "product_family": family,
            "process_node": node,
            "package_type": package,
            "pin_count": int(rng.choice([16, 20, 24, 32, 48, 64, 100, 144])),
            "launch_date": launch.date().isoformat(),
            "product_status": status,
        })
    return pd.DataFrame(rows)


def generate_customers(n: int, rng: np.random.Generator, faker: Faker) -> pd.DataFrame:
    tier_slots = ["A"] * TIER_SIZE["A"] + ["B"] * TIER_SIZE["B"] + ["C"] * TIER_SIZE["C"]
    tiers = (tier_slots * ((n // len(tier_slots)) + 1))[:n]
    rng.shuffle(tiers)

    rows = []
    for i, tier in enumerate(tiers):
        rows.append({
            "customer_id": f"CUS{i + 100:03d}",
            "customer_name": faker.company(),
            "customer_tier": tier,
            "industry": rng.choice(INDUSTRIES),
            "country": rng.choice(REGIONS),
        })
    return pd.DataFrame(rows)


def _month_range(months: int) -> list[str]:
    end = date(2026, 6, 1)
    return [
        (pd.Timestamp(end) - pd.DateOffset(months=months - 1 - i)).strftime("%Y-%m")
        for i in range(months)
    ]


def generate_costs(products: pd.DataFrame, periods: list[str], rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for _, prod in products.iterrows():
        launch_date = pd.Timestamp(prod["launch_date"])
        pin_count = int(prod["pin_count"])

        # Different node/package/pin-count specs carry genuinely different BOM
        # cost, not just noise — mirrors how different "models" price out in
        # real IC cost sheets.
        die_variance = float(rng.uniform(0.85, 1.15))
        base_wafer = NODE_WAFER_COST_PER_DIE[int(prod["process_node"])] * die_variance
        base_packaging = (
            PACKAGE_BASE_COST_USD[prod["package_type"]] * (1 + pin_count / 200) * float(rng.uniform(0.9, 1.1))
        )
        base_testing = (0.02 + pin_count * 0.0015) * float(rng.uniform(0.9, 1.1))
        base_overhead = float(rng.uniform(0.05, 0.40))
        royalty = float(rng.choice([0.0, 0.0, 0.0, rng.uniform(0.01, 0.15)]))

        for period in periods:
            period_ts = pd.Timestamp(period + "-01")
            months_since_launch = max(0, (period_ts.year - launch_date.year) * 12 + (period_ts.month - launch_date.month))

            learning = 0.99 ** (months_since_launch // 3)
            wafer = base_wafer * learning * float(rng.uniform(0.97, 1.03))
            packaging = base_packaging * float(rng.uniform(0.97, 1.03))
            testing = base_testing * float(rng.uniform(0.95, 1.05))
            overhead = base_overhead * float(rng.uniform(0.98, 1.02))

            if months_since_launch < 3:
                yield_rate = float(rng.uniform(0.75, 0.85))
            elif months_since_launch < 12:
                yield_rate = float(rng.uniform(0.85, 0.93))
            else:
                yield_rate = float(rng.uniform(0.93, 0.98))

            raw_unit_cost = wafer + packaging + testing + overhead + royalty
            unit_cost = raw_unit_cost / yield_rate

            rows.append({
                "product_id": prod["product_id"],
                "period": period,
                "wafer_cost_usd": round(wafer, 4),
                "packaging_cost_usd": round(packaging, 4),
                "testing_cost_usd": round(testing, 4),
                "yield_rate": round(yield_rate, 4),
                "overhead_cost_usd": round(overhead, 4),
                "royalty_cost_usd": round(royalty, 4),
                "unit_cost_usd": round(unit_cost, 4),
            })
    return pd.DataFrame(rows)


def generate_fx(periods: list[str]) -> pd.DataFrame:
    rates = {"USD": 1.0, "TWD": 32.0, "JPY": 150.0, "EUR": 0.92, "CNY": 7.20}
    rows = []
    for period in periods:
        for cur, base in rates.items():
            noise = np.random.default_rng(hash((period, cur)) & 0xFFFFFFFF).uniform(0.97, 1.03)
            rows.append({"period": period, "currency": cur, "rate_to_usd": round(base * noise, 4)})
    return pd.DataFrame(rows)


def generate_sales(
    products: pd.DataFrame,
    customers: pd.DataFrame,
    costs: pd.DataFrame,
    periods: list[str],
    rng: np.random.Generator,
) -> pd.DataFrame:
    cost_lookup = costs.set_index(["product_id", "period"])["unit_cost_usd"].to_dict()

    tier_customers = {
        tier: customers[customers["customer_tier"] == tier]["customer_id"].tolist()
        for tier in CUSTOMER_TIERS
    }

    outlier_ids = rng.choice(products["product_id"].to_numpy(), size=8, replace=False)
    loss_leaders = set(outlier_ids[:4].tolist())
    super_margin = set(outlier_ids[4:].tolist())

    rows: list[dict] = []
    order_seq = 1

    for period in periods:
        period_ts = pd.Timestamp(period + "-01")
        seasonality = 1.25 if period_ts.month in (10, 11, 12) else 1.0

        for _, prod in products.iterrows():
            if prod["product_status"] == "EOL" and rng.random() < 0.5:
                continue
            if prod["product_status"] == "NPI" and rng.random() < 0.3:
                continue

            n_orders = int(rng.integers(1, 10))
            unit_cost = cost_lookup.get((prod["product_id"], period))
            if unit_cost is None:
                continue

            base_margin = FAMILY_TARGET_MARGIN[prod["product_family"]]
            if prod["product_id"] in loss_leaders:
                base_margin = float(rng.uniform(-0.15, 0.05))
            elif prod["product_id"] in super_margin:
                base_margin = float(rng.uniform(0.60, 0.80))

            for _ in range(n_orders):
                tier = rng.choice(CUSTOMER_TIERS, p=[TIER_WEIGHTS[t] for t in CUSTOMER_TIERS])
                customer_id = rng.choice(tier_customers[tier])

                qty_scale = {"A": 5000, "B": 1500, "C": 400}[tier]
                quantity = int(max(10, rng.normal(qty_scale, qty_scale * 0.4) * seasonality))

                margin_noise = float(rng.normal(0, 0.05))
                unit_price = round(unit_cost * (1 + base_margin + TIER_MARGIN_ADJ[tier] + margin_noise), 4)
                unit_price = max(unit_price, 0.01)
                revenue = round(unit_price * quantity, 2)

                day = int(rng.integers(1, 28))
                order_date = f"{period}-{day:02d}"

                rows.append({
                    "order_id": f"ORD{order_seq:07d}",
                    "order_date": order_date,
                    "product_id": prod["product_id"],
                    "customer_id": customer_id,
                    "region": rng.choice(REGIONS),
                    "quantity": quantity,
                    "unit_price_usd": unit_price,
                    "revenue_usd": revenue,
                    "currency": rng.choice(SUPPORTED_CURRENCIES, p=[0.55, 0.20, 0.10, 0.10, 0.05]),
                })
                order_seq += 1

    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    faker = Faker()
    Faker.seed(args.seed)

    periods = _month_range(args.months)

    print(f"[1/5] Products     ({args.products}) ...")
    products = generate_products(args.products, rng, faker)
    products.to_csv(args.output_dir / "product_master.csv", index=False)

    print(f"[2/5] Customers    ({args.customers}) ...")
    customers = generate_customers(args.customers, rng, faker)
    customers.to_csv(args.output_dir / "customer_master.csv", index=False)

    print(f"[3/5] Cost data    ({args.products} × {args.months}) ...")
    costs = generate_costs(products, periods, rng)
    costs.to_csv(args.output_dir / "cost_data.csv", index=False)

    print(f"[4/5] FX rates     (5 × {args.months}) ...")
    fx = generate_fx(periods)
    fx.to_csv(args.output_dir / "fx_rates.csv", index=False)

    print(f"[5/5] Sales        (~{args.products * args.months * 5:,} rows expected) ...")
    sales = generate_sales(products, customers, costs, periods, rng)
    sales.to_csv(args.output_dir / "sales_transactions.csv", index=False)

    print()
    print(f"Wrote {len(products):>6,} products    → {args.output_dir / 'product_master.csv'}")
    print(f"Wrote {len(customers):>6,} customers   → {args.output_dir / 'customer_master.csv'}")
    print(f"Wrote {len(costs):>6,} cost rows   → {args.output_dir / 'cost_data.csv'}")
    print(f"Wrote {len(fx):>6,} fx rows     → {args.output_dir / 'fx_rates.csv'}")
    print(f"Wrote {len(sales):>6,} sales rows  → {args.output_dir / 'sales_transactions.csv'}")


if __name__ == "__main__":
    main()
