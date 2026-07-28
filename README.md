# Farm Paddock Digital Twin MVP

A small, extensible digital twin that connects synthetic environmental inputs,
a biological pasture model, scenario simulation, and an interactive dashboard.
It demonstrates the core twin loop: **observe → model → simulate → explain**.

## Architecture

```text
data/generator.py       Synthetic rainfall, temperature, and soil state
        ↓
models/pasture_model.py Stateless pasture-growth calculation
        ↓
twin/simulator.py       30-day Normal and Drought scenario orchestration
        ↓
dashboard/app.py        Streamlit charts, metrics, and decision insight
```

The modules are deliberately separated so future versions can add paddocks,
animals, sensors, forecasts, or calibrated models without replacing the UI.
The drought scenario uses the same seeded weather baseline as Normal, but
reduces rainfall by 50%, enabling an apples-to-apples comparison.

## Run locally

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run dashboard/app.py
```

Streamlit will print the local dashboard URL, normally
`http://localhost:8501`.

## Model

Daily pasture growth is calculated as:

```text
growth = 40 × (1 + 0.05 × rainfall) - 0.03 × max(0, temperature - 25)
```

Growth is expressed in kg DM/ha/day, rainfall in mm/day, temperature in °C,
and soil moisture as a percentage. The model is intentionally transparent and
illustrative; it is not a calibrated agronomic forecasting model.

## Run the simulator directly

```powershell
python -c "from twin.simulator import run_simulation; print(run_simulation('Drought').head())"
```

All dependencies are open source: NumPy, pandas, Streamlit, and Matplotlib.

## Backend v2

The twin now supports paddock domain objects and soil presets, dated irrigation,
grazing and fertiliser events, multi-paddock farm simulation, P10/P50/P90 Monte
Carlo forecast envelopes, and SQLite scenario persistence. These capabilities
are implemented in `models/paddock.py`, `twin/uncertainty.py`,
`storage/repository.py`, and the extended `twin/simulator.py`.
