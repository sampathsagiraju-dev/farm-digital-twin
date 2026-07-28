"""Numerical orchestration for the coupled paddock digital twin."""
from __future__ import annotations
from typing import Literal
import pandas as pd
from data.generator import generate_environment_data
from models.paddock import ManagementEvent, PaddockConfig, SOIL_PRESETS
from models.pasture_model import ModelParameters, potential_growth, step_biomass, step_soil_water, water_stress
Scenario = Literal["Normal", "Drought"]

def parameters_for_paddock(paddock: PaddockConfig, base: ModelParameters | None = None) -> ModelParameters:
    """Apply soil and starting-state properties to model parameters."""
    from dataclasses import replace
    p=base or ModelParameters(); soil=SOIL_PRESETS[paddock.soil_type]
    return replace(p,field_capacity=soil["field_capacity"],wilting_point=soil["wilting_point"],drainage_factor=soil["drainage_factor"],initial_biomass=paddock.initial_biomass,initial_soil_water=min(paddock.initial_soil_water,soil["field_capacity"]))

def run_simulation(scenario: Scenario = "Normal", days: int = 30, seed: int = 42, start_date: str | pd.Timestamp | None = None, parameters: ModelParameters | None = None, events: list[ManagementEvent] | None = None) -> pd.DataFrame:
    """Integrate coupled states and apply dated management events."""
    if scenario not in ("Normal", "Drought"): raise ValueError("scenario must be 'Normal' or 'Drought'")
    p=parameters or ModelParameters(); event_map={event.day:event for event in (events or [])}
    environment=generate_environment_data(days,seed,start_date).copy(); environment["rainfall_mm"]*=.5 if scenario=="Drought" else 1.0
    soil_water,biomass,records=p.initial_soil_water,p.initial_biomass,[]
    for index,row in enumerate(environment.itertuples(index=False),start=1):
        event=event_map.get(index); irrigation=0.;removed=0.;fertiliser_factor=1.
        if event and event.kind=="Irrigation": irrigation=max(0.,event.amount)
        if event and event.kind=="Grazing":
            residual=max(0.,event.amount); removed=max(0.,biomass-residual); biomass=max(residual,min(biomass,residual))
        if event and event.kind=="Fertiliser": fertiliser_factor=1.+min(max(event.amount,0.),100.)/500.
        effective_rain=row.rainfall_mm+irrigation
        soil_water,et,drainage=step_soil_water(soil_water,effective_rain,row.temperature_c,p)
        moisture_factor=water_stress(soil_water,p); potential=potential_growth(row.rainfall_mm,row.temperature_c,p)*fertiliser_factor
        biomass,realised,senescence=step_biomass(biomass,potential,moisture_factor,p)
        records.append({"date":row.date,"day":index,"rainfall_mm":row.rainfall_mm,"irrigation_mm":irrigation,"temperature_c":row.temperature_c,"soil_water_mm":soil_water,"soil_moisture_pct":soil_water/p.field_capacity*100,"water_stress_factor":moisture_factor,"potential_growth_kg_dm_ha_day":potential,"pasture_growth_kg_dm_ha_day":realised,"pasture_biomass_kg_dm_ha":biomass,"evapotranspiration_mm":et,"drainage_mm":drainage,"senescence_kg_dm_ha_day":senescence,"grazing_removed_kg_dm_ha":removed,"management_event":event.kind if event else "None","scenario":scenario})
    result=pd.DataFrame(records); cols=result.select_dtypes("number").columns; result[cols]=result[cols].round(3); return result

def compare_scenarios(days: int=30,seed: int=42,parameters: ModelParameters|None=None,events: list[ManagementEvent]|None=None) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Run Normal and Drought against identical forcing and management."""
    return run_simulation("Normal",days,seed,parameters=parameters,events=events),run_simulation("Drought",days,seed,parameters=parameters,events=events)

def run_farm(paddocks: list[PaddockConfig],scenario: Scenario="Normal",days: int=30,seed: int=42,events_by_paddock: dict[str,list[ManagementEvent]]|None=None) -> pd.DataFrame:
    """Simulate multiple paddocks and combine their results."""
    frames=[]
    for offset,paddock in enumerate(paddocks):
        frame=run_simulation(scenario,days,seed+offset,parameters=parameters_for_paddock(paddock),events=(events_by_paddock or {}).get(paddock.name,[]));frame["paddock"]=paddock.name;frame["area_ha"]=paddock.area_ha;frame["total_biomass_kg_dm"]=frame.pasture_biomass_kg_dm_ha*paddock.area_ha;frames.append(frame)
    return pd.concat(frames,ignore_index=True)

def drought_growth_drop_percent(days: int=30,seed: int=42,parameters: ModelParameters|None=None,events: list[ManagementEvent]|None=None) -> float:
    """Return drought reduction in cumulative realised growth."""
    normal,drought=compare_scenarios(days,seed,parameters,events);total=normal.pasture_growth_kg_dm_ha_day.sum();return max(0.,(total-drought.pasture_growth_kg_dm_ha_day.sum())/total*100.) if total else 0.
