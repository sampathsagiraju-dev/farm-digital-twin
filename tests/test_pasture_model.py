"""Tests for models/pasture_model.py."""
from __future__ import annotations

import pytest

from models.pasture_model import (
    ModelParameters,
    calculate_growth,
    potential_growth,
    step_biomass,
    step_soil_water,
    temperature_stress,
    water_stress,
)


def test_temperature_stress_is_zero_below_threshold():
    assert temperature_stress(20.0) == 0.0
    assert temperature_stress(25.0) == 0.0


def test_temperature_stress_scales_above_threshold():
    assert temperature_stress(30.0) == pytest.approx(5.0)


def test_potential_growth_increases_with_rainfall():
    params = ModelParameters()
    dry = potential_growth(0.0, 20.0, params)
    wet = potential_growth(20.0, 20.0, params)
    assert wet > dry


def test_potential_growth_reduced_by_heat_stress():
    params = ModelParameters()
    cool = potential_growth(10.0, 20.0, params)
    hot = potential_growth(10.0, 35.0, params)
    assert hot < cool


def test_potential_growth_never_negative():
    params = ModelParameters(base_growth=1.0, heat_stress_coefficient=10.0)
    assert potential_growth(0.0, 60.0, params) == 0.0


def test_water_stress_bounds():
    params = ModelParameters(field_capacity=110.0, wilting_point=20.0)
    assert water_stress(0.0, params) == 0.0
    assert water_stress(20.0, params) == 0.0
    assert water_stress(110.0, params) == 1.0
    assert water_stress(200.0, params) == 1.0


def test_water_stress_linear_between_bounds():
    params = ModelParameters(field_capacity=120.0, wilting_point=20.0)
    assert water_stress(70.0, params) == pytest.approx(0.5)


def test_step_soil_water_clips_to_field_capacity():
    params = ModelParameters(field_capacity=100.0)
    water, et, drainage = step_soil_water(90.0, 200.0, 15.0, params)
    assert water <= params.field_capacity
    assert drainage >= 0.0
    assert et >= 0.0


def test_step_soil_water_never_negative():
    params = ModelParameters()
    water, _, _ = step_soil_water(0.0, 0.0, 40.0, params)
    assert water >= 0.0


def test_step_biomass_applies_growth_and_senescence():
    params = ModelParameters(senescence_rate=0.01)
    biomass, realised, senescence = step_biomass(1000.0, 40.0, 1.0, params)
    assert realised == pytest.approx(40.0)
    assert senescence == pytest.approx(10.0)
    assert biomass == pytest.approx(1000.0 + 40.0 - 10.0)


def test_step_biomass_never_negative():
    params = ModelParameters(senescence_rate=0.5)
    biomass, _, _ = step_biomass(1.0, 0.0, 0.0, params)
    assert biomass >= 0.0


def test_calculate_growth_matches_potential_growth():
    params = ModelParameters(base_growth=40.0, rainfall_response=0.05, heat_stress_coefficient=0.03)
    assert calculate_growth(10.0, 30.0) == pytest.approx(
        potential_growth(10.0, 30.0, params)
    )


def test_model_parameters_rejects_invalid_soil_bounds():
    with pytest.raises(ValueError):
        ModelParameters(field_capacity=10.0, wilting_point=20.0)


def test_model_parameters_rejects_negative_base_growth():
    with pytest.raises(ValueError):
        ModelParameters(base_growth=-1.0)
