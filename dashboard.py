import streamlit as st
import pandas as pd
import os
from experiments.config import SimulationConfig
from experiments.runner import run_all_experiments
from experiments.analysis import analyze_results

# Setare pagina
st.set_page_config(page_title="Simulare UPU", layout="wide")

st.title("Dashboard Simulare UPU")
st.markdown("Acest panou de control permite compararea diferitelor strategii de gestionare a pacienților în Unitățile de Primiri Urgențe (UPU), pe baza parametrilor configurabili.")

# --- SIDEBAR CONFIGURARE ---
st.sidebar.header("Configurare Parametri")

st.sidebar.subheader("Resurse Umane")
num_doctors = st.sidebar.number_input("Număr Medici", min_value=1, value=3, step=1)
num_nurses = st.sidebar.number_input("Număr Asistente", min_value=1, value=2, step=1)

st.sidebar.subheader("Flux Pacienți")
arrival_rate = st.sidebar.number_input("Rata de sosire (pacienți/oră)", min_value=1.0, value=12.0, step=1.0)

st.sidebar.subheader("Distribuție Triaj (%)")
st.sidebar.markdown("Suma valorilor trebuie să fie 100%.")
col1, col2 = st.sidebar.columns(2)
with col1:
    p_red = st.number_input("Cod Roșu", min_value=0, max_value=100, value=5, step=1)
    p_yellow = st.number_input("Cod Galben", min_value=0, max_value=100, value=15, step=1)
    p_green = st.number_input("Cod Verde", min_value=0, max_value=100, value=30, step=1)
with col2:
    p_blue = st.number_input("Cod Albastru", min_value=0, max_value=100, value=35, step=1)
    p_white = st.number_input("Cod Alb", min_value=0, max_value=100, value=15, step=1)

total_p = p_red + p_yellow + p_green + p_blue + p_white
if total_p != 100:
    st.sidebar.error(f"Atenție: Suma procentelor este {total_p}%. Ajustați valorile pentru a atinge 100%.")

st.sidebar.subheader("Timpi Medii Tratament (minute)")
t_red = st.sidebar.number_input("Timp Cod Roșu", min_value=1, value=45, step=5)
t_yellow = st.sidebar.number_input("Timp Cod Galben", min_value=1, value=30, step=5)
t_green = st.sidebar.number_input("Timp Cod Verde", min_value=1, value=20, step=5)
t_blue = st.sidebar.number_input("Timp Cod Albastru", min_value=1, value=15, step=5)
t_white = st.sidebar.number_input("Timp Cod Alb", min_value=1, value=10, step=5)

st.sidebar.subheader("Parametri Simulare")
sim_duration = st.sidebar.number_input("Durata simulare (minute)", min_value=60, value=480, step=60)
replications = st.sidebar.number_input("Număr replicări", min_value=1, value=30, step=1)

# --- MAIN AREA ---
if st.button("Rulează Simularea", type="primary", disabled=(total_p != 100)):
    with st.spinner("Rulare experimente în progres. Vă rugăm așteptați..."):
        
        # Generare config
        config = SimulationConfig(
            num_doctors=num_doctors,
            num_nurses=num_nurses,
            arrival_rate=arrival_rate,
            simulation_duration=sim_duration,
            num_replications=replications,
            triage_distribution={
                1: p_red / 100.0,
                2: p_yellow / 100.0,
                3: p_green / 100.0,
                4: p_blue / 100.0,
                5: p_white / 100.0,
            },
            treatment_times={
                1: (t_red, max(1, int(t_red * 0.3))),
                2: (t_yellow, max(1, int(t_yellow * 0.3))),
                3: (t_green, max(1, int(t_green * 0.3))),
                4: (t_blue, max(1, int(t_blue * 0.3))),
                5: (t_white, max(1, int(t_white * 0.3))),
            }
        )
        
        # Rulare backend
        all_results = run_all_experiments(config)
        summary = analyze_results(all_results, output_dir="results")
        
        st.success("Simularea a fost completată cu succes.")
        
        # Afisare Rezultate
        st.subheader("Tabel Rezumat Rezultate")
        st.dataframe(summary, use_container_width=True)
        
        st.subheader("Vizualizări")
        st.markdown("Analiza comparativă a performanței strategiilor de gestionare a pacienților.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if os.path.exists("results/1_avg_waiting_time.png"):
                st.image("results/1_avg_waiting_time.png")
            if os.path.exists("results/3_los_boxplot.png"):
                st.image("results/3_los_boxplot.png")
            if os.path.exists("results/5_heatmap.png"):
                st.image("results/5_heatmap.png")
                
        with col2:
            if os.path.exists("results/2_waiting_by_level.png"):
                st.image("results/2_waiting_by_level.png")
            if os.path.exists("results/4_target_compliance.png"):
                st.image("results/4_target_compliance.png")
