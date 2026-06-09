import streamlit as st
import pandas as pd
from services.patient_service import PatientService
from services.referral_service import ReferralService
from services.doctor_service import DoctorService

class ReferralView:
    @staticmethod
    def render_doctor_urgente(user_info: dict, patient_service: PatientService, referral_service: ReferralService):
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
                    st.success(f"Pacient găsit: {patient.prenume} {patient.nume}")
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
                                nume=new_nume,
                                prenume=new_prenume
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
                        specialty=specialty_dest,
                        sender_id=user_info["id"],
                        observatii=observatii
                    )
                    if success:
                        st.success(msg)
                        st.session_state.reset_search_cnp = True
                        st.rerun()
                    else:
                        st.error(msg)

        # Istoric trimiteri efectuate (randat în fragment auto-refresh)
        ReferralView.render_history_fragment(user_info, referral_service)

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
                    "Secție Destinație": r.specialty,
                    "Status": r.status.replace("in_asteptare", "În așteptare").replace("acceptat", "Acceptat").replace("refuzat", "Refuzat"),
                    "Observații": r.observatii or "-",
                    "Răspuns Secție": r.response_notes or "-"
                })
            
            df = pd.DataFrame(ref_data)
            st.dataframe(df, use_container_width=True)


    @staticmethod
    def render_doctor_sectie(user_info: dict, referral_service: ReferralService):
        """Randează interfața pentru medicul de pe o secție de specialitate."""
        specialty = user_info.get("specialty", "")
        if not specialty or specialty == "Urgențe":
            st.error("Utilizatorul conectat nu este asociat unei secții de specialitate valide.")
            return

        ReferralView.render_sectie_fragment(user_info, referral_service, specialty)

    @st.fragment(run_every=5)
    @staticmethod
    def render_sectie_fragment(user_info: dict, referral_service: ReferralService, specialty: str):
        st.subheader("Solicitări Noi de Internare (în așteptare)")
        pending_referrals = referral_service.get_pending_referrals_for_specialty(specialty)
        
        if not pending_referrals:
            st.info("Nu există solicitări noi în așteptare pentru secția dumneavoastră.")
        else:
            for r in pending_referrals:
                with st.container(border=True):
                    col_p1, col_p2 = st.columns([3, 1])
                    with col_p1:
                        st.write(f"**Pacient:** {r.patient_name} (CNP: {r.patient_cnp})")
                        st.write(f"**Nivel Triaj:** {r.triage_level}")
                        st.write(f"**Medic Trimițător:** Dr. {r.sender_name}")
                        st.write(f"**Observații UPU:** {r.observatii or '-'}")
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
            pat_data = []
            for r in accepted_patients:
                pat_data.append({
                    "Pacient": r.patient_name,
                    "CNP": r.patient_cnp,
                    "Nivel Triaj UPU": r.triage_level,
                    "Medic Trimițător": f"Dr. {r.sender_name}",
                    "Observații UPU": r.observatii or "-",
                    "Note Internare": r.response_notes or "-"
                })
            
            df = pd.DataFrame(pat_data)
            st.dataframe(df, use_container_width=True)
