"""Domain objects for paddocks and management interventions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

SOIL_PRESETS = {
    "Sandy": {"field_capacity": 85.0, "wilting_point": 14.0, "drainage_factor": 0.22},
    "Loam": {"field_capacity": 110.0, "wilting_point": 20.0, "drainage_factor": 0.12},
    "Clay": {"field_capacity": 145.0, "wilting_point": 32.0, "drainage_factor": 0.06},
}

EVENT_KINDS = ("Irrigation", "Grazing", "Fertiliser")


@dataclass(frozen=True)
class PaddockConfig:
    """Physical identity and starting condition of one paddock."""
    name: str = "North Paddock"
    area_ha: float = 12.0
    soil_type: Literal["Sandy", "Loam", "Clay"] = "Loam"
    initial_biomass: float = 1800.0
    initial_soil_water: float = 90.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("paddock name is required")
        if self.area_ha <= 0:
            raise ValueError("area_ha must be greater than zero")
        if self.soil_type not in SOIL_PRESETS:
            raise ValueError(f"soil_type must be one of {tuple(SOIL_PRESETS)}")
        if self.initial_biomass < 0:
            raise ValueError("initial_biomass cannot be negative")
        if self.initial_soil_water < 0:
            raise ValueError("initial_soil_water cannot be negative")


@dataclass(frozen=True)
class ManagementEvent:
    """A dated intervention applied during simulation."""
    day: int
    kind: Literal["Irrigation", "Grazing", "Fertiliser"]
    amount: float

    def __post_init__(self) -> None:
        if self.day < 1:
            raise ValueError("day must be 1 or greater")
        if self.kind not in EVENT_KINDS:
            raise ValueError(f"kind must be one of {EVENT_KINDS}")
