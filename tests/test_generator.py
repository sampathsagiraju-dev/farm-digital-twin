"""Tests for data/generator.py."""
from __future__ import annotations

import pandas as pd
import pytest

from data.generator import generate_environment_data


def test_returns_requested_number_of_days():
    df = generate_environment_data(days=10)
    assert len(df) == 10


def test_same_seed_is_reproducible():
    a = generate_environment_data(days=14, seed=7)
    b = generate_environment_data(days=14, seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_different_seeds_diverge():
    a = generate_environment_data(days=14, seed=1)
    b = generate_environment_data(days=14, seed=2)
    assert not a["rainfall_mm"].equals(b["rainfall_mm"])


def test_soil_moisture_stays_within_bounds():
    df = generate_environment_data(days=60, seed=3)
    assert (df["soil_moisture_pct"] >= 10.0).all()
    assert (df["soil_moisture_pct"] <= 100.0).all()


def test_rainfall_is_never_negative():
    df = generate_environment_data(days=60, seed=3)
    assert (df["rainfall_mm"] >= 0.0).all()


def test_rejects_non_positive_days():
    with pytest.raises(ValueError):
        generate_environment_data(days=0)
    with pytest.raises(ValueError):
        generate_environment_data(days=-5)


def test_honours_start_date():
    df = generate_environment_data(days=5, start_date="2026-01-01")
    assert df["date"].iloc[0] == pd.Timestamp("2026-01-01")
    assert df["date"].iloc[-1] == pd.Timestamp("2026-01-05")


def test_columns_present():
    df = generate_environment_data(days=3)
    assert list(df.columns) == [
        "date",
        "rainfall_mm",
        "temperature_c",
        "soil_moisture_pct",
    ]
