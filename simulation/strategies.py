"""
Strategii de coada pentru simularea UPU.

Fiecare strategie determina prioritatea cu care un pacient
intra in coada de asteptare pentru tratament.
"""
from simulation.models import Patient


class QueueStrategy:
    """Clasa de baza pentru strategiile de coada."""
    name = "Base"

    def get_priority(self, patient: Patient, current_time: float) -> tuple:
        """
        Returneaza un tuplu de prioritate pentru SimPy PriorityResource.
        Valoare mai mica = prioritate mai mare.
        """
        raise NotImplementedError


class FIFOStrategy(QueueStrategy):
    """
    First-In-First-Out: pacientii sunt tratati in ordinea sosirii,
    fara nicio considerare a nivelului de triaj.
    """
    name = "FIFO"

    def get_priority(self, patient: Patient, current_time: float) -> tuple:
        # Toti au aceeasi prioritate (0), deci SimPy ii va servi in ordine FIFO
        return (0, patient.arrival_time)


class StrictPriorityStrategy(QueueStrategy):
    """
    Prioritate stricta pe nivelul de triaj.
    In cadrul aceluiasi nivel, ordine FIFO.
    """
    name = "Priority Strict"

    def get_priority(self, patient: Patient, current_time: float) -> tuple:
        return (patient.triage_level.value, patient.arrival_time)


class PriorityFIFOStrategy(QueueStrategy):
    """
    Prioritate pe triaj cu FIFO in cadrul aceluiasi nivel.
    Similar cu StrictPriority, dar explicit separat pentru claritate.
    In practica, acesta este modelul cel mai folosit in UPU-uri reale.
    """
    name = "Priority + FIFO"

    def get_priority(self, patient: Patient, current_time: float) -> tuple:
        return (patient.triage_level.value, patient.arrival_time)


class SJFStrategy(QueueStrategy):
    """
    Shortest Job First: pacientul cu cel mai scurt timp estimat
    de tratament este tratat primul.
    """
    name = "SJF (Shortest Job First)"

    def get_priority(self, patient: Patient, current_time: float) -> tuple:
        return (patient.treatment_duration, patient.arrival_time)


class WeightedRoundRobinStrategy(QueueStrategy):
    """
    Round Robin ponderat: se aloca prioritate pe baza nivelului de triaj
    dar cu o componenta de 'aging' — pacientii care asteapta mai mult
    isi cresc prioritatea, evitand starvation-ul.

    Formula: priority = triage_level - (wait_time / aging_factor)
    Astfel, un pacient cu nivel scazut care asteapta mult poate
    depasi un pacient cu nivel mai inalt sosit recent.
    """
    name = "Round Robin Ponderat"

    def __init__(self, aging_factor: float = 30.0):
        """
        Args:
            aging_factor: cate minute de asteptare echivaleaza cu
                         o reducere de 1 nivel in prioritate.
        """
        self.aging_factor = aging_factor

    def get_priority(self, patient: Patient, current_time: float) -> tuple:
        wait_time = current_time - patient.arrival_time
        adjusted_priority = patient.triage_level.value - (wait_time / self.aging_factor)
        return (adjusted_priority, patient.arrival_time)


# Lista tuturor strategiilor disponibile
ALL_STRATEGIES = [
    FIFOStrategy(),
    StrictPriorityStrategy(),
    PriorityFIFOStrategy(),
    SJFStrategy(),
    WeightedRoundRobinStrategy(),
]
