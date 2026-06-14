import streamlit as st
import pandas as pd
import textwrap
from services.patient_service import PatientService
from services.referral_service import ReferralService
from services.doctor_service import DoctorService
from ui.doctor_utils import DoctorUtils

class DoctorUPUView:
    @staticmethod
    def render(user_info: dict, patient_service: PatientService, referral_service: ReferralService):
        """Randează interfața pentru medicul din Urgențe."""
        if "reset_search_cnp" in st.session_state and st.session_state.reset_search_cnp:
            st.session_state.search_cnp_input = ""
            st.session_state.reset_search_cnp = False

        st.subheader("Căutare Pacient")
        
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
                        "trimis_sectie": "În așteptare pe secție",
                        "internat": "Internat pe secție",
                        "refuzat": "Refuzat",
                        "externat": "Externat"
                    }
                    st.info(f"**Stare curentă pacient:** {status_translation.get(status, status)}")
                    
                    with st.expander("Vizualizare Istoric Medical Pacient"):
                        DoctorUtils.render_patient_history(patient.id, patient_service)
                else:
                    st.info("Pacientul nu este înregistrat în sistem. Completați formularul de mai jos pentru înregistrare.")
                    
                    # Formular înregistrare pacient nou
                    with st.form("form_register_patient"):
                        st.write("### Înregistrare Pacient Nou")
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

                triage_options = ["Cod Roșu", "Cod Galben", "Cod Verde", "Cod Albastru", "Cod Alb"]
                triage_level = st.selectbox("Nivel de triaj", triage_options)
                
                # Secție destinație
                all_specialties = DoctorService.SPECIALTIES
                sectii_options = [s for s in all_specialties if s != "Urgențe"]
                specialty_dest = st.selectbox("Secție destinație", sectii_options)
                
                observatii = st.text_area("Observații medicale (opțional)", placeholder="Detalii despre starea pacientului...")
                
                submit_ref = st.form_submit_button("Trimite", use_container_width=True)
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

    @staticmethod
    @st.fragment(run_every=5)
    def render_history_fragment(user_info: dict, referral_service: ReferralService):
        st.markdown("---")
        st.subheader("Istoric Trimiteri Efectuate")
        referrals = referral_service.get_referrals_by_sender(user_info["id"])
        
        if not referrals:
            st.info("Nu ați efectuat nicio trimitere până în prezent.")
        else:
            html_rows = ""
            for r in referrals:
                triage_colors = {
                    "Cod Roșu": ("#ef4444", "#ffffff"),
                    "Cod Galben": ("#f59e0b", "#ffffff"),
                    "Cod Verde": ("#10b981", "#ffffff"),
                    "Cod Albastru": ("#3b82f6", "#ffffff"),
                    "Cod Alb": ("#6b7280", "#ffffff"),
                }
                tr_color = triage_colors.get(r.triage_level, ("#6b7280", "#ffffff"))
                triage_style = f"background-color: {tr_color[0]}; color: {tr_color[1]}; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;"
                
                # Status colors
                status_colors = {
                    "in_asteptare": ("rgba(245, 158, 11, 0.15)", "#f59e0b", "rgba(245, 158, 11, 0.3)", "În așteptare"),
                    "acceptat": ("rgba(16, 185, 129, 0.15)", "#10b981", "rgba(16, 185, 129, 0.3)", "Acceptat"),
                    "refuzat": ("rgba(239, 68, 68, 0.15)", "#ef4444", "rgba(239, 68, 68, 0.3)", "Refuzat"),
                    "externat": ("rgba(139, 92, 246, 0.15)", "#8b5cf6", "rgba(139, 92, 246, 0.3)", "Externat"),
                }
                st_color = status_colors.get(r.status, ("rgba(107, 114, 128, 0.15)", "#6b7280", "rgba(107, 114, 128, 0.3)", r.status.capitalize()))
                status_style = f"background-color: {st_color[0]}; color: {st_color[1]}; border: 1px solid {st_color[2]}; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;"
                
                obs = r.observations or "-"
                resp = r.response_notes or "-"
                
                html_rows += textwrap.dedent(f"""
                <tr style="margin-bottom: 8px;">
                    <td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.05); border-radius: 8px 0 0 8px; font-weight: 500; color: #f0f2f6;">{r.patient_name}</td>
                    <td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.05); color: #a3a8b4;">{r.patient_cnp}</td>
                    <td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.05);"><span style="{triage_style}">{r.triage_level}</span></td>
                    <td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.05); color: #f0f2f6;">{r.specialty_name}</td>
                    <td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.05);"><span style="{status_style}">{st_color[3]}</span></td>
                    <td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.05); color: #f0f2f6; max-width: 220px; word-wrap: break-word;">{obs}</td>
                    <td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.05); border-radius: 0 8px 8px 0; color: #a3a8b4; max-width: 220px; word-wrap: break-word;">{resp}</td>
                </tr>
                """).strip()
                
            table_html = textwrap.dedent(f"""
            <div style="background-color: rgba(255, 255, 255, 0.02); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05);">
                <table style="width: 100%; border-collapse: separate; border-spacing: 0 8px; text-align: left; font-family: inherit;">
                    <thead>
                        <tr style="color: #a3a8b4; font-weight: 600; font-size: 0.9em;">
                            <th style="padding: 10px;">Pacient</th>
                            <th style="padding: 10px;">CNP</th>
                            <th style="padding: 10px;">Nivel Triaj</th>
                            <th style="padding: 10px;">Secție Destinație</th>
                            <th style="padding: 10px;">Status</th>
                            <th style="padding: 10px;">Observații</th>
                            <th style="padding: 10px;">Răspuns Secție</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_rows}
                    </tbody>
                </table>
            </div>
            """).strip()
            st.markdown(table_html, unsafe_allow_html=True)
