"""
Calcul metrici din rezultatele simularii.
"""
import numpy as np
from simulation.models import Patient, TriageLevel


def compute_metrics(patients: list[Patient]) -> dict:
    """
    Calculeaza metricile principale din lista de pacienti tratati.

    Returns:
        dict cu metrici agregate
    """
    if not patients:
        return _empty_metrics()

    waiting_times = [p.waiting_time for p in patients if p.waiting_time is not None]
    los_times = [p.total_time_in_system for p in patients if p.total_time_in_system is not None]

    metrics = {
        "total_patients": len(patients),
        "avg_waiting_time": np.mean(waiting_times) if waiting_times else 0,
        "median_waiting_time": np.median(waiting_times) if waiting_times else 0,
        "max_waiting_time": np.max(waiting_times) if waiting_times else 0,
        "avg_los": np.mean(los_times) if los_times else 0,
        "median_los": np.median(los_times) if los_times else 0,
        "target_compliance": np.mean([p.met_target for p in patients]) * 100,
    }

    # Metrici per nivel de triaj
    for level in TriageLevel:
        level_patients = [p for p in patients if p.triage_level == level]
        level_wt = [p.waiting_time for p in level_patients if p.waiting_time is not None]

        prefix = f"level_{level.value}"
        metrics[f"{prefix}_count"] = len(level_patients)
        metrics[f"{prefix}_avg_wait"] = np.mean(level_wt) if level_wt else 0
        metrics[f"{prefix}_median_wait"] = np.median(level_wt) if level_wt else 0
        metrics[f"{prefix}_max_wait"] = np.max(level_wt) if level_wt else 0
        metrics[f"{prefix}_target_compliance"] = (
            np.mean([p.met_target for p in level_patients]) * 100
            if level_patients else 0
        )

    return metrics


def _empty_metrics() -> dict:
    """Returneaza metrici goale cand nu exista pacienti."""
    metrics = {
        "total_patients": 0,
        "avg_waiting_time": 0,
        "median_waiting_time": 0,
        "max_waiting_time": 0,
        "avg_los": 0,
        "median_los": 0,
        "target_compliance": 0,
    }
    for level in TriageLevel:
        prefix = f"level_{level.value}"
        metrics[f"{prefix}_count"] = 0
        metrics[f"{prefix}_avg_wait"] = 0
        metrics[f"{prefix}_median_wait"] = 0
        metrics[f"{prefix}_max_wait"] = 0
        metrics[f"{prefix}_target_compliance"] = 0
    return metrics
