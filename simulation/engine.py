"""
Motor de simulare DES pentru UPU, bazat pe SimPy.
"""
import simpy
import numpy as np
from simulation.models import Patient, TriageLevel
from simulation.strategies import QueueStrategy


class EmergencyDepartment:
    """
    Simuleaza o Unitate de Primiri Urgente.

    Fluxul pacientului:
        Sosire -> Triaj (asistenta) -> Coada de asteptare -> Tratament (medic) -> Iesire
    """

    def __init__(self, env: simpy.Environment, config, strategy: QueueStrategy, rng: np.random.Generator):
        self.env = env
        self.config = config
        self.strategy = strategy
        self.rng = rng

        # Resurse SimPy
        self.nurses = simpy.PriorityResource(env, capacity=config.num_nurses)
        self.doctors = simpy.PriorityResource(env, capacity=config.num_doctors)

        # Rezultate
        self.patients_treated = []
        self.patients_in_system = []
        self.patient_counter = 0
        self.congestion_logs = []

    def run(self):
        self.env.process(self._generate_arrivals())
        self.env.process(self._monitor_congestion())
        self.env.run()

    def _monitor_congestion(self):
        # Salveaza periodic informatii despre lungimea cozilor 
        while self.env.now <= self.config.simulation_duration:
            self.congestion_logs.append({
                "time": self.env.now,
                "doctors_queue": len(self.doctors.queue),
                "nurses_queue": len(self.nurses.queue)
            })
            yield self.env.timeout(5.0)

    def _generate_arrivals(self):
        while self.env.now < self.config.simulation_duration:
            # Calcul rata curenta in functie de orele de varf
            current_rate = self.config.arrival_rate
            if self.config.peak_start_min <= self.env.now <= (self.config.peak_start_min + self.config.peak_duration_min):
                current_rate *= self.config.peak_multiplier

            # Interval mediu intre sosiri
            mean_interarrival = 60.0 / current_rate
            
            # Timp pana la urmatoarea sosire
            interarrival_time = self.rng.exponential(mean_interarrival)
            
            if self.env.now + interarrival_time >= self.config.simulation_duration:
                break
                
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
        if patient.triage_level == TriageLevel.RED:
            # Codul Rosu are prioritate maxima (priority=0)
            with self.nurses.request(priority=(0, patient.arrival_time)) as req:
                yield req
                patient.triage_start_time = self.env.now
                patient.triage_end_time = self.env.now
        else:
            # Codurile celelalte au prioritate mai mica (priority=1)
            with self.nurses.request(priority=(1, patient.arrival_time)) as req:
                yield req
                patient.triage_start_time = self.env.now

                # Triajul dureaza 3-7 minute daca nu e Cod Rosu
                triage_duration = self.rng.uniform(3, 7)
                yield self.env.timeout(triage_duration)
                patient.triage_end_time = self.env.now

        # 2. Asteptare + Tratament (la medic)
        priority = self.strategy.get_priority(patient, self.env.now)
        with self.doctors.request(priority=priority) as req:
            yield req
            patient.treatment_start_time = self.env.now

            # Tratament
            yield self.env.timeout(patient.treatment_duration)
            patient.treatment_end_time = self.env.now

        # Iesire din sistem
        self.patients_treated.append(patient)

    def get_results(self):
        """Returneaza doar pacientii tratati dupa perioada de warmup."""
        warmup = self.config.warmup_period
        return [p for p in self.patients_treated if p.arrival_time >= warmup]
