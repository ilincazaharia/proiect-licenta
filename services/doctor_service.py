from typing import List, Tuple, Optional
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from domain.models import User

class DoctorService:
    # Listă statică de specializări definită conform cerințelor
    SPECIALTIES = [
        "Urgențe",
        "Cardiologie",
        "Neurologie",
        "Pediatrie",
        "Chirurgie",
        "Terapie Intensivă",
        "Gastroenterologie"
    ]

    def __init__(self, user_repository: Optional[UserRepository] = None, auth_service: Optional[AuthService] = None):
        self.user_repo = user_repository or UserRepository()
        self.auth_service = auth_service or AuthService(self.user_repo)

    def get_all_specialties(self) -> List[str]:
        """Returnează lista statică de specializări."""
        return self.SPECIALTIES

    def get_all_doctors(self) -> List[User]:
        """Returnează toți medicii înregistrați."""
        return self.user_repo.get_all_doctors()

    def delete_doctor(self, doctor_id: int) -> Tuple[bool, str]:
        """Șterge un medic din baza de date."""
        success = self.user_repo.delete_doctor(doctor_id)
        if success:
            return True, "Contul de medic a fost șters cu succes."
        return False, "Eroare la ștergerea contului de medic."

    def register_doctor(self, nume: str, prenume: str, email: str, password: str, specialty: str) -> Tuple[bool, str]:
        """
        Înregistrează un cont nou de medic (urgente sau sectie) pe baza specializării alese.
        Dacă specializarea este "Urgențe", rolul va fi 'medic_urgente'.
        Altfel, rolul va fi 'medic_sectie' cu specializarea respectivă.
        """
        specialty = specialty.strip()
        if specialty == "Urgențe":
            target_role = "medic_urgente"
        else:
            target_role = "medic_sectie"
            
        success, msg = self.auth_service.register_user(
            nume=nume,
            prenume=prenume,
            email=email,
            password=password,
            role=target_role,
            specialty=specialty
        )
        return success, msg
