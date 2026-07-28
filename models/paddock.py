"""Domain objects for paddocks and management interventions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class PaddockConfig:
    """Physical identity and starting condition of one paddock."""
    name: str = "North Paddock"
    area_ha: float = 12.0
    soil_type: Literal["Sandy", "Loam", "Clay"] = "Loam"
    initial_biomass: float = 1800.0
    initial_soil_water: float = 90.0

@dataclass(frozen=True)
class ManagementEvent:
    """A dated intervention applied during simulation."""
    day: int
    kind: Literal["Irrigation", "Grazing", "Fertiliser"]
    amount: float

SOIL_PRESETS = {
    "Sandy": {"field_capacity": 85.0, "wilting_point": 14.0, "drainage_factor": 0.22},
    "Loam": {"field_capacity": 110.0, "wilting_point": 20.0, "drainage_factor": 0.12},
    "Clay": {"field_capacity": 145.0, "wilting_point": 32.0, "drainage_factor": 0.06},
}
