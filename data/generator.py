"""Generate synthetic weather and soil observations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_environment_data(
    days: int = 30,
    seed: int = 42,
    start_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Return reproducible daily rainfall, temperature, and soil moisture.

    Soil moisture is represented as a percentage and responds to rainfall,
    evaporation, and drainage. Values are constrained to a plausible 10–100%.
    """
    if days <= 0:
        raise ValueError("days must be greater than zero")

    rng = np.random.default_rng(seed)
    dates = pd.date_range(
        start=pd.Timestamp(start_date) if start_date else pd.Timestamp.today().normalize(),
        periods=days,
        freq="D",
    )

    # Many days are dry; wet days receive skewed, non-negative rainfall.
    wet_days = rng.random(days) < 0.42
    rainfall = np.where(wet_days, rng.gamma(shape=1.7, scale=4.0, size=days), 0.0)

    # A gentle cycle plus random variation gives the dashboard a natural shape.
    seasonal_cycle = 3.0 * np.sin(np.linspace(0, 2 * np.pi, days))
    temperature = 21.0 + seasonal_cycle + rng.normal(0.0, 1.8, days)

    soil_moisture = np.empty(days)
    soil_moisture[0] = 55.0
    for day in range(1, days):
        evaporation = max(0.0, temperature[day] - 12.0) * 0.35
        recharge = rainfall[day] * 1.25
        drainage = max(0.0, soil_moisture[day - 1] - 75.0) * 0.08
        soil_moisture[day] = np.clip(
            soil_moisture[day - 1] + recharge - evaporation - drainage,
            10.0,
            100.0,
        )

    return pd.DataFrame(
        {
            "date": dates,
            "rainfall_mm": rainfall.round(2),
            "temperature_c": temperature.round(2),
            "soil_moisture_pct": soil_moisture.round(2),
        }
    )
