import unittest
from unittest.mock import MagicMock, patch
import io
import pandas as pd
from services.auth_service import AuthService
from services.doctor_service import DoctorService
from services.patient_service import PatientService
from services.referral_service import ReferralService
from services.simulation_service import SimulationService
from domain.models import User, PatientEntity, Referral, SimulationRun
from experiments.config import SimulationConfig


class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = MagicMock()
        self.auth_service = AuthService(user_repository=self.mock_user_repo)

    def test_is_valid_email(self):
        self.assertTrue(self.auth_service.is_valid_email("test@spital.ro"))
        self.assertTrue(self.auth_service.is_valid_email("ana.popescu@gmail.com"))
        self.assertFalse(self.auth_service.is_valid_email("invalid-email"))
        self.assertFalse(self.auth_service.is_valid_email("invalid@spital"))

    def test_hash_password(self):
        salt = "salt123"
        pwd = "myPassword"
        h1 = self.auth_service.hash_password(pwd, salt)
        h2 = self.auth_service.hash_password(pwd, salt)
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, pwd)

    def test_generate_salt(self):
        s1 = self.auth_service.generate_salt()
        s2 = self.auth_service.generate_salt()
        self.assertNotEqual(s1, s2)
        self.assertEqual(len(s1), 32) # hex of 16 bytes is 32 chars

    def test_register_user_validation_failures(self):
        # Empty names
        success, msg = self.auth_service.register_user("  ", "Ion", "ion@test.ro", "123456")
        self.assertFalse(success)
        self.assertEqual(msg, "Numele și prenumele sunt obligatorii.")

        # Invalid email
        success, msg = self.auth_service.register_user("Popescu", "Ion", "ion_test", "123456")
        self.assertFalse(success)
        self.assertEqual(msg, "Formatul adresei de e-mail nu este valid.")

        # Password too short
        success, msg = self.auth_service.register_user("Popescu", "Ion", "ion@test.ro", "1234")
        self.assertFalse(success)
        self.assertEqual(msg, "Parola trebuie să aibă cel puțin 6 caractere.")

    def test_register_user_already_exists(self):
        self.mock_user_repo.get_by_email.return_value = User(1, "Popescu", "Ion", "ion@test.ro")
        success, msg = self.auth_service.register_user("Popescu", "Ion", "ion@test.ro", "123456")
        self.assertFalse(success)
        self.assertEqual(msg, "Această adresă de e-mail este deja înregistrată.")

    def test_register_user_success(self):
        self.mock_user_repo.get_by_email.return_value = None
        self.mock_user_repo.create.return_value = True

        success, msg = self.auth_service.register_user("Popescu", "Ion", "ion@test.ro", "123456", "manager")
        self.assertTrue(success)
        self.assertEqual(msg, "Înregistrarea a fost efectuată cu succes.")
        self.mock_user_repo.create.assert_called_once()

    def test_verify_user_fail_email(self):
        self.mock_user_repo.get_password_info_by_email.return_value = None
        success, user = self.auth_service.verify_user("nonexistent@spital.ro", "pwd")
        self.assertFalse(success)
        self.assertIsNone(user)

    def test_verify_user_fail_password(self):
        salt = "salt"
        correct_hash = self.auth_service.hash_password("correct_password", salt)
        self.mock_user_repo.get_password_info_by_email.return_value = (correct_hash, salt)

        success, user = self.auth_service.verify_user("test@spital.ro", "wrong_password")
        self.assertFalse(success)
        self.assertIsNone(user)

    def test_verify_user_success(self):
        salt = "salt"
        correct_hash = self.auth_service.hash_password("correct_password", salt)
        expected_user = User(5, "Popescu", "Ion", "test@spital.ro")
        
        self.mock_user_repo.get_password_info_by_email.return_value = (correct_hash, salt)
        self.mock_user_repo.get_by_email.return_value = expected_user

        success, user = self.auth_service.verify_user("test@spital.ro", "correct_password")
        self.assertTrue(success)
        self.assertEqual(user, expected_user)


