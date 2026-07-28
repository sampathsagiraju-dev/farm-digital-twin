"""Engineering console for the paddock digital twin."""
from __future__ import annotations
import sys
from dataclasses import replace
from pathlib import Path
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import streamlit as st
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from models.pasture_model import ModelParameters
from models.paddock import ManagementEvent, PaddockConfig, SOIL_PRESETS
from storage.repository import list_scenarios, save_scenario
from twin.simulator import compare_scenarios
from twin.uncertainty import run_ensemble

st.set_page_config(page_title="Paddock Twin Studio", page_icon="◈", layout="wide")
st.markdown("""<style>
header[data-testid="stHeader"] {height:3rem; visibility:visible; background:transparent; position:fixed; top:0; left:0; right:0; z-index:99999; pointer-events:none;}
header[data-testid="stHeader"] button {pointer-events:auto;}
button[data-testid="stBaseButton-headerNoPadding"] {visibility:visible !important; opacity:1 !important; display:inline-flex !important; background:#ffffff !important; border:1px solid #cfdacf !important; border-radius:9px !important; box-shadow:0 3px 12px rgba(35,64,42,.14) !important; width:34px !important; height:34px !important;}
[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display:flex !important; position:fixed !important; top:.55rem !important; left:.55rem !important; z-index:999999 !important; background:#ffffff !important; border:1px solid #cfdacf !important; border-radius:9px !important; box-shadow:0 3px 12px rgba(35,64,42,.12) !important;}
[data-testid="stDecoration"], [data-testid="stBaseButton-header"], [data-testid="stMainMenuButton"] {display:none !important;}
[data-testid="stToolbar"] {display:flex !important; pointer-events:none;}
[data-testid="stExpandSidebarButton"] {display:flex !important; visibility:visible !important; pointer-events:auto !important; position:fixed !important; top:.75rem !important; left:.75rem !important; width:36px !important; height:36px !important; background:#ffffff !important; border:1px solid #cfdacf !important; border-radius:9px !important; box-shadow:0 3px 12px rgba(35,64,42,.14) !important;}
html, body, .stApp {background:#f4f6f1; color:#223127;}
.stApp {background:linear-gradient(180deg,#eef4eb 0,#f7f8f4 220px,#f7f8f4 100%);}
[data-testid="stSidebar"] {background:#ffffff; border-right:1px solid #dfe6dc;}
[data-testid="stSidebar"] > div:first-child {padding-top:1rem;}
.block-container {padding-top:.35rem !important; padding-bottom:2rem; max-width:1500px;}
[data-testid="stMetric"] {background:#ffffff; border:1px solid #dce5da; border-radius:12px; padding:16px 18px; box-shadow:0 3px 14px rgba(35,64,42,.05);}
[data-testid="stMetricLabel"] {color:#657369;}
[data-testid="stMetricValue"] {color:#173c2a; font-family:ui-monospace,monospace;}
[data-testid="stMetricDelta"] {color:#6a7a6e;}
.eyebrow {color:#367c4b; letter-spacing:.16em; font-size:.7rem; font-weight:750; padding-top:.15rem;}
.hero {font-size:2.05rem; line-height:1.15; font-weight:700; color:#193426; margin-top:.2rem;}
.sub {color:#718078; margin:.25rem 0 1rem;}
.status {display:inline-block; color:#27733f; background:#e7f5e9; border:1px solid #b9dbbf; border-radius:99px; padding:.35rem .7rem; font-size:.7rem; margin-top:.4rem;}
.schematic {background:#ffffff; border:1px solid #dde6db; padding:22px; border-radius:12px; display:flex; align-items:center; justify-content:space-around; gap:10px; box-shadow:0 3px 14px rgba(35,64,42,.04);}
.node {min-width:140px; text-align:center; border:1px solid #cfe0d1; background:#f3f8f2; padding:15px 10px; border-radius:9px; color:#46594c; font-family:ui-monospace,monospace; font-size:.8rem;}
.node b {display:block; color:#216b3d; font-size:.95rem; margin-bottom:5px;}
.arrow {color:#82a88b; font-size:1.4rem;}
.insight {border-left:4px solid #4c9560; background:#edf6ec; padding:16px 18px; border-radius:0 9px 9px 0; color:#314a37;}
.stTabs [data-baseweb="tab-list"] {gap:8px; border-bottom:1px solid #dce4da;}
.stTabs [data-baseweb="tab"] {background:#ffffff; border:1px solid #dce4da; border-radius:8px 8px 0 0; color:#53635a; padding:8px 16px;}
.stTabs [aria-selected="true"] {color:#24623a; background:#edf5eb;}
h1,h2,h3,h4 {color:#263b2d;}
</style>""",unsafe_allow_html=True)

