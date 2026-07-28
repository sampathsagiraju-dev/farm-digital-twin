"""Coupled pasture/soil-water equations for the paddock digital twin."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelParameters:
    """Tunable physical and biological parameters."""
    base_growth: float = 40.0
    rainfall_response: float = 0.05
    heat_stress_coefficient: float = 0.03
    field_capacity: float = 110.0
    wilting_point: float = 20.0
    initial_soil_water: float = 90.0
    initial_biomass: float = 1800.0
    evapotranspiration_factor: float = 0.18
    drainage_factor: float = 0.12
    senescence_rate: float = 0.008

def temperature_stress(temperature: float) -> float:
    """Return heat stress above 25 C."""
    return max(0.0, float(temperature) - 25.0)

def potential_growth(rainfall: float, temperature: float, p: ModelParameters) -> float:
    """Calculate the required biological-inspired potential growth."""
    value = p.base_growth * (1.0 + p.rainfall_response * float(rainfall))
    return max(0.0, value - p.heat_stress_coefficient * temperature_stress(temperature))

def water_stress(soil_water: float, p: ModelParameters) -> float:
    """Return a 0-1 growth multiplier from available soil water."""
    return min(1.0, max(0.0, (soil_water - p.wilting_point) / (p.field_capacity - p.wilting_point)))

def step_soil_water(soil_water: float, rainfall: float, temperature: float, p: ModelParameters) -> tuple[float, float, float]:
    """Advance soil water one day; return water, ET and drainage."""
    et = max(0.0, temperature - 5.0) * p.evapotranspiration_factor
    drainage = max(0.0, soil_water + rainfall - p.field_capacity) * p.drainage_factor
    return min(p.field_capacity, max(0.0, soil_water + rainfall - et - drainage)), et, drainage

def step_biomass(biomass: float, potential: float, moisture_factor: float, p: ModelParameters) -> tuple[float, float, float]:
    """Advance biomass; return biomass, realised growth and senescence."""
    realised = potential * moisture_factor
    senescence = biomass * p.senescence_rate
    return max(0.0, biomass + realised - senescence), realised, senescence

def calculate_growth(rainfall: float, temperature: float, base_growth: float = 40.0, alpha: float = 0.05, beta: float = 0.03) -> float:
    """Backward-compatible original MVP equation."""
    return potential_growth(rainfall, temperature, ModelParameters(base_growth=base_growth, rainfall_response=alpha, heat_stress_coefficient=beta))

