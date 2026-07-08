"""Sanity checks for concentration metrics (HHI, top-N share)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.analytics.ranking import concentration_index, top_n_share


def test_concentration_index_full_concentration_is_10000() -> None:
    fact = pd.DataFrame({"customer_id": ["C1", "C1"], "revenue_usd": [100.0, 200.0]})
    assert concentration_index(fact, dimension="customer_id") == pytest.approx(10000.0)


def test_concentration_index_even_split_across_four() -> None:
    fact = pd.DataFrame({
        "customer_id": ["C1", "C2", "C3", "C4"],
        "revenue_usd": [100.0, 100.0, 100.0, 100.0],
    })
    # 4 equal 25% shares: 4 * 25^2 = 2500
    assert concentration_index(fact, dimension="customer_id") == pytest.approx(2500.0)


def test_concentration_index_zero_total_returns_zero() -> None:
    fact = pd.DataFrame({"customer_id": ["C1"], "revenue_usd": [0.0]})
    assert concentration_index(fact, dimension="customer_id") == 0.0


def test_top_n_share_basic() -> None:
    fact = pd.DataFrame({
        "customer_id": ["C1", "C2", "C3"],
        "revenue_usd": [70.0, 20.0, 10.0],
    })
    assert top_n_share(fact, dimension="customer_id", n=1) == pytest.approx(70.0)
    assert top_n_share(fact, dimension="customer_id", n=2) == pytest.approx(90.0)


def test_top_n_share_zero_total_returns_zero() -> None:
    fact = pd.DataFrame({"customer_id": ["C1"], "revenue_usd": [0.0]})
    assert top_n_share(fact, dimension="customer_id", n=1) == 0.0
