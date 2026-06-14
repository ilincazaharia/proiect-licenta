import sys
import os
import io
import numpy as np
import simpy

# Setează encoding-ul standard output la UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adaugă directorul de lucru la path pentru a importa modulele
sys.path.insert(0, r"/")

from experiments.config import SimulationConfig
from experiments.runner import run_experiment
from simulation.strategies import PriorityFIFOStrategy

def main():
    strategy = PriorityFIFOStrategy()
    
    # Scenariul A - Triage Mix Standard (Red: 5%, Yellow: 15%, Green: 30%, Blue: 35%, White: 15%)
    # Folosim 7 medici și 10 asistente pentru a oferi timpi mult mai buni (optimi) în Scenariul A
    config_std = SimulationConfig(
        num_doctors=7,
        num_nurses=10,
        arrival_rate=12.0,
        simulation_duration=480.0,
        warmup_period=60.0,
        num_replications=30,
        random_seed=42,
        triage_distribution={
            1: 0.05,
            2: 0.15,
            3: 0.30,
            4: 0.35,
            5: 0.15
        }
    )
    
    # Scenariul B - Triage Mix Sever/Epidemie (Red: 20%, Yellow: 45%, Green: 20%, Blue: 10%, White: 5%)
    config_shift = SimulationConfig(
        num_doctors=7,
        num_nurses=10,
        arrival_rate=12.0,
        simulation_duration=480.0,
        warmup_period=60.0,
        num_replications=30,
        random_seed=42,
        triage_distribution={
            1: 0.20,
            2: 0.45,
            3: 0.20,
            4: 0.10,
            5: 0.05
        }
    )
    
    print("Rulare Scenariu A (Triage Standard)...")
    res_std = run_experiment(config_std, strategy)
    
    print("Rulare Scenariu B (Mix Sever / Epidemie)...")
    res_shift = run_experiment(config_shift, strategy)
    
    # Rezultate Scenariul A
    std_wait = np.mean([r["avg_waiting_time"] for r in res_std])
    std_comp = np.mean([r["target_compliance"] for r in res_std])
    std_w_red = np.mean([r["level_1_avg_wait"] for r in res_std])
    std_c_red = np.mean([r["level_1_target_compliance"] for r in res_std])
    std_w_yel = np.mean([r["level_2_avg_wait"] for r in res_std])
    std_c_yel = np.mean([r["level_2_target_compliance"] for r in res_std])
    std_w_gre = np.mean([r["level_3_avg_wait"] for r in res_std])
    std_c_gre = np.mean([r["level_3_target_compliance"] for r in res_std])
    std_w_blu = np.mean([r["level_4_avg_wait"] for r in res_std])
    std_c_blu = np.mean([r["level_4_target_compliance"] for r in res_std])
    std_w_whi = np.mean([r["level_5_avg_wait"] for r in res_std])
    std_c_whi = np.mean([r["level_5_target_compliance"] for r in res_std])
    
    # Rezultate Scenariul B
    shift_wait = np.mean([r["avg_waiting_time"] for r in res_shift])
    shift_comp = np.mean([r["target_compliance"] for r in res_shift])
    shift_w_red = np.mean([r["level_1_avg_wait"] for r in res_shift])
    shift_c_red = np.mean([r["level_1_target_compliance"] for r in res_shift])
    shift_w_yel = np.mean([r["level_2_avg_wait"] for r in res_shift])
    shift_c_yel = np.mean([r["level_2_target_compliance"] for r in res_shift])
    shift_w_gre = np.mean([r["level_3_avg_wait"] for r in res_shift])
    shift_c_gre = np.mean([r["level_3_target_compliance"] for r in res_shift])
    shift_w_blu = np.mean([r["level_4_avg_wait"] for r in res_shift])
    shift_c_blu = np.mean([r["level_4_target_compliance"] for r in res_shift])
    shift_w_whi = np.mean([r["level_5_avg_wait"] for r in res_shift])
    shift_c_whi = np.mean([r["level_5_target_compliance"] for r in res_shift])

    print("\n" + "="*95)
    print("REZULTATE EXPERIMENT MIX SEVERITATE / DEPRIVARE (Media pe 30 de replicări)")
    print("="*95)
    
    row_format = "{:<45} | {:<22} | {:<22}"
    print(row_format.format("Cod Triaj / Metrică", "Scenariu A (Std 20% Red+Yel)", "Scenariu B (Shift 65% Red+Yel)"))
    print("-" * 95)
    
    print(row_format.format("T.A. Mediu Global", f"{std_wait:.2f} min", f"{shift_wait:.2f} min"))
    print(row_format.format("Conformitate Globală UPU", f"{std_comp:.2f}%", f"{shift_comp:.2f}%"))
    print("-" * 95)
    print(row_format.format("T.A. Cod Roșu (Timp țintă: 0 min)", f"{std_w_red:.2f} min (C: {std_c_red:.1f}%)", f"{shift_w_red:.2f} min (C: {shift_c_red:.1f}%)"))
    print(row_format.format("T.A. Cod Galben (Timp țintă: < 15 min)", f"{std_w_yel:.2f} min (C: {std_c_yel:.1f}%)", f"{shift_w_yel:.2f} min (C: {shift_c_yel:.1f}%)"))
    print(row_format.format("T.A. Cod Verde (Timp țintă: < 60 min)", f"{std_w_gre:.2f} min (C: {std_c_gre:.1f}%)", f"{shift_w_gre:.2f} min (C: {shift_c_gre:.1f}%)"))
    print(row_format.format("T.A. Cod Albastru (Timp țintă: < 120 min)", f"{std_w_blu:.2f} min (C: {std_c_blu:.1f}%)", f"{shift_w_blu:.2f} min (C: {shift_c_blu:.1f}%)"))
    print(row_format.format("T.A. Cod Alb (Timp țintă: < 180 min)", f"{std_w_whi:.2f} min (C: {std_c_whi:.1f}%)", f"{shift_w_whi:.2f} min (C: {shift_c_whi:.1f}%)"))
    print("="*95)

if __name__ == "__main__":
    main()
