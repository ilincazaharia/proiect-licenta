import streamlit as st
import pandas as pd
from repositories.db_connection import DBConnection
from services.auth_service import AuthService
from services.doctor_service import DoctorService
from services.simulation_service import SimulationService
from ui.auth_view import AuthView
from ui.sidebar import SidebarView
from ui.simulation_view import SimulationView
from ui.doctor_view import DoctorView

# Inițializare bază de date SQLite
DBConnection.init_db()

# Instanțiere servicii (Business Logic Layer)
auth_service = AuthService()
doctor_service = DoctorService()
simulation_service = SimulationService()

# Setare pagină
st.set_page_config(page_title="Simulare UPU", layout="wide")

# Inițializare session state pentru autentificare
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

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
    st.rerun()

# --- BLOC AUTENTIFICARE ---
if not st.session_state.logged_in:
    AuthView.render(auth_service)

# --- BLOC APLICAȚIE AUTENTIFICATĂ ---
user_role = st.session_state.user_info.get("role", "manager")

if user_role == "manager":
    st.title("Dashboard Simulare UPU")
    st.markdown("Acest panou de control permite vizualizarea și analizarea performanțelor Unităților de Primiri Urgențe (UPU) prin simularea fluxului de pacienți.")

    # 1. Randare sidebar configurare și preluare date
    config_sidebar_data = SidebarView.render(logout)

    # 2. Configurare tab-uri principale manager
    tab_sim, tab_med = st.tabs(["Rulare & Rezultate active", "Administrare Medici"])

    with tab_sim:
        SimulationView.render(
            simulation_service=simulation_service,
            user_id=st.session_state.user_info["id"],
            config_sidebar_data=config_sidebar_data
        )

    with tab_med:
        DoctorView.render(doctor_service=doctor_service)

else:
    # --- PANOU CONTROL MEDIC ---
    st.sidebar.header("Utilizator conectat")
    st.sidebar.text(f"{st.session_state.user_info['prenume']} {st.session_state.user_info['nume']}")
    st.sidebar.text(st.session_state.user_info['email'])
    
    role_display = "Medic Urgențe" if user_role == "medic_urgente" else f"Medic Secție - {st.session_state.user_info.get('specialty', 'Nespecificat')}"
    st.sidebar.text(f"Rol: {role_display}")
    
    if st.sidebar.button("Deconectare", type="secondary", use_container_width=True):
        logout()
    st.sidebar.markdown("---")
    
    if user_role == "medic_urgente":
        st.title("Dashboard Medic Urgențe")
        st.subheader(f"Bine ați venit, Dr. {st.session_state.user_info['prenume']} {st.session_state.user_info['nume']}")
        st.info("Această secțiune este destinată medicului din Unitatea de Primiri Urgențe (UPU).")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Pacienți în Triaj & Tratament")
            st.write("Vizualizare pacienți activi în UPU. În etapa următoare a proiectului, aici veți putea decide trimiterea pacienților către secțiile de specialitate.")
            st.dataframe(pd.DataFrame({
                "Nume Pacient": ["Ionescu Maria", "Popescu Andrei", "Vasile Elena"],
                "Nivel Triaj": ["Cod Roșu", "Cod Galben", "Cod Verde"],
                "Stare": ["În tratament", "În așteptare", "Triat"]
            }), use_container_width=True)
            
        with col2:
            st.markdown("### Trimiteri active către Secții")
            st.write("Urmăriți starea trimiterilor efectuate către medicii de pe secții.")
            st.info("Nu există trimiteri active în acest moment.")
            
    elif user_role == "medic_sectie":
        spec_name = st.session_state.user_info.get('specialty', 'Nespecificat')
        st.title(f"Dashboard Medic Secție: {spec_name}")
        st.subheader(f"Bine ați venit, Dr. {st.session_state.user_info['prenume']} {st.session_state.user_info['nume']}")
        st.info(f"Această secțiune este destinată medicului de pe secția de specialitate **{spec_name}**.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Solicitări noi de internare / transfer")
            st.write("Aici veți primi propunerile de transfer din UPU, având posibilitatea de a le **Accepta** sau **Respinge**.")
            st.warning("Momentan nu aveți nicio solicitare nouă de transfer din UPU.")
            
        with col2:
            st.markdown("### Pacienți Internați pe Secție")
            st.write(f"Lista pacienților internați în prezent pe secția {spec_name}.")
            st.dataframe(pd.DataFrame({
                "Nume Pacient": ["Georgescu Dan", "Marinescu Ana"],
                "Diagnostic": ["Tratament Observație", "Investigații Suplimentare"],
                "Data Internării": ["2026-06-08", "2026-06-07"]
            }), use_container_width=True)
