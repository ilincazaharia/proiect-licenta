from typing import List, Tuple, Optional
from repositories.referral_repository import ReferralRepository
from repositories.patient_repository import PatientRepository
from repositories.user_repository import UserRepository
from domain.models import Referral

class ReferralService:
    def __init__(self, referral_repository: Optional[ReferralRepository] = None, patient_repository: Optional[PatientRepository] = None):
        self.referral_repo = referral_repository or ReferralRepository()
        self.patient_repo = patient_repository or PatientRepository()
        self.user_repo = UserRepository()

    def create_referral(self, patient_id: int, triage_level: str, specialty_name: str, sender_id: int, observations: Optional[str] = None) -> Tuple[bool, str]:
        """Creează o nouă trimitere din UPU către o secție de specialitate."""
        if not patient_id:
            return False, "ID-ul pacientului este invalid."
        if not triage_level or triage_level not in ["Cod Roșu", "Cod Galben", "Cod Verde", "Cod Albastru", "Cod Alb"]:
            return False, "Nivelul de triaj este invalid."
        if not specialty_name or specialty_name == "Urgențe":
            return False, "Secția de destinație este invalidă."
        if not sender_id:
            return False, "ID-ul medicului trimițător este invalid."

        specialty_id = self.user_repo.get_specialty_id_by_name(specialty_name)
        if not specialty_id:
            return False, "Secția de destinație este invalidă."

        new_referral = Referral(
            id=None,
            patient_id=patient_id,
            triage_level=triage_level,
            specialty_id=specialty_id,
            sender_id=sender_id,
            status="in_asteptare",
            observations=observations
        )

        success = self.referral_repo.create(new_referral)
        if success:
            obs_details = f". Observatii: {observations}" if observations else ""
            self.patient_repo.add_log(
                patient_id=patient_id,
                event_type="trimis_sectie",
                details=f"Sosire in UPU si trimitere catre sectia {specialty_name} (Nivel triaj: {triage_level}){obs_details}"
            )
            return True, "Trimiterea a fost înregistrată cu succes în stare de așteptare."
        return False, "Eroare la salvarea trimiterii în baza de date."

    def get_referrals_by_sender(self, sender_id: int) -> List[Referral]:
        """Obține trimiterile create de un anumit medic de urgențe."""
        return self.referral_repo.get_by_sender_id(sender_id)

    def get_pending_referrals_for_specialty(self, specialty_name: str) -> List[Referral]:
        """Obține toate trimiterile în așteptare pentru o secție specializată."""
        return self.referral_repo.get_pending_by_specialty(specialty_name)

    def get_accepted_patients_for_specialty(self, specialty_name: str) -> List[Referral]:
        """Obține toți pacienții care au fost acceptați pe o secție (internați)."""
        return self.referral_repo.get_accepted_by_specialty(specialty_name)

    def respond_to_referral(self, referral_id: int, receiver_id: int, accept: bool, response_notes: str) -> Tuple[bool, str]:
        """
        Medicul de pe secție acceptă sau refuză trimiterea primită.
        Actualizează starea în 'acceptat' sau 'refuzat'.
        """
        status = "acceptat" if accept else "refuzat"
        response_notes = response_notes.strip()
        
        ref = self.referral_repo.get_by_id(referral_id)
        if not ref:
            return False, "Trimiterea specificată nu a fost găsită."

        success = self.referral_repo.update_status(
            referral_id=referral_id,
            receiver_id=receiver_id,
            status=status,
            response_notes=response_notes
        )
        if success:
            action = "acceptată" if accept else "refuzată"
            event_type = "internat" if accept else "refuzat"
            note_details = f". Note: {response_notes}" if response_notes else ""
            
            if accept:
                msg = f"Internat pe sectia {ref.specialty_name}{note_details}"
            else:
                msg = f"Trimitere refuzata de sectia {ref.specialty_name}{note_details}"

            self.patient_repo.add_log(
                patient_id=ref.patient_id,
                event_type=event_type,
                details=msg
            )
            return True, f"Trimiterea a fost {action} cu succes."
        return False, "Eroare la actualizarea stării trimiterii în baza de date."

    def discharge_patient(self, referral_id: int, patient_id: int, response_notes: str) -> Tuple[bool, str]:
        """
        Externează un pacient de pe secție.
        Actualizează starea trimiterii în 'externat' și adaugă logul aferent.
        """
        response_notes = response_notes.strip()
        ref = self.referral_repo.get_by_id(referral_id)
        if not ref:
            return False, "Trimiterea specificată nu a fost găsită."

        success = self.referral_repo.update_status(
            referral_id=referral_id,
            receiver_id=ref.receiver_id,
            status="externat",
            response_notes=response_notes if response_notes else ref.response_notes
        )
        if success:
            note_details = f". Note externare: {response_notes}" if response_notes else ""
            self.patient_repo.add_log(
                patient_id=patient_id,
                event_type="externat",
                details=f"Externat de pe sectia {ref.specialty_name}{note_details}"
            )
            return True, "Pacientul a fost externat cu succes."
        return False, "Eroare la externarea pacientului din baza de date."
