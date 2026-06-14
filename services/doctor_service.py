from typing import List, Tuple, Optional
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from domain.models import User

class DoctorService:
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
        """Returnează lista statică de specializări în engleză."""
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

    def register_doctor(self, last_name: str, first_name: str, email: str, password: str, specialty_name: str) -> Tuple[bool, str]:
        """
        Înregistrează un cont nou de medic (urgente sau sectie) pe baza specializării alese.
        Dacă specializarea este "Emergency", rolul va fi 'medic_urgente'.
        Altfel, rolul va fi 'medic_sectie' cu specializarea respectivă.
        """
        specialty_name = specialty_name.strip()
        if specialty_name == "Urgențe":
            target_role = "medic_urgente"
        else:
            target_role = "medic_sectie"
            
        specialty_id = self.user_repo.get_specialty_id_by_name(specialty_name)
        if not specialty_id:
            return False, "Specializarea aleasă este invalidă."
            
        success, msg = self.auth_service.register_user(
            last_name=last_name,
            first_name=first_name,
            email=email,
            password=password,
            role=target_role,
            specialty_id=specialty_id
        )
        return success, msg
