import unittest
from domain.models import User, PatientEntity, Referral, SimulationRun


class TestDomainModels(unittest.TestCase):
    def test_user_creation_and_defaults(self):
        # Test construct user with default role
        user = User(
            id=1,
            last_name="Popescu",
            first_name="Ion",
            email="ion.popescu@spital.ro"
        )
        self.assertEqual(user.id, 1)
        self.assertEqual(user.last_name, "Popescu")
        self.assertEqual(user.first_name, "Ion")
        self.assertEqual(user.email, "ion.popescu@spital.ro")
        self.assertEqual(user.role, "manager")
        self.assertIsNone(user.specialty_id)
        self.assertIsNone(user.specialty_name)

    def test_user_with_specialty(self):
        # Test construct user with non-default role and specialty
        user = User(
            id=2,
            last_name="Ionescu",
            first_name="Ana",
            email="ana.ionescu@spital.ro",
            role="medic_sectie",
            specialty_id=3,
            specialty_name="Cardiologie"
        )
        self.assertEqual(user.role, "medic_sectie")
        self.assertEqual(user.specialty_id, 3)
        self.assertEqual(user.specialty_name, "Cardiologie")

    def test_patient_entity_creation(self):
        patient = PatientEntity(
            id=10,
            cnp="1234567890123",
            last_name="Vasilescu",
            first_name="Vasile"
        )
        self.assertEqual(patient.id, 10)
        self.assertEqual(patient.cnp, "1234567890123")
        self.assertEqual(patient.last_name, "Vasilescu")
        self.assertEqual(patient.first_name, "Vasile")

    def test_referral_creation_and_defaults(self):
        referral = Referral(
            id=100,
            patient_id=10,
            triage_level="Cod Roșu",
            specialty_id=2,
            sender_id=1
        )
        self.assertEqual(referral.id, 100)
        self.assertEqual(referral.patient_id, 10)
        self.assertEqual(referral.triage_level, "Cod Roșu")
        self.assertEqual(referral.specialty_id, 2)
        self.assertEqual(referral.sender_id, 1)
        self.assertIsNone(referral.receiver_id)
        self.assertEqual(referral.status, "in_asteptare")
        self.assertIsNone(referral.observations)
        self.assertIsNone(referral.response_notes)
        self.assertIsNone(referral.patient_name)
        self.assertIsNone(referral.patient_cnp)

    def test_simulation_run_creation(self):
        run = SimulationRun(
            id=5,
            user_id=1,
            run_name="Simulare Test",
            num_doctors=3,
            num_nurses=2,
            arrival_rate=10.0,
            peak_multiplier=1.5,
            peak_start_min=60.0,
            peak_duration_min=120.0,
            simulation_duration=480.0,
            warmup_period=60.0,
            num_replications=10,
            random_seed=123,
            triage_distribution={1: 0.1, 2: 0.9},
            treatment_times={1: (30, 5), 2: (20, 4)},
            results_json=[{"strategy": "FIFO", "avg_waiting_time": 12.5}]
        )
        self.assertEqual(run.id, 5)
        self.assertEqual(run.user_id, 1)
        self.assertEqual(run.run_name, "Simulare Test")
        self.assertEqual(run.num_doctors, 3)
        self.assertEqual(run.num_nurses, 2)
        self.assertEqual(run.arrival_rate, 10.0)
        self.assertEqual(run.triage_distribution[1], 0.1)
        self.assertEqual(run.treatment_times[2], (20, 4))
        self.assertEqual(run.results_json[0]["strategy"], "FIFO")


if __name__ == "__main__":
    unittest.main()
