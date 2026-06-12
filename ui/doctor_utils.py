import streamlit as st
from services.patient_service import PatientService

class DoctorUtils:
    @staticmethod
    def render_patient_history(patient_id: int, patient_service: PatientService):
        """Randează istoricul medical (logurile) al unui pacient într-un mod prietenos."""
        logs = patient_service.get_patient_logs(patient_id)
        if not logs:
            st.info("Nu există istoric medical înregistrat pentru acest pacient.")
            return

        # Mapare tipuri evenimente la etichete mai prietenoase și culori
        event_meta = {
            "inregistrare": ("Înregistrare Sistem", "blue"),
            "trimis_sectie": ("Sosire UPU & Trimitere", "orange"),
            "internat": ("Internare Secție", "green"),
            "refuzat": ("Refuz Internare", "red"),
            "externat": ("Externare Secție", "violet")
        }

        st.markdown("##### Istoric Medical Cronologic (Patient Logs)")
        for log in logs:
            ev_type = log["event_type"]
            meta = event_meta.get(ev_type, (ev_type.capitalize(), "grey"))
            label, color = meta
            
            with st.container(border=True):
                col_time, col_ev = st.columns([1.2, 3])
                with col_time:
                    st.caption(f"{log['timestamp']}")
                with col_ev:
                    st.markdown(f"**:{color}[{label}]**")
                    st.write(log["details"])
