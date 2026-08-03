"""Tests for storage/repository.py."""
from __future__ import annotations

import pytest

from models.paddock import ManagementEvent, PaddockConfig
from models.pasture_model import ModelParameters
from storage import repository


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "twin_scenarios.db"


def test_save_and_load_round_trips_scenario(db_path):
    paddock = PaddockConfig(name="North", area_ha=10.0, soil_type="Sandy")
    parameters = ModelParameters(base_growth=35.0)
    events = [ManagementEvent(day=3, kind="Irrigation", amount=15.0)]

    repository.save_scenario("Test Scenario", paddock, parameters, events, path=db_path)
    loaded_paddock, loaded_parameters, loaded_events = repository.load_scenario(
        "Test Scenario", path=db_path
    )

    assert loaded_paddock == paddock
    assert loaded_parameters == parameters
    assert loaded_events == events


def test_load_unknown_scenario_raises_key_error(db_path):
    with pytest.raises(KeyError):
        repository.load_scenario("Nonexistent", path=db_path)


def test_save_rejects_blank_name(db_path):
    with pytest.raises(ValueError):
        repository.save_scenario(
            "  ", PaddockConfig(), ModelParameters(), [], path=db_path
        )


def test_list_scenarios_is_alphabetical(db_path):
    for name in ["Zebra", "Alpha", "Mango"]:
        repository.save_scenario(name, PaddockConfig(), ModelParameters(), [], path=db_path)
    assert repository.list_scenarios(path=db_path) == ["Alpha", "Mango", "Zebra"]


def test_save_scenario_overwrites_existing_name(db_path):
    repository.save_scenario(
        "Reused", PaddockConfig(area_ha=5.0), ModelParameters(), [], path=db_path
    )
    repository.save_scenario(
        "Reused", PaddockConfig(area_ha=99.0), ModelParameters(), [], path=db_path
    )
    paddock, _, _ = repository.load_scenario("Reused", path=db_path)
    assert paddock.area_ha == pytest.approx(99.0)
    assert repository.list_scenarios(path=db_path) == ["Reused"]


def test_delete_scenario_removes_it(db_path):
    repository.save_scenario(
        "Temp", PaddockConfig(), ModelParameters(), [], path=db_path
    )
    repository.delete_scenario("Temp", path=db_path)
    assert repository.list_scenarios(path=db_path) == []


def test_delete_unknown_scenario_is_a_no_op(db_path):
    repository.delete_scenario("Nonexistent", path=db_path)
