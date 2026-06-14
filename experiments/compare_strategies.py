"""
Compara diferite strategii de gestionare a cozilor de asteptare
"""
from experiments.config import SimulationConfig
from experiments.runner import run_all_experiments
from experiments.analysis import analyze_results


def main():
    print("-" * 60)
    print("Comparatie Strategii de Coada")
    print("-" * 60)

    config = SimulationConfig(
        num_doctors=10,
        num_nurses=20,
        arrival_rate=12.0,
        simulation_duration=480.0,    # 8 ore
        warmup_period=60.0,
        num_replications=30,
        random_seed=42,
    )

    print(f"\n  Parametri simulare:")
    print(f"    Medici: {config.num_doctors}")
    print(f"    Asistente: {config.num_nurses}")
    print(f"    Rata sosire: {config.arrival_rate} pacienti/ora")
    print(f"    Durata: {config.simulation_duration} min ({config.simulation_duration / 60:.0f} ore)")
    print(f"    Warmup: {config.warmup_period} min")
    print(f"    Replicari: {config.num_replications}")
    print()

    print("  Rulare experimente...")
    all_results = run_all_experiments(config)

    print("\n  Analiza rezultate...")
    summary = analyze_results(all_results, output_dir="results")

    print("\n  Rezultate generate")
