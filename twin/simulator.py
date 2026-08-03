"""Numerical orchestration for the coupled paddock digital twin."""
from __future__ import annotations

from dataclasses import replace
from typing import Literal

import pandas as pd

from data.generator import generate_environment_data
from models.paddock import ManagementEvent, PaddockConfig, SOIL_PRESETS
from models.pasture_model import (
    ModelParameters,
    potential_growth,
    step_biomass,
    step_soil_water,
    water_stress,
)

Scenario = Literal["Normal", "Drought"]


def parameters_for_paddock(
    paddock: PaddockConfig, base: ModelParameters | None = None
) -> ModelParameters:
    """Apply a paddock's soil preset and starting state to model parameters."""
    params = base or ModelParameters()
    soil = SOIL_PRESETS[paddock.soil_type]
    return replace(
        params,
        field_capacity=soil["field_capacity"],
        wilting_point=soil["wilting_point"],
        drainage_factor=soil["drainage_factor"],
        initial_biomass=paddock.initial_biomass,
        initial_soil_water=min(paddock.initial_soil_water, soil["field_capacity"]),
    )


def run_simulation(
    scenario: Scenario = "Normal",
    days: int = 30,
    seed: int = 42,
    start_date: str | pd.Timestamp | None = None,
    parameters: ModelParameters | None = None,
    events: list[ManagementEvent] | None = None,
) -> pd.DataFrame:
    """Integrate coupled soil-water and biomass states, applying dated events."""
    if scenario not in ("Normal", "Drought"):
        raise ValueError("scenario must be 'Normal' or 'Drought'")

    params = parameters or ModelParameters()
    event_by_day = {event.day: event for event in (events or [])}

    environment = generate_environment_data(days, seed, start_date).copy()
    if scenario == "Drought":
        environment["rainfall_mm"] *= 0.5

    soil_water = params.initial_soil_water
    biomass = params.initial_biomass
    records = []

    for index, row in enumerate(environment.itertuples(index=False), start=1):
        event = event_by_day.get(index)
        irrigation = 0.0
        grazed = 0.0
        fertiliser_factor = 1.0

        if event and event.kind == "Irrigation":
            irrigation = max(0.0, event.amount)
        if event and event.kind == "Grazing":
            residual = max(0.0, event.amount)
            grazed = max(0.0, biomass - residual)
            biomass = min(biomass, residual)
        if event and event.kind == "Fertiliser":
            fertiliser_factor = 1.0 + min(max(event.amount, 0.0), 100.0) / 500.0

        effective_rainfall = row.rainfall_mm + irrigation
        soil_water, evapotranspiration, drainage = step_soil_water(
            soil_water, effective_rainfall, row.temperature_c, params
        )
        moisture_factor = water_stress(soil_water, params)
        potential = (
            potential_growth(row.rainfall_mm, row.temperature_c, params)
            * fertiliser_factor
        )
        biomass, realised_growth, senescence = step_biomass(
            biomass, potential, moisture_factor, params
        )

        records.append(
            {
                "date": row.date,
                "day": index,
                "rainfall_mm": row.rainfall_mm,
                "irrigation_mm": irrigation,
                "temperature_c": row.temperature_c,
                "soil_water_mm": soil_water,
                "soil_moisture_pct": soil_water / params.field_capacity * 100,
                "water_stress_factor": moisture_factor,
                "potential_growth_kg_dm_ha_day": potential,
                "pasture_growth_kg_dm_ha_day": realised_growth,
                "pasture_biomass_kg_dm_ha": biomass,
                "evapotranspiration_mm": evapotranspiration,
                "drainage_mm": drainage,
                "senescence_kg_dm_ha_day": senescence,
                "grazing_removed_kg_dm_ha": grazed,
                "management_event": event.kind if event else "None",
                "scenario": scenario,
            }
        )

    result = pd.DataFrame(records)
    numeric_cols = result.select_dtypes("number").columns
    result[numeric_cols] = result[numeric_cols].round(3)
    return result


def compare_scenarios(
    days: int = 30,
    seed: int = 42,
    parameters: ModelParameters | None = None,
    events: list[ManagementEvent] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run Normal and Drought scenarios against identical forcing and management."""
    normal = run_simulation("Normal", days, seed, parameters=parameters, events=events)
    drought = run_simulation(
        "Drought", days, seed, parameters=parameters, events=events
    )
    return normal, drought


def run_farm(
    paddocks: list[PaddockConfig],
    scenario: Scenario = "Normal",
    days: int = 30,
    seed: int = 42,
    events_by_paddock: dict[str, list[ManagementEvent]] | None = None,
) -> pd.DataFrame:
    """Simulate multiple paddocks and combine their results into one frame."""
    events_by_paddock = events_by_paddock or {}
    frames = []
    for offset, paddock in enumerate(paddocks):
        frame = run_simulation(
            scenario,
            days,
            seed + offset,
            parameters=parameters_for_paddock(paddock),
            events=events_by_paddock.get(paddock.name, []),
        )
        frame["paddock"] = paddock.name
        frame["area_ha"] = paddock.area_ha
        frame["total_biomass_kg_dm"] = frame.pasture_biomass_kg_dm_ha * paddock.area_ha
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def drought_growth_drop_percent(
    days: int = 30,
    seed: int = 42,
    parameters: ModelParameters | None = None,
    events: list[ManagementEvent] | None = None,
) -> float:
    """Return the percentage drop in cumulative realised growth under drought."""
    normal, drought = compare_scenarios(days, seed, parameters, events)
    normal_total = normal.pasture_growth_kg_dm_ha_day.sum()
    if not normal_total:
        return 0.0
    drought_total = drought.pasture_growth_kg_dm_ha_day.sum()
    return max(0.0, (normal_total - drought_total) / normal_total * 100.0)
