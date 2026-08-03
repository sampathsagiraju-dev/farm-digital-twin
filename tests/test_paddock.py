"""Tests for models/paddock.py."""
from __future__ import annotations

import pytest

from models.paddock import SOIL_PRESETS, ManagementEvent, PaddockConfig


def test_default_paddock_is_valid():
    paddock = PaddockConfig()
    assert paddock.soil_type in SOIL_PRESETS


def test_rejects_blank_name():
    with pytest.raises(ValueError):
        PaddockConfig(name="  ")


def test_rejects_non_positive_area():
    with pytest.raises(ValueError):
        PaddockConfig(area_ha=0)


def test_rejects_unknown_soil_type():
    with pytest.raises(ValueError):
        PaddockConfig(soil_type="Peat")  # type: ignore[arg-type]


def test_rejects_negative_biomass():
    with pytest.raises(ValueError):
        PaddockConfig(initial_biomass=-1)


def test_management_event_rejects_day_before_one():
    with pytest.raises(ValueError):
        ManagementEvent(day=0, kind="Irrigation", amount=10.0)


def test_management_event_rejects_unknown_kind():
    with pytest.raises(ValueError):
        ManagementEvent(day=1, kind="Mowing", amount=10.0)  # type: ignore[arg-type]


def test_soil_presets_cover_all_paddock_soil_types():
    assert set(SOIL_PRESETS) == {"Sandy", "Loam", "Clay"}
    for preset in SOIL_PRESETS.values():
        assert preset["field_capacity"] > preset["wilting_point"]
