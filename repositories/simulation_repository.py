import sqlite3
import json
from typing import List, Optional
from repositories.db_connection import DBConnection
from domain.models import SimulationRun

class SimulationRunRepository:
    def __init__(self):
        pass

    def save(self, run: SimulationRun) -> bool:
        """Salvează o rulare de simulare în baza de date."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO simulation_runs (
                    user_id, run_name, num_doctors, num_nurses, arrival_rate, 
                    peak_multiplier, peak_start_min, peak_duration_min, 
                    simulation_duration, warmup_period, num_replications, random_seed, 
                    triage_distribution, treatment_times, results_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.user_id,
                run.run_name,
                run.num_doctors,
                run.num_nurses,
                run.arrival_rate,
                run.peak_multiplier,
                run.peak_start_min,
                run.peak_duration_min,
                run.simulation_duration,
                run.warmup_period,
                run.num_replications,
                run.random_seed,
                json.dumps(run.triage_distribution),
                json.dumps(run.treatment_times),
                json.dumps(run.results_json)
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în SimulationRunRepository.save: {e}")
            return False

    def get_by_user_id(self, user_id: int) -> List[SimulationRun]:
        """Returnează toate simulările salvate pentru un utilizator."""
        try:
            conn = DBConnection.get_connection()
            # row_factory ne permite accesul prin nume coloană
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, run_name, num_doctors, num_nurses, arrival_rate, 
                       peak_multiplier, peak_start_min, peak_duration_min, 
                       simulation_duration, warmup_period, num_replications, random_seed, 
                       triage_distribution, treatment_times, results_json, created_at
                FROM simulation_runs
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            
            runs = []
            for r in rows:
                triage_dist_raw = json.loads(r['triage_distribution'])
                triage_distribution = {int(k): float(v) for k, v in triage_dist_raw.items()}
                
                treatment_times_raw = json.loads(r['treatment_times'])
                treatment_times = {int(k): tuple(map(int, v)) for k, v in treatment_times_raw.items()}
                
                results_json = json.loads(r['results_json'])
                
                run = SimulationRun(
                    id=r['id'],
                    user_id=r['user_id'],
                    run_name=r['run_name'],
                    num_doctors=r['num_doctors'],
                    num_nurses=r['num_nurses'],
                    arrival_rate=r['arrival_rate'],
                    peak_multiplier=r['peak_multiplier'],
                    peak_start_min=r['peak_start_min'],
                    peak_duration_min=r['peak_duration_min'],
                    simulation_duration=r['simulation_duration'],
                    warmup_period=r['warmup_period'],
                    num_replications=r['num_replications'],
                    random_seed=r['random_seed'],
                    triage_distribution=triage_distribution,
                    treatment_times=treatment_times,
                    results_json=results_json,
                    created_at=r['created_at']
                )
                runs.append(run)
                
            conn.close()
            return runs
        except Exception as e:
            print(f"Eroare în SimulationRunRepository.get_by_user_id: {e}")
            return []

    def delete(self, run_id: int, user_id: int) -> bool:
        """Șterge o rulare de simulare din baza de date."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM simulation_runs WHERE id = ? AND user_id = ?", (run_id, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în SimulationRunRepository.delete: {e}")
            return False

    def rename(self, run_id: int, user_id: int, new_name: str) -> bool:
        """Redenumește o rulare de simulare în baza de date."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE simulation_runs SET run_name = ? WHERE id = ? AND user_id = ?", (new_name, run_id, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în SimulationRunRepository.rename: {e}")
            return False
