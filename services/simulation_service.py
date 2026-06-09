import numpy as np
import pandas as pd
import scipy.stats as stats
from typing import List, Tuple, Optional, Dict, Any
from repositories.simulation_repository import SimulationRunRepository
from domain.models import SimulationRun
from experiments.config import SimulationConfig
from experiments.runner import run_all_experiments
from experiments.analysis import analyze_results

class SimulationService:
    def __init__(self, simulation_repository: Optional[SimulationRunRepository] = None):
        self.simulation_repo = simulation_repository or SimulationRunRepository()

    def run_experiments(self, config: SimulationConfig) -> List[Dict[str, Any]]:
        """Apelează motorul SimPy pentru a rula replicările pe toate strategiile."""
        return run_all_experiments(config)

    def analyze_active_results(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apelează funcția de analiză și întoarce tabelul sumar general."""
        return analyze_results(results, output_dir="results")

    def save_simulation(self, user_id: int, run_name: str, config: SimulationConfig, results: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Pregătește și salvează rularea în baza de date prin repozitoriu."""
        run = SimulationRun(
            id=None,
            user_id=user_id,
            run_name=run_name,
            num_doctors=config.num_doctors,
            num_nurses=config.num_nurses,
            arrival_rate=config.arrival_rate,
            peak_multiplier=config.peak_multiplier,
            peak_start_min=config.peak_start_min,
            peak_duration_min=config.peak_duration_min,
            simulation_duration=config.simulation_duration,
            warmup_period=config.warmup_period,
            num_replications=config.num_replications,
            random_seed=config.random_seed,
            triage_distribution=config.triage_distribution,
            treatment_times=config.treatment_times,
            results_json=results
        )
        success = self.simulation_repo.save(run)
        if success:
            return True, "Simularea a fost salvată în istoric."
        return False, "Eroare la salvarea rulării în baza de date."

    def get_user_history(self, user_id: int) -> List[SimulationRun]:
        """Obține istoricul de simulări salvate ale utilizatorului."""
        return self.simulation_repo.get_by_user_id(user_id)

    def delete_run(self, run_id: int, user_id: int) -> Tuple[bool, str]:
        """Șterge o simulare din istoric."""
        success = self.simulation_repo.delete(run_id, user_id)
        if success:
            return True, "Simularea a fost ștearsă din istoric."
        return False, "Eroare la ștergerea simulării."

    def rename_run(self, run_id: int, user_id: int, new_name: str) -> Tuple[bool, str]:
        """Redenumește o simulare din istoric."""
        new_name = new_name.strip()
        if not new_name:
            return False, "Numele simulării nu poate fi gol."
        success = self.simulation_repo.rename(run_id, user_id, new_name)
        if success:
            return True, "Simularea a fost redenumită cu succes."
        return False, "Eroare la redenumirea simulării."

    def export_detailed_csv(self, results: List[Dict[str, Any]]) -> bytes:
        """Generează fișierul CSV detaliat din memorie (doar Priority + FIFO, fără coloana strategy)."""
        df_all = pd.DataFrame(results)
        df_p_fifo = df_all[df_all["strategy"] == "Priority + FIFO"]
        df_detalii = df_p_fifo.drop(columns=["strategy"]) if "strategy" in df_p_fifo.columns else df_p_fifo
        return df_detalii.to_csv(index=False).encode('utf-8')

    def export_summary_csv(self, results: List[Dict[str, Any]]) -> bytes:
        """Generează fișierul CSV sumar din memorie (doar Priority + FIFO, fără coloana strategy)."""
        df_all = pd.DataFrame(results)
        df_p_fifo = df_all[df_all["strategy"] == "Priority + FIFO"]
        
        rows_sumar = []
        row_s = {}
        for metric in ["avg_waiting_time", "avg_los", "total_patients", "target_compliance"]:
            values_metric = df_p_fifo[metric].values
            mean_val = np.mean(values_metric)
            if len(values_metric) > 1:
                ci_val = stats.t.interval(0.95, len(values_metric) - 1, loc=mean_val, scale=stats.sem(values_metric))
                ci_low = ci_val[0]
                ci_high = ci_val[1]
            else:
                ci_low = mean_val
                ci_high = mean_val
            row_s[f"{metric}_mean"] = round(mean_val, 2)
            row_s[f"{metric}_ci_low"] = round(ci_low, 2)
            row_s[f"{metric}_ci_high"] = round(ci_high, 2)
            
        rows_sumar.append(row_s)
        df_sumar = pd.DataFrame(rows_sumar)
        return df_sumar.to_csv(index=False).encode('utf-8')
