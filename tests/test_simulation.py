import unittest
import numpy as np
import simpy
from simulation.models import TriageLevel, Patient
from simulation.metrics import compute_metrics, _empty_metrics
from simulation.engine import EmergencyDepartment
from experiments.config import SimulationConfig
from simulation.strategies import FIFOStrategy


class TestSimulationModels(unittest.TestCase):
    def test_triage_level_properties(self):
        # Test Red
        self.assertEqual(TriageLevel.RED.color_name, "Rosu")
        self.assertEqual(TriageLevel.RED.target_time, 0)

        # Test Yellow
        self.assertEqual(TriageLevel.YELLOW.color_name, "Galben")
        self.assertEqual(TriageLevel.YELLOW.target_time, 15)

        # Test Green
        self.assertEqual(TriageLevel.GREEN.color_name, "Verde")
        self.assertEqual(TriageLevel.GREEN.target_time, 60)

        # Test Blue
        self.assertEqual(TriageLevel.BLUE.color_name, "Albastru")
        self.assertEqual(TriageLevel.BLUE.target_time, 120)

        # Test White
        self.assertEqual(TriageLevel.WHITE.color_name, "Alb")
        self.assertEqual(TriageLevel.WHITE.target_time, 180)

    def test_patient_properties(self):
        # Case 1: patient has not started treatment
        p1 = Patient(id=1, triage_level=TriageLevel.YELLOW, arrival_time=10.0, treatment_duration=30.0)
        self.assertIsNone(p1.waiting_time)
        self.assertIsNone(p1.total_time_in_system)
        self.assertFalse(p1.met_target)

        # Case 2: patient started treatment but not finished
        p1.treatment_start_time = 20.0
        self.assertEqual(p1.waiting_time, 10.0)
        self.assertIsNone(p1.total_time_in_system)
        # 10.0 waiting time <= 15.0 target time for YELLOW
        self.assertTrue(p1.met_target)

        # Case 3: patient finished treatment
        p1.treatment_end_time = 50.0
        self.assertEqual(p1.total_time_in_system, 40.0)

        # Case 4: did not meet target (e.g. waiting time = 20.0, target = 15.0)
        p2 = Patient(id=2, triage_level=TriageLevel.YELLOW, arrival_time=10.0, treatment_duration=30.0)
        p2.treatment_start_time = 35.0
        self.assertEqual(p2.waiting_time, 25.0)
        self.assertFalse(p2.met_target)


class TestSimulationMetrics(unittest.TestCase):
    def test_empty_metrics(self):
        m = compute_metrics([])
        self.assertEqual(m["total_patients"], 0)
        self.assertEqual(m["avg_waiting_time"], 0)
        self.assertEqual(m["level_1_count"], 0)
        self.assertEqual(m["level_2_target_compliance"], 0)

    def test_compute_metrics_calculation(self):
        # Create a list of test patients
        # Patient 1: YELLOW, arrived 0, started 10, ended 40 (wait=10, los=40, target met)
        p1 = Patient(id=1, triage_level=TriageLevel.YELLOW, arrival_time=0.0)
        p1.treatment_start_time = 10.0
        p1.treatment_end_time = 40.0

        # Patient 2: RED, arrived 5, started 15, ended 30 (wait=10, los=25, target NOT met since target is 0)
        p2 = Patient(id=2, triage_level=TriageLevel.RED, arrival_time=5.0)
        p2.treatment_start_time = 15.0
        p2.treatment_end_time = 30.0

        patients = [p1, p2]
        metrics = compute_metrics(patients)

        self.assertEqual(metrics["total_patients"], 2)
        # waiting times: 10, 10 -> avg = 10
        self.assertEqual(metrics["avg_waiting_time"], 10.0)
        # los: 40, 25 -> avg = 32.5
        self.assertEqual(metrics["avg_los"], 32.5)
        # target compliance: 1 met (p1), 1 not met (p2) -> 50%
        self.assertEqual(metrics["target_compliance"], 50.0)

        # level counts
        self.assertEqual(metrics["level_1_count"], 1)
        self.assertEqual(metrics["level_2_count"], 1)
        self.assertEqual(metrics["level_3_count"], 0)

        # level target compliance
        self.assertEqual(metrics["level_1_target_compliance"], 0.0)
        self.assertEqual(metrics["level_2_target_compliance"], 100.0)


class TestEmergencyDepartmentEngine(unittest.TestCase):
    def test_department_short_run(self):
        # A minimal simulation run test to verify integration and SimPy environment logic
        env = simpy.Environment()
        rng = np.random.default_rng(42)
        
        config = SimulationConfig(
            num_doctors=1,
            num_nurses=1,
            arrival_rate=5.0,
            simulation_duration=60.0, # 1 hour
            warmup_period=10.0,
            peak_multiplier=1.0,
            peak_start_min=0.0,
            peak_duration_min=0.0
        )
        strategy = FIFOStrategy()
        
        dept = EmergencyDepartment(env, config, strategy, rng)
        dept.run()
        
        # Verify that simulation has processed arrivals and ran successfully
        self.assertGreater(dept.patient_counter, 0)
        self.assertGreaterEqual(env.now, 60.0)
        
        results = dept.get_results()
        # Results should only contain patients with arrival_time >= warmup_period (10.0)
        for p in results:
            self.assertGreaterEqual(p.arrival_time, 10.0)


if __name__ == "__main__":
    unittest.main()
