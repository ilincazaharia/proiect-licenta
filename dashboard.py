import streamlit as st
import pandas as pd
from repositories.db_connection import DBConnection
from services.auth_service import AuthService
from services.doctor_service import DoctorService
from services.simulation_service import SimulationService
from services.patient_service import PatientService
from services.referral_service import ReferralService
from ui.auth_view import AuthView
from ui.sidebar import SidebarView
from ui.manager_view import ManagerView
from ui.doctor_upu_view import DoctorUPUView
from ui.doctor_sectie_view import DoctorSectieView

# Inițializare bază de date SQLite
DBConnection.init_db()

# Instanțiere servicii (Business Logic Layer)
auth_service = AuthService()
doctor_service = DoctorService()
simulation_service = SimulationService()
patient_service = PatientService()
referral_service = ReferralService()

# Setare pagină
st.set_page_config(page_title="Simulare UPU", layout="wide")

# Inițializare session state pentru autentificare
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# Auto-login pe bază de query params dacă sesiunea a fost reîmprospătată
if not st.session_state.logged_in and "user_id" in st.query_params:
    try:
        user_id = int(st.query_params["user_id"])
        from repositories.user_repository import UserRepository
        user = UserRepository().get_by_id(user_id)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_info = {
                "id": user.id,
                "email": user.email,
                "last_name": user.last_name,
                "first_name": user.first_name,
                "role": user.role,
                "specialty_name": user.specialty_name
            }
    except Exception as e:
        pass

# Inițializare session state pentru rezultate active
if "current_results" not in st.session_state:
    st.session_state.current_results = None
if "current_summary" not in st.session_state:
    st.session_state.current_summary = None
if "current_run_name" not in st.session_state:
    st.session_state.current_run_name = None

# Inițializare parametri în session state pentru a fi folosiți de sliders din sidebar
if "num_doctors" not in st.session_state: st.session_state.num_doctors = 10
if "num_nurses" not in st.session_state: st.session_state.num_nurses = 20
if "arrival_rate" not in st.session_state: st.session_state.arrival_rate = 30.0
if "peak_multiplier" not in st.session_state: st.session_state.peak_multiplier = 2.0
if "peak_start" not in st.session_state: st.session_state.peak_start = 120
if "peak_duration" not in st.session_state: st.session_state.peak_duration = 120
if "p_red" not in st.session_state: st.session_state.p_red = 5
if "p_yellow" not in st.session_state: st.session_state.p_yellow = 15
if "p_green" not in st.session_state: st.session_state.p_green = 20
if "p_blue" not in st.session_state: st.session_state.p_blue = 25
if "p_white" not in st.session_state: st.session_state.p_white = 35
if "t_red" not in st.session_state: st.session_state.t_red = 45
if "t_yellow" not in st.session_state: st.session_state.t_yellow = 30
if "t_green" not in st.session_state: st.session_state.t_green = 20
if "t_blue" not in st.session_state: st.session_state.t_blue = 15
if "t_white" not in st.session_state: st.session_state.t_white = 10
if "sim_duration" not in st.session_state: st.session_state.sim_duration = 480
if "replications" not in st.session_state: st.session_state.replications = 30

# Funcție Deconectare
def logout():
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.query_params.clear()
    st.rerun()

# --- BLOC AUTENTIFICARE ---
if not st.session_state.logged_in:
    AuthView.render(auth_service)

# --- BLOC APLICAȚIE AUTENTIFICATĂ ---
user_role = st.session_state.user_info.get("role", "manager")

if user_role == "manager":
    st.title("Dashboard Simulare UPU")

    # 1. Randare sidebar configurare și preluare date
    config_sidebar_data = SidebarView.render(logout)

    # 2. Configurare tab-uri principale manager
    ManagerView.render(
        simulation_service=simulation_service,
        doctor_service=doctor_service,
        user_id=st.session_state.user_info["id"],
        config_sidebar_data=config_sidebar_data
    )

else:
    # --- PANOU CONTROL MEDIC ---
    st.sidebar.header("Utilizator conectat")
    st.sidebar.text(f"{st.session_state.user_info['first_name']} {st.session_state.user_info['last_name']}")
    st.sidebar.text(st.session_state.user_info['email'])
    
    role_display = "Medic Urgențe" if user_role == "medic_urgente" else f"Medic {st.session_state.user_info.get('specialty_name', 'Nespecificat')}"
    st.sidebar.text(role_display)
    
    if st.sidebar.button("Deconectare", type="secondary", use_container_width=True):
        logout()
    st.sidebar.markdown("---")
    
    if user_role == "medic_urgente":
        st.title(f"Bine ați venit, Dr. {st.session_state.user_info['first_name']} {st.session_state.user_info['last_name']}")
        DoctorUPUView.render(
            user_info=st.session_state.user_info,
            patient_service=patient_service,
            referral_service=referral_service
        )
            
    elif user_role == "medic_sectie":
        spec_name = st.session_state.user_info.get('specialty_name', 'Nespecificat')
        st.title(f"Bine ați venit, Dr. {st.session_state.user_info['first_name']} {st.session_state.user_info['last_name']}")
        DoctorSectieView.render(
            user_info=st.session_state.user_info,
            referral_service=referral_service,
            patient_service=patient_service
        )
