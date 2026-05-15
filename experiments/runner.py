"""
Runner pentru experimente — ruleaza simulari cu diferite strategii.
"""
import simpy
import numpy as np
from simulation.engine import EmergencyDepartment
from simulation.metrics import compute_metrics
from simulation.strategies import QueueStrategy, ALL_STRATEGIES
from experiments.config import SimulationConfig


def run_single_simulation(config: SimulationConfig, strategy: QueueStrategy, seed: int) -> dict:
    """Ruleaza o singura simulare si returneaza metricile."""
    env = simpy.Environment()
    rng = np.random.default_rng(seed)

    department = EmergencyDepartment(env, config, strategy, rng)
    department.run()

    patients = department.get_results()
    metrics = compute_metrics(patients)
    metrics["strategy"] = strategy.name
    metrics["seed"] = seed
    return metrics


def run_experiment(config: SimulationConfig, strategy: QueueStrategy) -> list[dict]:
    """Ruleaza toate replicarile pentru o strategie data."""
    results = []
    for i in range(config.num_replications):
        seed = config.random_seed + i
        metrics = run_single_simulation(config, strategy, seed)
        metrics["replication"] = i + 1
        results.append(metrics)
    return results


def run_all_experiments(config: SimulationConfig, strategies: list[QueueStrategy] = None) -> list[dict]:
    """
    Ruleaza experimentele pentru toate strategiile.
    Returneaza o lista cu toate rezultatele (toate replicarile, toate strategiile).
    """
    if strategies is None:
        strategies = ALL_STRATEGIES

    all_results = []
    for strategy in strategies:
        print(f"  Rulare strategie: {strategy.name} ({config.num_replications} replicari)...")
        results = run_experiment(config, strategy)
        all_results.extend(results)
        avg_wait = np.mean([r["avg_waiting_time"] for r in results])
        print(f"    -> Timp mediu asteptare: {avg_wait:.1f} min")

    return all_results
