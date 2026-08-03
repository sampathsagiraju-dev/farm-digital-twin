"""Monte Carlo ensemble utilities for forecast uncertainty."""
from __future__ import annotations

import numpy as np
import pandas as pd

from models.paddock import ManagementEvent
from models.pasture_model import ModelParameters
from twin.simulator import Scenario, run_simulation


def run_ensemble(
    scenario: Scenario,
    days: int,
    seed: int,
    parameters: ModelParameters,
    events: list[ManagementEvent] | None = None,
    members: int = 60,
) -> pd.DataFrame:
    """Run many weather realisations and return P10/P50/P90 state envelopes."""
    if members < 10:
        raise ValueError("members must be at least 10")

    member_frames = []
    for member in range(members):
        frame = run_simulation(
            scenario, days, seed + member, parameters=parameters, events=events
        )
        frame["member"] = member
        member_frames.append(frame)
    ensemble = pd.concat(member_frames, ignore_index=True)

    rows = []
    day_index = ensemble.groupby("member").cumcount()
    for day, group in ensemble.groupby(day_index):
        rows.append(
            {
                "day": int(day) + 1,
                "date": group["date"].iloc[0],
                "biomass_p10": float(np.quantile(group.pasture_biomass_kg_dm_ha, 0.10)),
                "biomass_p50": float(np.quantile(group.pasture_biomass_kg_dm_ha, 0.50)),
                "biomass_p90": float(np.quantile(group.pasture_biomass_kg_dm_ha, 0.90)),
                "soil_water_p10": float(np.quantile(group.soil_water_mm, 0.10)),
                "soil_water_p50": float(np.quantile(group.soil_water_mm, 0.50)),
                "soil_water_p90": float(np.quantile(group.soil_water_mm, 0.90)),
            }
        )

    result = pd.DataFrame(rows)
    numeric_cols = result.select_dtypes("number").columns
    result[numeric_cols] = result[numeric_cols].round(3)
    return result
