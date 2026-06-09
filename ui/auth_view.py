import streamlit as st
from services.auth_service import AuthService

class AuthView:
    @staticmethod
    def render(auth_service: AuthService):
        """Randează formularele de conectare și înregistrare UPU."""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.write("")
            st.write("")
            st.title("Autentificare Simulare UPU")
            
            tab_login, tab_register = st.tabs(["Conectare", "Inregistrare"])
            
            with tab_login:
                with st.form("form_login"):
                    email = st.text_input("Adresa de email")
                    password = st.text_input("Parola", type="password")
                    submit_login = st.form_submit_button("Conectare", use_container_width=True)
                    
                    if submit_login:
                        if not email or not password:
                            st.error("Va rugam sa completati toate campurile.")
                        else:
                            success, user = auth_service.verify_user(email, password)
                            if success and user:
                                st.session_state.logged_in = True
                                st.session_state.user_info = {
                                    "id": user.id,
                                    "email": user.email,
                                    "nume": user.nume,
                                    "prenume": user.prenume,
                                    "role": user.role,
                                    "specialty": user.specialty_name
                                }
                                st.rerun()
                            else:
                                st.error("Adresa de email sau parola incorecta.")
                                
            with tab_register:
                with st.form("form_register"):
                    nume = st.text_input("Nume")
                    prenume = st.text_input("Prenume")
                    email_reg = st.text_input("Adresa de email")
                    password_reg = st.text_input("Parola (minim 6 caractere)", type="password")
                    password_confirm = st.text_input("Confirmare parola", type="password")
                    submit_register = st.form_submit_button("Inregistrare", use_container_width=True)
                    
                    if submit_register:
                        if not nume or not prenume or not email_reg or not password_reg or not password_confirm:
                            st.error("Va rugam sa completati toate campurile.")
                        elif password_reg != password_confirm:
                            st.error("Parolele nu coincid.")
                        else:
                            success, message = auth_service.register_user(nume, prenume, email_reg, password_reg)
                            if success:
                                st.success("Contul a fost creat cu succes. Va puteti conecta din tab-ul Conectare.")
                            else:
                                st.error(message)
        st.stop()
