import streamlit as st
from services.patient_service import PatientService
from services.referral_service import ReferralService
from ui.doctor_utils import DoctorUtils

class DoctorSectieView:
    @staticmethod
    def render(user_info: dict, referral_service: ReferralService, patient_service: PatientService):
        """Randează interfața pentru medicul de pe o secție de specialitate."""
        specialty = user_info.get("specialty_name", "")
        if not specialty or specialty == "Urgențe":
            st.error("Utilizatorul conectat nu este asociat unei secții de specialitate valide.")
            return

        # Căutare generală pacient pentru vizualizare istoric
        st.subheader("Căutare Pacient și Vizualizare Istoric")
        search_cnp = st.text_input("Introduceți CNP pacient", max_chars=13, key="search_cnp_sectie")
        if search_cnp:
            search_cnp = search_cnp.strip()
            if not search_cnp.isdigit() or len(search_cnp) != 13:
                st.warning("CNP-ul trebuie să conțină exact 13 cifre.")
            else:
                patient = patient_service.get_patient_by_cnp(search_cnp)
                if patient:
                    st.success(f"Pacient găsit: {patient.first_name} {patient.last_name}")
                    status = patient_service.get_patient_status(patient.id)
                    status_translation = {
                        "inregistrare": "Înregistrat",
                        "trimis_sectie": "În așteptare pe secție",
                        "internat": "Internat pe secție",
                        "refuzat": "Refuzat",
                        "externat": "Externat"
                    }
                    st.info(f"**Stare curentă pacient:** {status_translation.get(status, status)}")
                    with st.expander("Vizualizare Istoric Medical Pacient", expanded=True):
                        DoctorUtils.render_patient_history(patient.id, patient_service)
                else:
                    st.warning("Pacientul nu a fost găsit în sistem.")
        
        st.markdown("---")
        DoctorSectieView.render_sectie_fragment(user_info, referral_service, patient_service, specialty)

    @st.fragment(run_every=5)
    @staticmethod
    def render_sectie_fragment(user_info: dict, referral_service: ReferralService, patient_service: PatientService, specialty: str):
        st.subheader("Solicitări Noi de Internare")
        pending_referrals = referral_service.get_pending_referrals_for_specialty(specialty)
        
        if not pending_referrals:
            st.info("Nu există solicitări noi de internare.")
        else:
            for r in pending_referrals:
                with st.container(border=True):
                    col_p1, col_p2 = st.columns([3, 1])
                    with col_p1:
                        st.write(f"**Pacient:** {r.patient_name} (CNP: {r.patient_cnp})")
                        st.write(f"**Nivel Triaj:** {r.triage_level}")
                        st.write(f"**Medic Trimițător:** Dr. {r.sender_name}")
                        st.write(f"**Observații UPU:** {r.observations or '-'}")
                        with st.expander("Vizualizare Istoric Medical"):
                            DoctorUtils.render_patient_history(r.patient_id, patient_service)
                    with col_p2:
                        response_note = st.text_input("Observații răspuns (opțional)", key=f"note_{r.id}")
                        
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            if st.button("Acceptă", key=f"acc_{r.id}", type="primary", use_container_width=True):
                                success, msg = referral_service.respond_to_referral(
                                    referral_id=r.id,
                                    receiver_id=user_info["id"],
                                    accept=True,
                                    response_notes=response_note
                                )
                                if success:
                                    st.success("Pacient acceptat pe secție.")
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with col_b2:
                            if st.button("Refuză", key=f"ref_{r.id}", type="secondary", use_container_width=True):
                                success, msg = referral_service.respond_to_referral(
                                    referral_id=r.id,
                                    receiver_id=user_info["id"],
                                    accept=False,
                                    response_notes=response_note
                                )
                                if success:
                                    st.warning("Trimitere refuzată.")
                                    st.rerun()
                                else:
                                    st.error(msg)

        # Pacienți internați pe secție
        st.markdown("---")
        st.subheader("Pacienți Internați pe Secție")
        accepted_patients = referral_service.get_accepted_patients_for_specialty(specialty)
        
        if not accepted_patients:
            st.info("Nu există pacienți internați în prezent pe secția dumneavoastră.")
        else:
            for r in accepted_patients:
                with st.container(border=True):
                    col_p1, col_p2 = st.columns([3, 1])
                    with col_p1:
                        st.write(f"**Pacient:** {r.patient_name} (CNP: {r.patient_cnp})")
                        st.write(f"**Nivel Triaj UPU:** {r.triage_level}")
                        st.write(f"**Medic:** Dr. {r.sender_name}")
                        st.write(f"**Observații UPU:** {r.observations or '-'}")
                        st.write(f"**Note Internare:** {r.response_notes or '-'}")
                        with st.expander("Vizualizare Istoric Medical"):
                            DoctorUtils.render_patient_history(r.patient_id, patient_service)
                    with col_p2:
                        discharge_notes = st.text_input("Observații externare (opțional)", key=f"dis_notes_{r.id}")
                        if st.button("Externează", key=f"dis_{r.id}", type="primary", use_container_width=True):
                            success, msg = referral_service.discharge_patient(
                                referral_id=r.id,
                                patient_id=r.patient_id,
                                response_notes=discharge_notes
                            )
                            if success:
                                st.success("Pacient externat cu succes.")
                                st.rerun()
                            else:
                                st.error(msg)
