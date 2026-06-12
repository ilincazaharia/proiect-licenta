from dataclasses import dataclass
from typing import Optional, Dict, List, Any

@dataclass
class User:
    id: Optional[int]
    last_name: str
    first_name: str
    email: str
    role: str = "manager"
    specialty_id: Optional[int] = None
    specialty_name: Optional[str] = None

@dataclass
class PatientEntity:
    id: Optional[int]
    cnp: str
    last_name: str
    first_name: str

@dataclass
class Referral:
    id: Optional[int]
    patient_id: int
    triage_level: str
    specialty_id: int
    sender_id: int
    receiver_id: Optional[int] = None
    status: str = "in_asteptare"
    observations: Optional[str] = None
    response_notes: Optional[str] = None
    
    # Helper fields for joined views in UI
    patient_name: Optional[str] = None
    patient_cnp: Optional[str] = None
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    specialty_name: Optional[str] = None

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
