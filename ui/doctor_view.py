import streamlit as st
from services.doctor_service import DoctorService

class DoctorView:
    @staticmethod
    def render(doctor_service: DoctorService):
        """Randează formularele de creare cont medic și lista conturilor active."""
        st.subheader("Administrare Conturi Medici")
        st.markdown("Creați noi conturi de medici pe baza specializării acestora și gestionați conturile existente.")
        
        # Formular Creare Cont fără st.form pentru a permite actualizarea interactivă
        st.write("#### Date Medic Nou")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m_nume = st.text_input("Nume de familie", key="m_nume")
            m_prenume = st.text_input("Prenume", key="m_prenume")
            m_email = st.text_input("Adresă Email", key="m_email")
        with col_m2:
            m_password = st.text_input("Parolă (minim 6 caractere)", type="password", key="m_password")
            
            # Preluare specializări (listă statică)
            specialties = doctor_service.get_all_specialties()
            m_spec_sel = st.selectbox("Specializare", specialties, key="m_spec_sel")
            
        if st.button("Creează Cont Medic", use_container_width=True, type="primary"):
            if not m_nume or not m_prenume or not m_email or not m_password or not m_spec_sel:
                st.error("Toate câmpurile sunt obligatorii.")
            elif len(m_password) < 6:
                st.error("Parola trebuie să aibă cel puțin 6 caractere.")
            else:
                success_reg, msg_reg = doctor_service.register_doctor(
                    nume=m_nume,
                    prenume=m_prenume,
                    email=m_email,
                    password=m_password,
                    specialty=m_spec_sel
                )
                
                if success_reg:
                    st.success(f"Contul medicului Dr. {m_prenume} {m_nume} a fost creat cu succes.")
                    # Ștergere campuri din session state
                    for k in ["m_nume", "m_prenume", "m_email", "m_password"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
                else:
                    st.error(f"Eroare la crearea contului: {msg_reg}")
                    
        st.markdown("---")
        st.write("#### Conturi Medici Înregistrați")
        
        doctors = doctor_service.get_all_doctors()
        if not doctors:
            st.info("Nu există medici înregistrați în baza de date.")
        else:
            for doc in doctors:
                role_label = "Medic Urgențe" if doc.role == "medic_urgente" else f"Medic Secție - {doc.specialty or 'Nespecificată'}"
                col_d1, col_d2, col_d3 = st.columns([3, 2, 1])
                with col_d1:
                    st.write(f"**Dr. {doc.prenume} {doc.nume}** - {doc.email}")
                with col_d2:
                    st.write(role_label)
                with col_d3:
                    if st.button("Șterge", key=f"del_doc_{doc.id}", type="secondary", use_container_width=True):
                        success_del, msg_del = doctor_service.delete_doctor(doc.id)
                        if success_del:
                            st.success("Cont șters!")
                            st.rerun()
                        else:
                            st.error(msg_del)