p0=ModelParameters()
with st.sidebar:
 st.markdown("### ◈ TWIN CONTROLS")
 scenario=st.selectbox("Active scenario",["Normal","Drought"])
 days=st.slider("Simulation horizon (days)",14,120,60)
 seed=st.number_input("Weather seed",1,9999,42)
 st.divider();st.markdown("#### PADDOCK")
 paddock_name=st.text_input("Paddock name","North Paddock")
 area=st.number_input("Area (ha)",1.0,500.0,12.0)
 soil_type=st.selectbox("Soil type",["Loam","Sandy","Clay"])
 st.divider();st.markdown("#### BIOLOGICAL MODEL")
 base=st.slider("Base growth (kg DM/ha/day)",10.,80.,40.)
 alpha=st.slider("Rain response α",0.,.10,.05,.005)
 beta=st.slider("Heat stress β",0.,.20,.03,.005)
 sen=st.slider("Senescence (%/day)",.2,3.,.8)/100
 st.divider();st.markdown("#### SOIL RESERVOIR")
 fc=st.slider("Field capacity (mm)",80.,200.,110.)
 iw=st.slider("Initial soil water (mm)",20.,fc,min(90.,fc))
 st.divider();st.markdown("#### MANAGEMENT EVENTS")
 irrigation_on=st.toggle("Schedule irrigation",True)
 irrigation_day=st.slider("Irrigation day",1,int(days),min(12,int(days)))
 irrigation_amount=st.slider("Irrigation amount (mm)",0.,50.,20.)
 grazing_on=st.toggle("Schedule grazing",True)
 grazing_day=st.slider("Grazing day",1,int(days),min(35,int(days)))
 grazing_residual=st.slider("Post-grazing residual (kg DM/ha)",800.,2200.,1500.)
 st.caption("Solver: explicit state integration · Δt = 1 day")
soil=SOIL_PRESETS[soil_type]
p=replace(p0,base_growth=base,rainfall_response=alpha,heat_stress_coefficient=beta,senescence_rate=sen,field_capacity=fc,wilting_point=soil["wilting_point"],drainage_factor=soil["drainage_factor"],initial_soil_water=iw)
paddock=PaddockConfig(paddock_name,float(area),soil_type,p.initial_biomass,iw)
events=[]
if irrigation_on: events.append(ManagementEvent(int(irrigation_day),"Irrigation",float(irrigation_amount)))
if grazing_on: events.append(ManagementEvent(int(grazing_day),"Grazing",float(grazing_residual)))
with st.sidebar:
 scenario_name=st.text_input("Save configuration as","My farm scenario")
 if st.button("Save scenario",use_container_width=True):
  save_scenario(scenario_name,paddock,p,events);st.success(f"Saved {scenario_name}")
 st.caption(f"{len(list_scenarios())} saved scenario(s)")
normal,drought=compare_scenarios(int(days),int(seed),p,events);active=normal if scenario=="Normal" else drought
ng=normal.pasture_growth_kg_dm_ha_day.sum();dg=drought.pasture_growth_kg_dm_ha_day.sum();drop=(ng-dg)/ng*100 if ng else 0;last=active.iloc[-1]

