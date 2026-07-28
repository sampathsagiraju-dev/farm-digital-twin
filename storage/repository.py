"""SQLite persistence for reusable twin scenarios."""
from __future__ import annotations
import json,sqlite3
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from models.paddock import ManagementEvent,PaddockConfig
from models.pasture_model import ModelParameters
DB_PATH=Path(__file__).resolve().parents[1]/"data"/"twin_scenarios.db"

def initialise_database(path: Path=DB_PATH)->None:
    """Create the scenario table if required and close the file deterministically."""
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS scenarios (name TEXT PRIMARY KEY, paddock_json TEXT NOT NULL, parameters_json TEXT NOT NULL, events_json TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)");connection.commit()

def save_scenario(name: str,paddock: PaddockConfig,parameters: ModelParameters,events: list[ManagementEvent],path: Path=DB_PATH)->None:
    """Insert or replace a named scenario."""
    if not name.strip():raise ValueError("scenario name is required")
    initialise_database(path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("INSERT OR REPLACE INTO scenarios(name,paddock_json,parameters_json,events_json,updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)",(name.strip(),json.dumps(asdict(paddock)),json.dumps(asdict(parameters)),json.dumps([asdict(e) for e in events])));connection.commit()

def list_scenarios(path: Path=DB_PATH)->list[str]:
    """Return stored scenario names."""
    initialise_database(path)
    with closing(sqlite3.connect(path)) as connection:return [row[0] for row in connection.execute("SELECT name FROM scenarios ORDER BY name").fetchall()]

def load_scenario(name: str,path: Path=DB_PATH)->tuple[PaddockConfig,ModelParameters,list[ManagementEvent]]:
    """Load a stored scenario by name."""
    initialise_database(path)
    with closing(sqlite3.connect(path)) as connection:row=connection.execute("SELECT paddock_json,parameters_json,events_json FROM scenarios WHERE name=?",(name,)).fetchone()
    if row is None:raise KeyError(name)
    return PaddockConfig(**json.loads(row[0])),ModelParameters(**json.loads(row[1])),[ManagementEvent(**item) for item in json.loads(row[2])]
