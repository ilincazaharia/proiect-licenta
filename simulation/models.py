"""
Modele de date pentru simularea UPU.
"""
from dataclasses import dataclass, field
from enum import IntEnum


class TriageLevel(IntEnum):
    # Prioritatea cea mai mică = cea mai urgenta
    RED = 1
    YELLOW = 2
    GREEN = 3
    BLUE = 4
    WHITE = 5

    @property
    def color_name(self):
        names = {1: "Rosu", 2: "Galben", 3: "Verde", 4: "Albastru", 5: "Alb"}
        return names[self.value]

    @property
    def target_time(self):
        """Timp tinta de tratament in minute."""
        targets = {1: 0, 2: 15, 3: 60, 4: 120, 5: 180}
        return targets[self.value]


@dataclass
class Patient:
    """Reprezinta un pacient in simulare."""
    id: int
    triage_level: TriageLevel
    arrival_time: float = 0.0
    treatment_duration: float = 0.0       # cat dureaza tratamentul (generat)

    # Timestamps completate pe parcursul simularii
    triage_start_time: float = -1.0
    triage_end_time: float = -1.0
    treatment_start_time: float = -1.0
    treatment_end_time: float = -1.0

    @property
    def waiting_time(self):
        """Timp de asteptare de la sosire pana la preluarea de către doctor."""
        if self.treatment_start_time < 0:
            return None
        return self.treatment_start_time - self.arrival_time

    @property
    def total_time_in_system(self):
        """Timpul total petrecut in sistem."""
        if self.treatment_end_time < 0:
            return None
        return self.treatment_end_time - self.arrival_time

    @property
    def met_target(self):
        """Returneaza T/F daca a fost tratat in timpul tinta"""
        wt = self.waiting_time
        if wt is None:
            return False
        return wt <= self.triage_level.target_time