a,b=st.columns([5,1])
with a: st.markdown('<div class="eyebrow">AGRO-SYSTEMS / DIGITAL TWIN</div><div class="hero">Paddock Twin Studio</div><div class="sub">Coupled soil–water–pasture simulation environment</div>',unsafe_allow_html=True)
with b: st.markdown('<div class="status">● MODEL ONLINE</div>',unsafe_allow_html=True)
cols=st.columns(5)
cols[0].metric("Pasture biomass",f"{last.pasture_biomass_kg_dm_ha:,.0f}","kg DM/ha")
cols[1].metric("Soil water",f"{last.soil_water_mm:.1f}","mm")
cols[2].metric("Growth rate",f"{last.pasture_growth_kg_dm_ha_day:.1f}","kg DM/ha/d")
cols[3].metric("Water state","STRESSED" if last.water_stress_factor<.35 else "NOMINAL",f"{last.water_stress_factor:.0%} factor")
cols[4].metric("Drought impact",f"−{drop:.1f}%","cumulative growth")

def style(ax,label):
 ax.set_facecolor("#ffffff");ax.figure.set_facecolor("#ffffff");ax.grid(color="#dfe7dd",alpha=.9,lw=.7);ax.tick_params(colors="#68776d",labelsize=8);ax.set_ylabel(label,color="#526258",fontsize=9);ax.spines[["top","right"]].set_visible(False);ax.spines[["left","bottom"]].set_color("#cbd6cc");ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

overview,comparison,uncertainty,diagnostics,equations=st.tabs(["SYSTEM OVERVIEW","SCENARIO LAB","UNCERTAINTY","DIAGNOSTICS","MODEL EQUATIONS"])
with overview:
 st.markdown("#### SYSTEM TOPOLOGY")
 st.markdown(f'''<div class="schematic"><div class="node"><b>WEATHER</b>{active.rainfall_mm.sum():.1f} mm rain<br>{active.temperature_c.mean():.1f} °C mean</div><div class="arrow">→</div><div class="node"><b>SOIL RESERVOIR</b>{last.soil_water_mm:.1f} mm<br>ET {active.evapotranspiration_mm.sum():.1f} mm</div><div class="arrow">→</div><div class="node"><b>WATER STRESS</b>{last.water_stress_factor:.2f}<br>dimensionless</div><div class="arrow">→</div><div class="node"><b>PASTURE</b>{last.pasture_biomass_kg_dm_ha:,.0f} kg DM/ha<br>+{active.pasture_growth_kg_dm_ha_day.sum():.0f} kg growth</div></div>''',unsafe_allow_html=True)
 st.markdown("#### STATE TRAJECTORIES")
 fig,ax=plt.subplots(2,1,figsize=(13,7),sharex=True);ax[0].plot(active.date,active.pasture_biomass_kg_dm_ha,color="#3f8f55",lw=2);ax[0].fill_between(active.date,active.pasture_biomass_kg_dm_ha,color="#3f8f55",alpha=.12);style(ax[0],"Biomass (kg DM/ha)");ax[1].plot(active.date,active.soil_water_mm,color="#287fa3",lw=2);ax[1].axhline(p.wilting_point,color="#c65c4b",ls="--",label="Wilting point");ax[1].axhline(p.field_capacity,color="#82968a",ls=":",label="Field capacity");style(ax[1],"Soil water (mm)");ax[1].legend(frameon=False,labelcolor="#526258");fig.tight_layout();st.pyplot(fig,use_container_width=True);plt.close(fig)
with comparison:
 st.markdown("#### NORMAL vs DROUGHT — IDENTICAL WEATHER REALISATION")
 fig,ax=plt.subplots(1,2,figsize=(13,4.5))
 for frame,label,color in [(normal,"Normal","#287fa3"),(drought,"Drought","#d9823b")]: ax[0].plot(frame.date,frame.pasture_biomass_kg_dm_ha,label=label,color=color,lw=2);ax[1].plot(frame.date,frame.soil_water_mm,label=label,color=color,lw=2)
 style(ax[0],"Biomass (kg DM/ha)");style(ax[1],"Soil water (mm)")
 for x in ax:x.legend(frameon=False,labelcolor="#526258")
 fig.tight_layout();st.pyplot(fig,use_container_width=True);plt.close(fig)
 gap=normal.iloc[-1].pasture_biomass_kg_dm_ha-drought.iloc[-1].pasture_biomass_kg_dm_ha
 st.markdown(f'<div class="insight"><b>Simulation insight</b><br>Drought removes {normal.rainfall_mm.sum()-drought.rainfall_mm.sum():.1f} mm rainfall, reduces cumulative realised growth by <b>{drop:.1f}%</b>, and finishes {gap:.0f} kg DM/ha lower.</div>',unsafe_allow_html=True)
