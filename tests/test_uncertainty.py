"""Tests for twin/uncertainty.py."""
from __future__ import annotations

import pytest

from models.pasture_model import ModelParameters
from twin.uncertainty import run_ensemble


def test_run_ensemble_returns_one_row_per_day():
    result = run_ensemble("Normal", days=15, seed=1, parameters=ModelParameters(), members=15)
    assert len(result) == 15
    assert result["day"].tolist() == list(range(1, 16))


def test_run_ensemble_rejects_too_few_members():
    with pytest.raises(ValueError):
        run_ensemble("Normal", days=10, seed=1, parameters=ModelParameters(), members=5)


def test_ensemble_quantiles_are_ordered():
    result = run_ensemble("Normal", days=20, seed=1, parameters=ModelParameters(), members=20)
    assert (result["biomass_p10"] <= result["biomass_p50"]).all()
    assert (result["biomass_p50"] <= result["biomass_p90"]).all()
    assert (result["soil_water_p10"] <= result["soil_water_p50"]).all()
    assert (result["soil_water_p50"] <= result["soil_water_p90"]).all()


def test_drought_ensemble_has_lower_median_biomass_than_normal():
    normal = run_ensemble("Normal", days=30, seed=1, parameters=ModelParameters(), members=15)
    drought = run_ensemble("Drought", days=30, seed=1, parameters=ModelParameters(), members=15)
    assert drought["biomass_p50"].iloc[-1] <= normal["biomass_p50"].iloc[-1]