class TestDoctorService(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = MagicMock()
        self.mock_auth_service = MagicMock()
        self.doctor_service = DoctorService(
            user_repository=self.mock_user_repo,
            auth_service=self.mock_auth_service
        )

    def test_get_all_specialties(self):
        specs = self.doctor_service.get_all_specialties()
        self.assertIn("Urgențe", specs)
        self.assertIn("Cardiologie", specs)

    def test_get_all_doctors(self):
        expected_docs = [User(1, "A", "B", "email", "medic_urgente")]
        self.mock_user_repo.get_all_doctors.return_value = expected_docs
        self.assertEqual(self.doctor_service.get_all_doctors(), expected_docs)

    def test_delete_doctor(self):
        self.mock_user_repo.delete_doctor.return_value = True
        success, msg = self.doctor_service.delete_doctor(1)
        self.assertTrue(success)
        self.assertEqual(msg, "Contul de medic a fost șters cu succes.")

        self.mock_user_repo.delete_doctor.return_value = False
        success, msg = self.doctor_service.delete_doctor(1)
        self.assertFalse(success)
        self.assertEqual(msg, "Eroare la ștergerea contului de medic.")

    def test_register_doctor_invalid_specialty(self):
        self.mock_user_repo.get_specialty_id_by_name.return_value = None
        success, msg = self.doctor_service.register_doctor("Popa", "Dan", "dan.popa@spital.ro", "123456", "Astrologie")
        self.assertFalse(success)
        self.assertEqual(msg, "Specializarea aleasă este invalidă.")

    def test_register_doctor_urgente(self):
        self.mock_user_repo.get_specialty_id_by_name.return_value = 1
        self.mock_auth_service.register_user.return_value = (True, "Succes")
        
        success, msg = self.doctor_service.register_doctor("Popa", "Dan", "dan.popa@spital.ro", "123456", "Urgențe")
        self.assertTrue(success)
        self.mock_auth_service.register_user.assert_called_with(
            last_name="Popa", first_name="Dan", email="dan.popa@spital.ro", password="123456",
            role="medic_urgente", specialty_id=1
        )

    def test_register_doctor_sectie(self):
        self.mock_user_repo.get_specialty_id_by_name.return_value = 2
        self.mock_auth_service.register_user.return_value = (True, "Succes")
        
        success, msg = self.doctor_service.register_doctor("Popescu", "Maria", "maria.popescu@spital.ro", "654321", "Cardiologie")
        self.assertTrue(success)
        self.mock_auth_service.register_user.assert_called_with(
            last_name="Popescu", first_name="Maria", email="maria.popescu@spital.ro", password="654321",
            role="medic_sectie", specialty_id=2
        )


class TestPatientService(unittest.TestCase):
    def setUp(self):
        self.mock_patient_repo = MagicMock()
        self.patient_service = PatientService(patient_repository=self.mock_patient_repo)

    def test_get_patient_by_cnp(self):
        self.patient_service.get_patient_by_cnp("   ")
        self.mock_patient_repo.get_by_cnp.assert_not_called()

        expected_patient = PatientEntity(1, "1234567890123", "N", "P")
        self.mock_patient_repo.get_by_cnp.return_value = expected_patient
        result = self.patient_service.get_patient_by_cnp("1234567890123")
        self.assertEqual(result, expected_patient)

    def test_register_patient_validation_failures(self):
        # Empty field
        success, patient, msg = self.patient_service.register_patient("", "Pop", "Dan")
        self.assertFalse(success)
        self.assertEqual(msg, "Toate câmpurile (CNP, Nume, Prenume) sunt obligatorii.")

        # CNP not 13 chars
        success, patient, msg = self.patient_service.register_patient("123", "Pop", "Dan")
        self.assertFalse(success)
        self.assertEqual(msg, "CNP-ul trebuie să fie format din exact 13 cifre.")

        # CNP not digits
        success, patient, msg = self.patient_service.register_patient("abc1234567890", "Pop", "Dan")
        self.assertFalse(success)
        self.assertEqual(msg, "CNP-ul trebuie să fie format din exact 13 cifre.")

    def test_register_patient_already_exists(self):
        existing_patient = PatientEntity(2, "1234567890123", "Popescu", "Vasile")
        self.mock_patient_repo.get_by_cnp.return_value = existing_patient
        
        success, patient, msg = self.patient_service.register_patient("1234567890123", "Popescu", "Vasile")
        self.assertTrue(success)
        self.assertEqual(patient, existing_patient)
        self.assertEqual(msg, "Pacientul există deja în baza de date.")

    def test_register_patient_success(self):
        self.mock_patient_repo.get_by_cnp.side_effect = [None, PatientEntity(3, "1234567890123", "Pop", "Dan")]
        self.mock_patient_repo.create.return_value = True

        success, patient, msg = self.patient_service.register_patient("1234567890123", "Pop", "Dan")
        self.assertTrue(success)
        self.assertEqual(patient.id, 3)
        self.assertEqual(msg, "Pacientul a fost înregistrat cu succes.")
        self.mock_patient_repo.add_log.assert_called_once()


class TestReferralService(unittest.TestCase):
    def setUp(self):
        self.mock_referral_repo = MagicMock()
        self.mock_patient_repo = MagicMock()
        self.referral_service = ReferralService(
            referral_repository=self.mock_referral_repo,
            patient_repository=self.mock_patient_repo
        )
        self.mock_user_repo = MagicMock()
        self.referral_service.user_repo = self.mock_user_repo

    def test_create_referral_failures(self):
        # Invalid patient_id
        success, msg = self.referral_service.create_referral(0, "Cod Verde", "Cardiologie", 1)
        self.assertFalse(success)
        self.assertEqual(msg, "ID-ul pacientului este invalid.")

        # Invalid triage level
        success, msg = self.referral_service.create_referral(1, "Cod Portocaliu", "Cardiologie", 1)
        self.assertFalse(success)
        self.assertEqual(msg, "Nivelul de triaj este invalid.")

        # Destination section "Urgențe" or empty
        success, msg = self.referral_service.create_referral(1, "Cod Verde", "Urgențe", 1)
        self.assertFalse(success)
        self.assertEqual(msg, "Secția de destinație este invalidă.")

        # Invalid sender
        success, msg = self.referral_service.create_referral(1, "Cod Verde", "Cardiologie", 0)
        self.assertFalse(success)
        self.assertEqual(msg, "ID-ul medicului trimițător este invalid.")

    def test_create_referral_specialty_not_found(self):
        self.mock_user_repo.get_specialty_id_by_name.return_value = None
        success, msg = self.referral_service.create_referral(1, "Cod Verde", "Cardiologie", 1)
        self.assertFalse(success)
        self.assertEqual(msg, "Secția de destinație este invalidă.")

    def test_create_referral_success(self):
        self.mock_user_repo.get_specialty_id_by_name.return_value = 2
        self.mock_referral_repo.create.return_value = True

        success, msg = self.referral_service.create_referral(5, "Cod Roșu", "Cardiologie", 10, "Simptome infarct")
        self.assertTrue(success)
        self.assertEqual(msg, "Trimiterea a fost înregistrată cu succes în stare de așteptare.")
        self.mock_referral_repo.create.assert_called_once()
        self.mock_patient_repo.add_log.assert_called_once()

    def test_respond_to_referral_not_found(self):
        self.mock_referral_repo.get_by_id.return_value = None
        success, msg = self.referral_service.respond_to_referral(1, 10, True, "Note")
        self.assertFalse(success)
        self.assertEqual(msg, "Trimiterea specificată nu a fost găsită.")

    def test_respond_to_referral_accept(self):
        ref = Referral(1, 5, "Cod Verde", 2, 10, None, "in_asteptare", "Obs")
        ref.specialty_name = "Cardiologie"
        self.mock_referral_repo.get_by_id.return_value = ref
        self.mock_referral_repo.update_status.return_value = True

        success, msg = self.referral_service.respond_to_referral(1, 15, True, "Salon 3")
        self.assertTrue(success)
        self.mock_referral_repo.update_status.assert_called_with(
            referral_id=1, receiver_id=15, status="acceptat", response_notes="Salon 3"
        )
        self.mock_patient_repo.add_log.assert_called_with(
            patient_id=5, event_type="internat", details="Internat pe sectia Cardiologie. Note: Salon 3"
        )

    def test_respond_to_referral_refuse(self):
        ref = Referral(1, 5, "Cod Verde", 2, 10, None, "in_asteptare", "Obs")
        ref.specialty_name = "Cardiologie"
        self.mock_referral_repo.get_by_id.return_value = ref
        self.mock_referral_repo.update_status.return_value = True

        success, msg = self.referral_service.respond_to_referral(1, 15, False, "Nu avem locuri")
        self.assertTrue(success)
        self.mock_referral_repo.update_status.assert_called_with(
            referral_id=1, receiver_id=15, status="refuzat", response_notes="Nu avem locuri"
        )
        self.mock_patient_repo.add_log.assert_called_with(
            patient_id=5, event_type="refuzat", details="Trimitere refuzata de sectia Cardiologie. Note: Nu avem locuri"
        )

    def test_discharge_patient_not_found(self):
        self.mock_referral_repo.get_by_id.return_value = None
        success, msg = self.referral_service.discharge_patient(1, 5, "Note")
        self.assertFalse(success)
        self.assertEqual(msg, "Trimiterea specificată nu a fost găsită.")

    def test_discharge_patient_success(self):
        ref = Referral(1, 5, "Cod Verde", 2, 10, 15, "acceptat", "Obs")
        ref.specialty_name = "Cardiologie"
        self.mock_referral_repo.get_by_id.return_value = ref
        self.mock_referral_repo.update_status.return_value = True

        success, msg = self.referral_service.discharge_patient(1, 5, "Stare buna")
        self.assertTrue(success)
        self.mock_referral_repo.update_status.assert_called_with(
            referral_id=1, receiver_id=15, status="externat", response_notes="Stare buna"
        )
        self.mock_patient_repo.add_log.assert_called_with(
            patient_id=5, event_type="externat", details="Externat de pe sectia Cardiologie. Note externare: Stare buna"
        )


class TestSimulationService(unittest.TestCase):
    def setUp(self):
        self.mock_sim_repo = MagicMock()
        self.sim_service = SimulationService(simulation_repository=self.mock_sim_repo)

    def test_get_user_history(self):
        expected_runs = [SimulationRun(1, 10, "Run 1", 3, 2, 12.0, 1.5, 0, 0, 480.0, 60.0, 10, 42, {}, {}, [])]
        self.mock_sim_repo.get_by_user_id.return_value = expected_runs
        self.assertEqual(self.sim_service.get_user_history(10), expected_runs)

    def test_delete_run(self):
        self.mock_sim_repo.delete.return_value = True
        success, msg = self.sim_service.delete_run(1, 10)
        self.assertTrue(success)
        self.assertEqual(msg, "Simularea a fost ștearsă din istoric.")

    def test_rename_run_empty(self):
        success, msg = self.sim_service.rename_run(1, 10, "   ")
        self.assertFalse(success)
        self.assertEqual(msg, "Numele simulării nu poate fi gol.")

    def test_rename_run_success(self):
        self.mock_sim_repo.rename.return_value = True
        success, msg = self.sim_service.rename_run(1, 10, "Nou Nume")
        self.assertTrue(success)
        self.assertEqual(msg, "Simularea a fost redenumită cu succes.")

    def test_save_simulation(self):
        self.mock_sim_repo.save.return_value = True
        config = SimulationConfig()
        success, msg = self.sim_service.save_simulation(10, "Sim Test", config, [])
        self.assertTrue(success)
        self.mock_sim_repo.save.assert_called_once()

    def test_export_detailed_csv(self):
        results = [
            {"strategy": "Priority + FIFO", "avg_waiting_time": 10.5, "avg_los": 45.2, "total_patients": 80, "target_compliance": 85.0},
            {"strategy": "FIFO", "avg_waiting_time": 15.2, "avg_los": 55.2, "total_patients": 81, "target_compliance": 75.0}
        ]
        csv_bytes = self.sim_service.export_detailed_csv(results)
        df_out = pd.read_csv(io.StringIO(csv_bytes.decode('utf-8')))
        self.assertEqual(len(df_out), 1)
        self.assertNotIn("strategy", df_out.columns)
        self.assertEqual(df_out["avg_waiting_time"].iloc[0], 10.5)

    def test_export_summary_csv(self):
        results = [
            {"strategy": "Priority + FIFO", "avg_waiting_time": 10.0, "avg_los": 40.0, "total_patients": 80, "target_compliance": 85.0},
            {"strategy": "Priority + FIFO", "avg_waiting_time": 12.0, "avg_los": 42.0, "total_patients": 82, "target_compliance": 87.0}
        ]
        csv_bytes = self.sim_service.export_summary_csv(results)
        df_out = pd.read_csv(io.StringIO(csv_bytes.decode('utf-8')))
        self.assertEqual(len(df_out), 1)
        self.assertEqual(df_out["avg_waiting_time_mean"].iloc[0], 11.0)
        self.assertIn("avg_waiting_time_ci_low", df_out.columns)


if __name__ == "__main__":
    unittest.main()