with uncertainty:
 st.markdown("#### MONTE CARLO FORECAST ENVELOPE")
 st.caption("Forty synthetic weather realisations quantify forecast spread with the active model and management plan.")
 ensemble=run_ensemble(scenario,int(days),int(seed),p,events,40)
 fig,ax=plt.subplots(2,1,figsize=(13,7),sharex=True)
 ax[0].fill_between(ensemble.date,ensemble.biomass_p10,ensemble.biomass_p90,color="#8fc69d",alpha=.35,label="P10–P90")
 ax[0].plot(ensemble.date,ensemble.biomass_p50,color="#367c4b",lw=2,label="Median")
 style(ax[0],"Biomass (kg DM/ha)");ax[0].legend(frameon=False,labelcolor="#526258")
 ax[1].fill_between(ensemble.date,ensemble.soil_water_p10,ensemble.soil_water_p90,color="#85bbd2",alpha=.35,label="P10–P90")
 ax[1].plot(ensemble.date,ensemble.soil_water_p50,color="#287fa3",lw=2,label="Median")
 style(ax[1],"Soil water (mm)");ax[1].legend(frameon=False,labelcolor="#526258")
 fig.tight_layout();st.pyplot(fig,use_container_width=True);plt.close(fig)
 spread=ensemble.iloc[-1].biomass_p90-ensemble.iloc[-1].biomass_p10
 st.markdown(f'<div class="insight"><b>Forecast confidence</b><br>The final P10–P90 biomass spread is <b>{spread:.0f} kg DM/ha</b> across 40 weather realisations.</div>',unsafe_allow_html=True)
with diagnostics:
 st.markdown("#### FORCING, FLUXES AND CONSTRAINTS")
 fig,ax=plt.subplots(3,1,figsize=(13,8),sharex=True);ax[0].bar(active.date,active.rainfall_mm,color="#4b91b5");style(ax[0],"Rain (mm)");ax[1].plot(active.date,active.temperature_c,color="#d9823b");style(ax[1],"Temperature (°C)");ax[2].plot(active.date,active.pasture_growth_kg_dm_ha_day,color="#3f8f55",label="Realised");ax[2].plot(active.date,active.potential_growth_kg_dm_ha_day,color="#89968e",ls="--",label="Potential");style(ax[2],"Growth (kg DM/ha/d)");ax[2].legend(frameon=False,labelcolor="#526258");fig.tight_layout();st.pyplot(fig,use_container_width=True);plt.close(fig)
 with st.expander("VARIABLE BROWSER / RESULT TABLE"):
  st.dataframe(active,hide_index=True,use_container_width=True);st.download_button("Export simulation CSV",active.to_csv(index=False),"paddock_twin.csv","text/csv")
with equations:
 st.markdown("#### COUPLED EQUATION SET")
 st.latex(r"G_{potential}=G_0(1+\alpha R)-\beta\max(0,T-25)")
 st.latex(r"W_{t+1}=\operatorname{clip}(W_t+R-ET-D,0,W_{FC})")
 st.latex(r"f_W=\operatorname{clip}\left(\frac{W-W_{WP}}{W_{FC}-W_{WP}},0,1\right)")
 st.latex(r"B_{t+1}=B_t+G_{potential}f_W-sB_t")
 st.info("State variables: soil water W and biomass B. External forcing: rainfall R and temperature T. Algebraic outputs: evapotranspiration, drainage, potential growth and water stress.")











