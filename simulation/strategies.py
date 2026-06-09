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

# Lista tuturor strategiilor disponibile
ALL_STRATEGIES = [
    FIFOStrategy(),
    StrictPriorityStrategy(),
    PriorityFIFOStrategy()
]
