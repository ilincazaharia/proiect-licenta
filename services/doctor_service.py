from typing import List, Tuple, Optional
from repositories.user_repository import UserRepository
from repositories.specialty_repository import SpecialtyRepository
from services.auth_service import AuthService
from domain.models import User, Specialty

class DoctorService:
    def __init__(self, user_repository: Optional[UserRepository] = None, specialty_repository: Optional[SpecialtyRepository] = None, auth_service: Optional[AuthService] = None):
        self.user_repo = user_repository or UserRepository()
        self.specialty_repo = specialty_repository or SpecialtyRepository()
        self.auth_service = auth_service or AuthService(self.user_repo)

    def get_all_specialties(self) -> List[Specialty]:
        """Returnează toate specializările."""
        return self.specialty_repo.get_all()

    def get_all_doctors(self) -> List[User]:
        """Returnează toți medicii înregistrați."""
        return self.user_repo.get_all_doctors()

    def delete_doctor(self, doctor_id: int) -> Tuple[bool, str]:
        """Șterge un medic din baza de date."""
        success = self.user_repo.delete_doctor(doctor_id)
        if success:
            return True, "Contul de medic a fost șters cu succes."
        return False, "Eroare la ștergerea contului de medic."

    def register_doctor(self, nume: str, prenume: str, email: str, password: str, role_display: str, specialty_id: Optional[int]) -> Tuple[bool, str]:
        """
        Înregistrează un cont nou de medic (urgente sau sectie) folosind AuthService.
        """
        target_role = "medic_urgente" if role_display == "Medic Urgențe" else "medic_sectie"
        target_spec_id = specialty_id if target_role == "medic_sectie" else None
        
        success, msg = self.auth_service.register_user(
            nume=nume,
            prenume=prenume,
            email=email,
            password=password,
            role=target_role,
            specialty_id=target_spec_id
        )
        return success, msg
