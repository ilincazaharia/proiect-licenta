"""
Motor de simulare DES pentru UPU, bazat pe SimPy.
"""
import simpy
import numpy as np
from simulation.models import Patient, TriageLevel
from simulation.strategies import QueueStrategy


class EmergencyDepartment:
    """
    Simuleaza o Unitate de Primiri Urgente (UPU).

    Fluxul pacientului:
        Sosire -> Triaj (asistenta) -> Coada de asteptare -> Tratament (medic) -> Iesire
    """

    def __init__(self, env: simpy.Environment, config, strategy: QueueStrategy, rng: np.random.Generator):
        self.env = env
        self.config = config
        self.strategy = strategy
        self.rng = rng

        # Resurse SimPy
        self.nurses = simpy.Resource(env, capacity=config.num_nurses)
        self.doctors = simpy.PriorityResource(env, capacity=config.num_doctors)

        # Rezultate
        self.patients_treated = []
        self.patients_in_system = []
        self.patient_counter = 0

    def run(self):
        """Porneste simularea."""
        self.env.process(self._generate_arrivals())
        self.env.run(until=self.config.simulation_duration)

    def _generate_arrivals(self):
        """Genereaza sosiri de pacienti (proces Poisson)."""
        # Interval mediu intre sosiri (in minute)
        mean_interarrival = 60.0 / self.config.arrival_rate

        while True:
            # Timp pana la urmatoarea sosire (distributie exponentiala)
            interarrival_time = self.rng.exponential(mean_interarrival)
            yield self.env.timeout(interarrival_time)

            # Creaza pacientul
            self.patient_counter += 1
            patient = self._create_patient()
            self.patients_in_system.append(patient)

            # Porneste procesul pacientului
            self.env.process(self._patient_process(patient))

    def _create_patient(self) -> Patient:
        """Creaza un pacient cu nivel de triaj si timp de tratament aleator."""
        # Alege nivelul de triaj conform distributiei
        levels = list(self.config.triage_distribution.keys())
        probs = list(self.config.triage_distribution.values())
        level_value = self.rng.choice(levels, p=probs)
        triage_level = TriageLevel(level_value)

        # Genereaza timpul de tratament (distributie normala, minim 5 min)
        mean, std = self.config.treatment_times[level_value]
        treatment_duration = max(5.0, self.rng.normal(mean, std))

        return Patient(
            id=self.patient_counter,
            triage_level=triage_level,
            arrival_time=self.env.now,
            treatment_duration=treatment_duration,
        )

    def _patient_process(self, patient: Patient):
        """Procesul complet al unui pacient in UPU."""

        # 1. Triaj (la asistenta)
        with self.nurses.request() as req:
            yield req
            patient.triage_start_time = self.env.now

            # Triajul dureaza 3-7 minute
            triage_duration = self.rng.uniform(3, 7)
            yield self.env.timeout(triage_duration)
            patient.triage_end_time = self.env.now

        # 2. Asteptare + Tratament (la medic, cu prioritate)
        priority = self.strategy.get_priority(patient, self.env.now)
        with self.doctors.request(priority=priority) as req:
            yield req
            patient.treatment_start_time = self.env.now

            # Tratament
            yield self.env.timeout(patient.treatment_duration)
            patient.treatment_end_time = self.env.now

        # Pacientul a terminat
        self.patients_treated.append(patient)

    def get_results(self):
        """Returneaza doar pacientii tratati dupa perioada de warmup."""
        warmup = self.config.warmup_period
        return [p for p in self.patients_treated if p.arrival_time >= warmup]
