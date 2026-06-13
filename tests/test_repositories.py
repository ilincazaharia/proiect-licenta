import os
import unittest
from repositories.db_connection import DBConnection
from repositories.user_repository import UserRepository
from repositories.patient_repository import PatientRepository
from repositories.referral_repository import ReferralRepository
from repositories.simulation_repository import SimulationRunRepository
from domain.models import User, PatientEntity, Referral, SimulationRun


class TestRepositories(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Redirecționăm baza de date spre un fișier temporar de test
        cls.db_filename = "test_users_db.db"
        DBConnection.DB_PATH = cls.db_filename
        
        # Ne asigurăm că fișierul temporar nu există deja
        if os.path.exists(cls.db_filename):
            try:
                os.remove(cls.db_filename)
            except OSError:
                pass
                
        # Inițializăm structura tabelelor
        DBConnection.init_db()
        
        # Instanțiem repozitoriile
        cls.user_repo = UserRepository()
        cls.patient_repo = PatientRepository()
        cls.referral_repo = ReferralRepository()
        cls.sim_repo = SimulationRunRepository()

    @classmethod
    def tearDownClass(cls):
        # Ștergem baza de date temporară la final
        if os.path.exists(cls.db_filename):
            try:
                os.remove(cls.db_filename)
            except OSError:
                print(f"Nu s-a putut sterge fisierul temporar {cls.db_filename}")

    def setUp(self):
        # Putem curăța tabelele între teste pentru izolare, dar pentru simplitate
        # vom genera ID-uri și date unice pentru fiecare test.
        pass

    def test_specialties_seeding(self):
        # La init_db, specializările implicite ar trebui populate
        specs = self.user_repo.get_all_specialties()
        self.assertGreater(len(specs), 0)
        
        # Căutăm o specializare cunoscută, ex: "Urgențe"
        urgente_id = self.user_repo.get_specialty_id_by_name("Urgențe")
        self.assertIsNotNone(urgente_id)

    def test_user_repository_crud(self):
        email = "doctor.test@spital.ro"
        user = User(
            id=None,
            last_name="Popa",
            first_name="Vasile",
            email=email,
            role="medic_sectie",
            specialty_id=self.user_repo.get_specialty_id_by_name("Cardiologie")
        )
        
        # Test create user
        success = self.user_repo.create(user, "hash123", "salt123")
        self.assertTrue(success)
        
        # Test get_by_email
        saved_user = self.user_repo.get_by_email(email)
        self.assertIsNotNone(saved_user)
        self.assertEqual(saved_user.last_name, "Popa")
        self.assertEqual(saved_user.first_name, "Vasile")
        self.assertEqual(saved_user.role, "medic_sectie")
        self.assertEqual(saved_user.specialty_name, "Cardiologie")
        
        # Test get_password_info_by_email
        pwd_info = self.user_repo.get_password_info_by_email(email)
        self.assertEqual(pwd_info, ("hash123", "salt123"))
        
        # Test get_by_id
        saved_user_by_id = self.user_repo.get_by_id(saved_user.id)
        self.assertEqual(saved_user_by_id.email, email)

        # Test get_all_doctors
        doctors = self.user_repo.get_all_doctors()
        self.assertTrue(any(d.email == email for d in doctors))

        # Test delete doctor
        delete_success = self.user_repo.delete_doctor(saved_user.id)
        self.assertTrue(delete_success)
        self.assertIsNone(self.user_repo.get_by_id(saved_user.id))

    def test_patient_repository_crud(self):
        cnp = "5010203123456"
        patient = PatientEntity(
            id=None,
            cnp=cnp,
            last_name="Georgescu",
            first_name="George"
        )
        
        # Test create patient
        success = self.patient_repo.create(patient)
        self.assertTrue(success)
        
        # Test get_by_cnp
        saved_patient = self.patient_repo.get_by_cnp(cnp)
        self.assertIsNotNone(saved_patient)
        self.assertEqual(saved_patient.last_name, "Georgescu")
        self.assertEqual(saved_patient.first_name, "George")
        
        # Test get_by_id
        saved_by_id = self.patient_repo.get_by_id(saved_patient.id)
        self.assertEqual(saved_by_id.cnp, cnp)
        
        # Test get_all
        all_patients = self.patient_repo.get_all()
        self.assertTrue(any(p.cnp == cnp for p in all_patients))

        # Test add_log and get_logs
        log_success = self.patient_repo.add_log(saved_patient.id, "internat", "Pacientul a fost internat.")
        self.assertTrue(log_success)
        
        logs = self.patient_repo.get_logs(saved_patient.id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["event_type"], "internat")
        self.assertEqual(logs[0]["details"], "Pacientul a fost internat.")
        
        # Test get_current_status
        status = self.patient_repo.get_current_status(saved_patient.id)
        self.assertEqual(status, "internat")

    def test_referral_repository_crud(self):
        # Creăm mai întâi un pacient și un doctor pentru referințe
        patient_cnp = "6020304123456"
        patient = PatientEntity(id=None, cnp=patient_cnp, last_name="Mihai", first_name="Ana")
        self.patient_repo.create(patient)
        saved_patient = self.patient_repo.get_by_cnp(patient_cnp)
        
        doctor_email = "referral.doc@spital.ro"
        doctor = User(
            id=None,
            last_name="Doctor",
            first_name="Trimitator",
            email=doctor_email,
            role="medic_urgente",
            specialty_id=self.user_repo.get_specialty_id_by_name("Urgențe")
        )
        self.user_repo.create(doctor, "hash", "salt")
        saved_doctor = self.user_repo.get_by_email(doctor_email)
        
        specialty_id = self.user_repo.get_specialty_id_by_name("Cardiologie")
        
        referral = Referral(
            id=None,
            patient_id=saved_patient.id,
            triage_level="Cod Galben",
            specialty_id=specialty_id,
            sender_id=saved_doctor.id,
            status="in_asteptare",
            observations="Posibil infarct"
        )
        
        # Test create referral
        success = self.referral_repo.create(referral)
        self.assertTrue(success)
        
        # Obținem referral-ul creat
        referrals = self.referral_repo.get_by_sender_id(saved_doctor.id)
        self.assertEqual(len(referrals), 1)
        saved_ref = referrals[0]
        self.assertEqual(saved_ref.triage_level, "Cod Galben")
        self.assertEqual(saved_ref.observations, "Posibil infarct")
        self.assertEqual(saved_ref.status, "in_asteptare")
        
        # Test get_pending_by_specialty
        pending_list = self.referral_repo.get_pending_by_specialty("Cardiologie")
        self.assertTrue(any(r.id == saved_ref.id for r in pending_list))
        
        # Creăm un alt doctor pe secția Cardiologie ca receptor
        rec_email = "cardio.doc@spital.ro"
        rec_doctor = User(
            id=None, last_name="Medic", first_name="Cardio", email=rec_email,
            role="medic_sectie", specialty_id=specialty_id
        )
        self.user_repo.create(rec_doctor, "hash", "salt")
        saved_rec = self.user_repo.get_by_email(rec_email)
        
        # Test update_status (acceptare trimitere)
        up_success = self.referral_repo.update_status(saved_ref.id, saved_rec.id, "acceptat", "Se interneaza in salonul 5")
        self.assertTrue(up_success)
        
        # Test get_by_id
        updated_ref = self.referral_repo.get_by_id(saved_ref.id)
        self.assertEqual(updated_ref.status, "acceptat")
        self.assertEqual(updated_ref.receiver_id, saved_rec.id)
        self.assertEqual(updated_ref.response_notes, "Se interneaza in salonul 5")
        
        # Test get_accepted_by_specialty
        accepted_list = self.referral_repo.get_accepted_by_specialty("Cardiologie")
        self.assertTrue(any(r.id == saved_ref.id for r in accepted_list))

    def test_simulation_repository_crud(self):
        # Creează utilizator manager pentru rulare
        mgr_email = "mgr.sim@spital.ro"
        mgr = User(id=None, last_name="Manager", first_name="Sim", email=mgr_email, role="manager")
        self.user_repo.create(mgr, "h", "s")
        saved_mgr = self.user_repo.get_by_email(mgr_email)
        
        run = SimulationRun(
            id=None,
            user_id=saved_mgr.id,
            run_name="Simulare Test Repozitoriu",
            num_doctors=2,
            num_nurses=2,
            arrival_rate=5.0,
            peak_multiplier=1.0,
            peak_start_min=0.0,
            peak_duration_min=0.0,
            simulation_duration=240.0,
            warmup_period=30.0,
            num_replications=5,
            random_seed=42,
            triage_distribution={1: 0.2, 2: 0.8},
            treatment_times={1: (20, 5), 2: (15, 3)},
            results_json=[{"replication": 1, "avg_waiting_time": 8.2}]
        )
        
        # Test save
        success = self.sim_repo.save(run)
        self.assertTrue(success)
        
        # Test get_by_user_id
        runs = self.sim_repo.get_by_user_id(saved_mgr.id)
        self.assertEqual(len(runs), 1)
        saved_run = runs[0]
        self.assertEqual(saved_run.run_name, "Simulare Test Repozitoriu")
        self.assertEqual(saved_run.num_doctors, 2)
        self.assertEqual(saved_run.triage_distribution[1], 0.2)
        self.assertEqual(saved_run.treatment_times[2], (15, 3))
        self.assertEqual(saved_run.results_json[0]["avg_waiting_time"], 8.2)
        self.assertIsNotNone(saved_run.created_at)
        
        # Test rename
        rename_success = self.sim_repo.rename(saved_run.id, saved_mgr.id, "Nume Nou Simulare")
        self.assertTrue(rename_success)
        runs_after_rename = self.sim_repo.get_by_user_id(saved_mgr.id)
        self.assertEqual(runs_after_rename[0].run_name, "Nume Nou Simulare")
        
        # Test delete
        delete_success = self.sim_repo.delete(saved_run.id, saved_mgr.id)
        self.assertTrue(delete_success)
        self.assertEqual(len(self.sim_repo.get_by_user_id(saved_mgr.id)), 0)


if __name__ == "__main__":
    unittest.main()
