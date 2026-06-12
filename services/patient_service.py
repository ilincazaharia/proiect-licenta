from typing import Optional, Tuple
from repositories.patient_repository import PatientRepository
from domain.models import PatientEntity

class PatientService:
    def __init__(self, patient_repository: Optional[PatientRepository] = None):
        self.patient_repo = patient_repository or PatientRepository()

    def get_patient_by_cnp(self, cnp: str) -> Optional[PatientEntity]:
        """Caută un pacient după CNP."""
        cnp = cnp.strip()
        if not cnp:
            return None
        return self.patient_repo.get_by_cnp(cnp)

    def register_patient(self, cnp: str, last_name: str, first_name: str) -> Tuple[bool, Optional[PatientEntity], str]:
        """
        Validează și înregistrează un pacient nou în baza de date.
        Dacă pacientul există deja (după CNP), îl returnează fără a-l duplica.
        """
        cnp = cnp.strip()
        last_name = last_name.strip()
        first_name = first_name.strip()

        if not cnp or not last_name or not first_name:
            return False, None, "Toate câmpurile (CNP, Nume, Prenume) sunt obligatorii."

        # Validare elementară CNP (13 cifre)
        if not cnp.isdigit() or len(cnp) != 13:
            return False, None, "CNP-ul trebuie să fie format din exact 13 cifre."

        # Verificăm dacă există deja
        existing = self.patient_repo.get_by_cnp(cnp)
        if existing:
            return True, existing, "Pacientul există deja în baza de date."

        new_patient = PatientEntity(
            id=None,
            cnp=cnp,
            last_name=last_name,
            first_name=first_name
        )

        success = self.patient_repo.create(new_patient)
        if success:
            # Preluăm pacientul salvat din baza de date pentru a-i lua ID-ul generat
            saved_patient = self.patient_repo.get_by_cnp(cnp)
            if saved_patient:
                self.log_patient_event(saved_patient.id, "inregistrare", "Pacient inregistrat in sistem.")
            return True, saved_patient, "Pacientul a fost înregistrat cu succes."
        
        return False, None, "Eroare la salvarea pacientului în baza de date."

    def get_patient_logs(self, patient_id: int) -> list:
        """Obține toate logurile pentru un pacient."""
        return self.patient_repo.get_logs(patient_id)

    def get_patient_status(self, patient_id: int) -> str:
        """Determină statusul curent al pacientului."""
        return self.patient_repo.get_current_status(patient_id)

    def log_patient_event(self, patient_id: int, event_type: str, details: str) -> bool:
        """Loghează un eveniment în istoricul pacientului."""
        return self.patient_repo.add_log(patient_id, event_type, details)
