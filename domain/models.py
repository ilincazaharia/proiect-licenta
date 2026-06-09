from dataclasses import dataclass
from typing import Optional, Dict, List, Any

@dataclass
class Specialty:
    id: int
    name: str

@dataclass
class User:
    id: Optional[int]
    nume: str
    prenume: str
    email: str
    role: str = "manager"
    specialty_id: Optional[int] = None
    specialty_name: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class SimulationRun:
    id: Optional[int]
    user_id: int
    run_name: str
    num_doctors: int
    num_nurses: int
    arrival_rate: float
    peak_multiplier: float
    peak_start_min: float
    peak_duration_min: float
    simulation_duration: float
    warmup_period: float
    num_replications: int
    random_seed: int
    triage_distribution: Dict[int, float]
    treatment_times: Dict[int, Any]
    results_json: List[Dict[str, Any]]
    created_at: Optional[str] = None
