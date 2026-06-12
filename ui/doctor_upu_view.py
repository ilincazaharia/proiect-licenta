import streamlit as st
import pandas as pd
from services.patient_service import PatientService
from services.referral_service import ReferralService
from services.doctor_service import DoctorService
from ui.doctor_utils import DoctorUtils

class DoctorUPUView:
    @staticmethod
    def render(user_info: dict, patient_service: PatientService, referral_service: ReferralService):
        """Randează interfața pentru medicul din UPU (Urgențe)."""
        if "reset_search_cnp" in st.session_state and st.session_state.reset_search_cnp:
            st.session_state.search_cnp_input = ""
            st.session_state.reset_search_cnp = False

        st.subheader("Căutare și Înregistrare Pacient")
        
        # Căutare pacient după CNP
        search_cnp = st.text_input("Introduceți CNP pacient", max_chars=13, key="search_cnp_input")
        
        patient = None
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
                        "trimis_sectie": "În așteptare pe secție / În UPU",
                        "internat": "Internat pe secție",
                        "refuzat": "Refuzat / Externat din UPU",
                        "externat": "Externat (Disponibil)"
                    }
                    st.info(f"**Stare curentă pacient:** {status_translation.get(status, status)}")
                    
                    with st.expander("Vizualizare Istoric Medical Pacient"):
                        DoctorUtils.render_patient_history(patient.id, patient_service)
                else:
                    st.info("Pacientul nu este înregistrat în sistem. Completați formularul de mai jos pentru înregistrare.")
                    
                    # Formular înregistrare pacient nou
                    with st.form("form_register_patient"):
                        st.write("#### Înregistrare Pacient Nou")
                        new_nume = st.text_input("Nume de familie")
                        new_prenume = st.text_input("Prenume")
                        submit_pat = st.form_submit_button("Înregistrează Pacient", use_container_width=True)
                        
                        if submit_pat:
                            success, registered_patient, msg = patient_service.register_patient(
                                cnp=search_cnp,
                                last_name=new_nume,
                                first_name=new_prenume
                            )
                            if success and registered_patient:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
        
        # Dacă pacientul este găsit/înregistrat, afișăm formularul de trimitere
        if patient:
            st.markdown("---")
            st.subheader("Trimitere Pacient către Secție")
            
            with st.form("form_create_referral"):
                # Nivel triaj
                triage_options = ["Cod Roșu", "Cod Galben", "Cod Verde", "Cod Albastru", "Cod Alb"]
                triage_level = st.selectbox("Nivel de triaj pacient", triage_options)
                
                # Secție destinație (excludem Urgențe)
                all_specialties = DoctorService.SPECIALTIES
                sectii_options = [s for s in all_specialties if s != "Urgențe"]
                specialty_dest = st.selectbox("Secție destinație", sectii_options)
                
                observatii = st.text_area("Observații medicale (opțional)", placeholder="Detalii despre starea pacientului...")
                
                submit_ref = st.form_submit_button("Trimite pacient către secție", use_container_width=True)
                if submit_ref:
                    success, msg = referral_service.create_referral(
                        patient_id=patient.id,
                        triage_level=triage_level,
                        specialty_name=specialty_dest,
                        sender_id=user_info["id"],
                        observations=observatii
                    )
                    if success:
                        st.success(msg)
                        st.session_state.reset_search_cnp = True
                        st.rerun()
                    else:
                        st.error(msg)

        # Istoric trimiteri efectuate
        DoctorUPUView.render_history_fragment(user_info, referral_service)

    @st.fragment(run_every=5)
    @staticmethod
    def render_history_fragment(user_info: dict, referral_service: ReferralService):
        st.markdown("---")
        st.subheader("Istoric Trimiteri Efectuate")
        referrals = referral_service.get_referrals_by_sender(user_info["id"])
        
        if not referrals:
            st.info("Nu ați efectuat nicio trimitere până în prezent.")
        else:
            ref_data = []
            for r in referrals:
                ref_data.append({
                    "Pacient": r.patient_name,
                    "CNP": r.patient_cnp,
                    "Nivel Triaj": r.triage_level,
                    "Secție Destinație": r.specialty_name,
                    "Status": r.status.replace("in_asteptare", "În așteptare").replace("acceptat", "Acceptat").replace("refuzat", "Refuzat").replace("externat", "Externat"),
                    "Observații": r.observations or "-",
                    "Răspuns Secție": r.response_notes or "-"
                })
            
            df = pd.DataFrame(ref_data)
            st.dataframe(df, use_container_width=True)
