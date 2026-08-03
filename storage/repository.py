"""SQLite persistence for reusable twin scenarios."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from pathlib import Path

from models.paddock import ManagementEvent, PaddockConfig
from models.pasture_model import ModelParameters

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "twin_scenarios.db"


def initialise_database(path: Path = DB_PATH) -> None:
    """Create the scenario table if required."""
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scenarios (
                name TEXT PRIMARY KEY,
                paddock_json TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                events_json TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def save_scenario(
    name: str,
    paddock: PaddockConfig,
    parameters: ModelParameters,
    events: list[ManagementEvent],
    path: Path = DB_PATH,
) -> None:
    """Insert or replace a named scenario."""
    if not name.strip():
        raise ValueError("scenario name is required")

    initialise_database(path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO scenarios
                (name, paddock_json, parameters_json, events_json, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                name.strip(),
                json.dumps(asdict(paddock)),
                json.dumps(asdict(parameters)),
                json.dumps([asdict(event) for event in events]),
            ),
        )
        connection.commit()


def list_scenarios(path: Path = DB_PATH) -> list[str]:
    """Return stored scenario names, alphabetically."""
    initialise_database(path)
    with closing(sqlite3.connect(path)) as connection:
        rows = connection.execute(
            "SELECT name FROM scenarios ORDER BY name"
        ).fetchall()
    return [row[0] for row in rows]


def load_scenario(
    name: str, path: Path = DB_PATH
) -> tuple[PaddockConfig, ModelParameters, list[ManagementEvent]]:
    """Load a stored scenario by name."""
    initialise_database(path)
    with closing(sqlite3.connect(path)) as connection:
        row = connection.execute(
            "SELECT paddock_json, parameters_json, events_json "
            "FROM scenarios WHERE name = ?",
            (name,),
        ).fetchone()

    if row is None:
        raise KeyError(name)

    paddock_json, parameters_json, events_json = row
    return (
        PaddockConfig(**json.loads(paddock_json)),
        ModelParameters(**json.loads(parameters_json)),
        [ManagementEvent(**item) for item in json.loads(events_json)],
    )


def delete_scenario(name: str, path: Path = DB_PATH) -> None:
    """Delete a stored scenario by name; no-op if it does not exist."""
    initialise_database(path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("DELETE FROM scenarios WHERE name = ?", (name,))
        connection.commit()
