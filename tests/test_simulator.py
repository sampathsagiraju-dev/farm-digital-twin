"""Tests for twin/simulator.py."""
from __future__ import annotations

import pytest

from models.paddock import ManagementEvent, PaddockConfig
from models.pasture_model import ModelParameters
from twin.simulator import (
    compare_scenarios,
    drought_growth_drop_percent,
    parameters_for_paddock,
    run_farm,
    run_simulation,
)


def test_run_simulation_returns_one_row_per_day():
    result = run_simulation("Normal", days=20)
    assert len(result) == 20
    assert result["day"].tolist() == list(range(1, 21))


def test_rejects_unknown_scenario():
    with pytest.raises(ValueError):
        run_simulation("Monsoon")  # type: ignore[arg-type]


def test_drought_receives_half_the_rainfall_of_normal():
    normal, drought = compare_scenarios(days=30, seed=1)
    assert drought["rainfall_mm"].sum() == pytest.approx(
        normal["rainfall_mm"].sum() * 0.5
    )


def test_drought_reduces_cumulative_growth():
    normal, drought = compare_scenarios(days=30, seed=1)
    assert drought["pasture_growth_kg_dm_ha_day"].sum() <= normal[
        "pasture_growth_kg_dm_ha_day"
    ].sum()


def test_drought_growth_drop_percent_is_non_negative():
    assert drought_growth_drop_percent(days=30, seed=1) >= 0.0


def test_irrigation_event_increases_effective_rainfall():
    events = [ManagementEvent(day=5, kind="Irrigation", amount=50.0)]
    with_irrigation = run_simulation("Drought", days=10, events=events)
    without_irrigation = run_simulation("Drought", days=10, events=[])
    day5_with = with_irrigation.loc[with_irrigation["day"] == 5].iloc[0]
    day5_without = without_irrigation.loc[without_irrigation["day"] == 5].iloc[0]
    assert day5_with["soil_water_mm"] >= day5_without["soil_water_mm"]


def test_grazing_event_removes_biomass_down_to_residual():
    residual = 1000.0
    events = [ManagementEvent(day=5, kind="Grazing", amount=residual)]
    result = run_simulation("Normal", days=10, events=events)
    day4 = result.loc[result["day"] == 4].iloc[0]
    day5 = result.loc[result["day"] == 5].iloc[0]
    assert day5["grazing_removed_kg_dm_ha"] > 0.0
    assert day5["pasture_biomass_kg_dm_ha"] < day4["pasture_biomass_kg_dm_ha"]
    assert day5["management_event"] == "Grazing"


def test_grazing_never_increases_biomass_when_below_residual():
    events = [ManagementEvent(day=1, kind="Grazing", amount=100_000.0)]
    result = run_simulation("Normal", days=3, events=events)
    day1 = result.loc[result["day"] == 1].iloc[0]
    assert day1["grazing_removed_kg_dm_ha"] == 0.0
    assert day1["pasture_biomass_kg_dm_ha"] < 100_000.0


def test_fertiliser_event_boosts_potential_growth():
    events = [ManagementEvent(day=5, kind="Fertiliser", amount=100.0)]
    fertilised = run_simulation("Normal", days=10, events=events)
    baseline = run_simulation("Normal", days=10, events=[])
    day5_fert = fertilised.loc[fertilised["day"] == 5].iloc[0]
    day5_base = baseline.loc[baseline["day"] == 5].iloc[0]
    assert day5_fert["potential_growth_kg_dm_ha_day"] >= day5_base[
        "potential_growth_kg_dm_ha_day"
    ]


def test_parameters_for_paddock_applies_soil_preset():
    paddock = PaddockConfig(soil_type="Sandy")
    params = parameters_for_paddock(paddock)
    assert params.field_capacity == pytest.approx(85.0)
    assert params.wilting_point == pytest.approx(14.0)


def test_parameters_for_paddock_clips_initial_soil_water_to_field_capacity():
    paddock = PaddockConfig(soil_type="Sandy", initial_soil_water=500.0)
    params = parameters_for_paddock(paddock)
    assert params.initial_soil_water == pytest.approx(85.0)


def test_run_farm_combines_multiple_paddocks():
    paddocks = [
        PaddockConfig(name="North", area_ha=10.0, soil_type="Loam"),
        PaddockConfig(name="South", area_ha=20.0, soil_type="Clay"),
    ]
    result = run_farm(paddocks, days=10)
    assert set(result["paddock"]) == {"North", "South"}
    assert len(result) == 20


def test_run_farm_computes_total_biomass_from_area():
    paddocks = [PaddockConfig(name="North", area_ha=10.0)]
    result = run_farm(paddocks, days=5)
    row = result.iloc[0]
    assert row["total_biomass_kg_dm"] == pytest.approx(
        row["pasture_biomass_kg_dm_ha"] * 10.0
    )


def test_run_simulation_reproducible_for_same_seed():
    a = run_simulation("Normal", days=15, seed=99)
    b = run_simulation("Normal", days=15, seed=99)
    assert a.equals(b)


def test_custom_parameters_override_defaults():
    custom = ModelParameters(base_growth=10.0)
    result = run_simulation("Normal", days=5, parameters=custom)
    default_result = run_simulation("Normal", days=5)
    assert result["potential_growth_kg_dm_ha_day"].sum() <= default_result[
        "potential_growth_kg_dm_ha_day"
    ].sum()
