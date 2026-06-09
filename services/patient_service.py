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

    def register_patient(self, cnp: str, nume: str, prenume: str) -> Tuple[bool, Optional[PatientEntity], str]:
        """
        Validează și înregistrează un pacient nou în baza de date.
        Dacă pacientul există deja (după CNP), îl returnează fără a-l duplica.
        """
        cnp = cnp.strip()
        nume = nume.strip()
        prenume = prenume.strip()

        if not cnp or not nume or not prenume:
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
            nume=nume,
            prenume=prenume
        )

        success = self.patient_repo.create(new_patient)
        if success:
            # Preluăm pacientul salvat din baza de date pentru a-i lua ID-ul generat
            saved_patient = self.patient_repo.get_by_cnp(cnp)
            return True, saved_patient, "Pacientul a fost înregistrat cu succes."
        
        return False, None, "Eroare la salvarea pacientului în baza de date."
