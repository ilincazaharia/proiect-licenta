"""
Configurari pentru simulare si experimente.
"""
from dataclasses import dataclass, field


@dataclass
class SimulationConfig:
    """Parametrii unei simulari UPU."""

    # Resurse
    num_doctors: int = 3
    num_nurses: int = 2

    # Rata de sosire
    arrival_rate: float = 12.0

    # Distributia nivelurilor de triaj
    triage_distribution: dict = field(default_factory=lambda: {
        1: 0.05,   # Rosu
        2: 0.15,   # Galben
        3: 0.30,   # Verde
        4: 0.35,   # Albastru
        5: 0.15,   # Alb
    })

    # Timpuri de tratament per nivel + dev standard
    treatment_times: dict = field(default_factory=lambda: {
        1: (45, 15),
        2: (30, 10),
        3: (20, 8),
        4: (15, 5),
        5: (10, 3),
    })

    # Ore de varf
    peak_multiplier: float = 2.0
    peak_start_min: float = 120.0
    peak_duration_min: float = 120.0

    # Durata simularii
    simulation_duration: float = 480.0
    warmup_period: float = 60.0

    # Replicari
    num_replications: int = 30
    random_seed: int = 42
