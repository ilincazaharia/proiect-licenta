from typing import List, Tuple, Optional
from repositories.referral_repository import ReferralRepository
from domain.models import Referral

class ReferralService:
    def __init__(self, referral_repository: Optional[ReferralRepository] = None):
        self.referral_repo = referral_repository or ReferralRepository()

    def create_referral(self, patient_id: int, triage_level: str, specialty: str, sender_id: int, observatii: Optional[str] = None) -> Tuple[bool, str]:
        """Creează o nouă trimitere din UPU către o secție de specialitate."""
        if not patient_id:
            return False, "ID-ul pacientului este invalid."
        if not triage_level or triage_level not in ["Cod Roșu", "Cod Galben", "Cod Verde", "Cod Albastru", "Cod Alb"]:
            return False, "Nivelul de triaj este invalid."
        if not specialty or specialty == "Urgențe":
            return False, "Secția de destinație este invalidă."
        if not sender_id:
            return False, "ID-ul medicului trimițător este invalid."

        new_referral = Referral(
            id=None,
            patient_id=patient_id,
            triage_level=triage_level,
            specialty=specialty,
            sender_id=sender_id,
            status="in_asteptare",
            observatii=observatii
        )

        success = self.referral_repo.create(new_referral)
        if success:
            return True, "Trimiterea a fost înregistrată cu succes în stare de așteptare."
        return False, "Eroare la salvarea trimiterii în baza de date."

    def get_referrals_by_sender(self, sender_id: int) -> List[Referral]:
        """Obține trimiterile create de un anumit medic de urgențe."""
        return self.referral_repo.get_by_sender_id(sender_id)

    def get_pending_referrals_for_specialty(self, specialty: str) -> List[Referral]:
        """Obține toate trimiterile în așteptare pentru o secție specializată."""
        return self.referral_repo.get_pending_by_specialty(specialty)

    def get_accepted_patients_for_specialty(self, specialty: str) -> List[Referral]:
        """Obține toți pacienții care au fost acceptați pe o secție (internați)."""
        return self.referral_repo.get_accepted_by_specialty(specialty)

    def respond_to_referral(self, referral_id: int, receiver_id: int, accept: bool, response_notes: str) -> Tuple[bool, str]:
        """
        Medicul de pe secție acceptă sau refuză trimiterea primită.
        Actualizează starea în 'acceptat' sau 'refuzat'.
        """
        status = "acceptat" if accept else "refuzat"
        response_notes = response_notes.strip()
        
        success = self.referral_repo.update_status(
            referral_id=referral_id,
            receiver_id=receiver_id,
            status=status,
            response_notes=response_notes
        )
        if success:
            action = "acceptată" if accept else "refuzată"
            return True, f"Trimiterea a fost {action} cu succes."
        return False, "Eroare la actualizarea stării trimiterii în baza de date."
