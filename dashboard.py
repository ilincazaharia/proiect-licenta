import streamlit as st
import pandas as pd
import os
import datetime
import matplotlib.pyplot as plt
import numpy as np
from experiments.config import SimulationConfig
from experiments.runner import run_all_experiments
from experiments.analysis import analyze_results
from auth.db import register_user, verify_user, save_simulation_run, get_user_simulation_runs, delete_simulation_run, get_all_specialties, get_all_doctors, delete_doctor

# Setare pagina
st.set_page_config(page_title="Simulare UPU", layout="wide")

# Initializare session state pentru autentificare
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# Initializare session state pentru rezultate active
if "current_results" not in st.session_state:
    st.session_state.current_results = None
if "current_summary" not in st.session_state:
    st.session_state.current_summary = None
if "current_run_name" not in st.session_state:
    st.session_state.current_run_name = None

# Initializare parametri in session state
if "num_doctors" not in st.session_state: st.session_state.num_doctors = 10
if "num_nurses" not in st.session_state: st.session_state.num_nurses = 20
if "arrival_rate" not in st.session_state: st.session_state.arrival_rate = 12.0
if "peak_multiplier" not in st.session_state: st.session_state.peak_multiplier = 2.0
if "peak_start" not in st.session_state: st.session_state.peak_start = 120
if "peak_duration" not in st.session_state: st.session_state.peak_duration = 120
if "p_red" not in st.session_state: st.session_state.p_red = 5
if "p_yellow" not in st.session_state: st.session_state.p_yellow = 15
if "p_green" not in st.session_state: st.session_state.p_green = 30
if "p_blue" not in st.session_state: st.session_state.p_blue = 35
if "p_white" not in st.session_state: st.session_state.p_white = 15
if "t_red" not in st.session_state: st.session_state.t_red = 45
if "t_yellow" not in st.session_state: st.session_state.t_yellow = 30
if "t_green" not in st.session_state: st.session_state.t_green = 20
if "t_blue" not in st.session_state: st.session_state.t_blue = 15
if "t_white" not in st.session_state: st.session_state.t_white = 10
if "sim_duration" not in st.session_state: st.session_state.sim_duration = 480
if "replications" not in st.session_state: st.session_state.replications = 30

# Deconectare
def logout():
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.rerun()

# Interfata de autentificare (Conectare / Inregistrare)
if not st.session_state.logged_in:
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
                        success, user_info = verify_user(email, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user_info = user_info
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
                        success, message = register_user(nume, prenume, email_reg, password_reg)
                        if success:
                            st.success("Contul a fost creat cu succes. Va puteti conecta din tab-ul Conectare.")
                        else:
                            st.error(message)
    st.stop()

# --- MAIN PAGE SETUP ---
# Preluam rolul din datele de conectare
user_role = st.session_state.user_info.get("role", "manager")

if user_role == "manager":
    # --- PANOU CONTROL MANAGER ---
    st.title("Dashboard Simulare UPU (Manager)")
    st.markdown("Acest panou de control permite compararea diferitelor strategii de gestionare a pacienților în Unitățile de Primiri Urgențe (UPU), pe baza parametrilor configurabili.")

    # --- SIDEBAR CONFIGURARE ---
    st.sidebar.header("Utilizator conectat")
    st.sidebar.text(f"{st.session_state.user_info['prenume']} {st.session_state.user_info['nume']}")
    st.sidebar.text(st.session_state.user_info['email'])
    st.sidebar.text("Rol: Manager")
    if st.sidebar.button("Deconectare", type="secondary", use_container_width=True):
        logout()
    st.sidebar.markdown("---")

    st.sidebar.header("Configurare Parametri")

    st.sidebar.subheader("Resurse Umane")
    num_doctors = st.sidebar.number_input("Număr Medici", min_value=1, value=int(st.session_state.num_doctors), step=1)
    st.session_state.num_doctors = num_doctors

    num_nurses = st.sidebar.number_input("Număr Asistente", min_value=1, value=int(st.session_state.num_nurses), step=1)
    st.session_state.num_nurses = num_nurses

    st.sidebar.subheader("Flux Pacienți")
    arrival_rate = st.sidebar.number_input("Rata de sosire (pacienți/oră)", min_value=1.0, value=float(st.session_state.arrival_rate), step=1.0)
    st.session_state.arrival_rate = arrival_rate

    st.sidebar.subheader("Ore de Vârf (Flux Dinamic)")
    peak_multiplier = st.sidebar.number_input("Multiplicator rată sosire (x)", min_value=1.0, max_value=5.0, value=float(st.session_state.peak_multiplier), step=0.1)
    st.session_state.peak_multiplier = peak_multiplier

    peak_start = st.sidebar.number_input("Început oră de vârf (minutul)", min_value=0, value=int(st.session_state.peak_start), step=30)
    st.session_state.peak_start = peak_start

    peak_duration = st.sidebar.number_input("Durată oră de vârf (minute)", min_value=0, value=int(st.session_state.peak_duration), step=30)
    st.session_state.peak_duration = peak_duration

    st.sidebar.subheader("Distribuție Triaj (%)")
    st.sidebar.markdown("Suma valorilor trebuie să fie 100%.")
    col_p1, col_p2 = st.sidebar.columns(2)
    with col_p1:
        p_red = st.number_input("Cod Roșu", min_value=0, max_value=100, value=int(st.session_state.p_red), step=1)
        st.session_state.p_red = p_red
        p_yellow = st.number_input("Cod Galben", min_value=0, max_value=100, value=int(st.session_state.p_yellow), step=1)
        st.session_state.p_yellow = p_yellow
        p_green = st.number_input("Cod Verde", min_value=0, max_value=100, value=int(st.session_state.p_green), step=1)
        st.session_state.p_green = p_green
    with col_p2:
        p_blue = st.number_input("Cod Albastru", min_value=0, max_value=100, value=int(st.session_state.p_blue), step=1)
        st.session_state.p_blue = p_blue
        p_white = st.number_input("Cod Alb", min_value=0, max_value=100, value=int(st.session_state.p_white), step=1)
        st.session_state.p_white = p_white

    total_p = p_red + p_yellow + p_green + p_blue + p_white
    if total_p != 100:
        st.sidebar.error(f"Atenție: Suma procentelor este {total_p}%. Ajustați valorile pentru a atinge 100%.")

    st.sidebar.subheader("Timpi Medii Tratament (minute)")
    t_red = st.sidebar.number_input("Timp Cod Roșu", min_value=1, value=int(st.session_state.t_red), step=5)
    st.session_state.t_red = t_red
    t_yellow = st.sidebar.number_input("Timp Cod Galben", min_value=1, value=int(st.session_state.t_yellow), step=5)
    st.session_state.t_yellow = t_yellow
    t_green = st.sidebar.number_input("Timp Cod Verde", min_value=1, value=int(st.session_state.t_green), step=5)
    st.session_state.t_green = t_green
    t_blue = st.sidebar.number_input("Timp Cod Albastru", min_value=1, value=int(st.session_state.t_blue), step=5)
    st.session_state.t_blue = t_blue
    t_white = st.sidebar.number_input("Timp Cod Alb", min_value=1, value=int(st.session_state.t_white), step=5)
    st.session_state.t_white = t_white

    st.sidebar.subheader("Parametri Simulare")
    sim_duration = st.sidebar.number_input("Durata simulare (minute)", min_value=60, value=int(st.session_state.sim_duration), step=60)
    st.session_state.sim_duration = sim_duration
    replications = st.sidebar.number_input("Număr replicări", min_value=1, value=int(st.session_state.replications), step=1)
    st.session_state.replications = replications

    # --- TABS SETUP FOR MANAGER ---
    tab_sim, tab_med = st.tabs(["Rulare & Rezultate active", "Administrare Medici"])

    with tab_sim:
        # --- SECȚIUNE ISTORIC INTEGRATĂ ---
        st.subheader("Simulări Salvate în Istoric")
        user_id = st.session_state.user_info["id"]
        saved_runs = get_user_simulation_runs(user_id)
        
        with st.expander("📂 Vizualizare Istoric Simulări (Încărcare / Gestiune)", expanded=False):
            if not saved_runs:
                st.info("Nu aveți nicio simulare salvată în istoric. Rulați o simulare mai jos pentru a o salva automat.")
            else:
                run_options = {f"{r['run_name']} (Salvat la: {r['created_at']})": r for r in saved_runs}
                selected_label = st.selectbox("Selectați o simulare salvată pentru încărcare:", list(run_options.keys()))
                
                if selected_label:
                    selected_run = run_options[selected_label]
                    
                    st.markdown("##### Detalii Configurație Simulare Selectată")
                    col_c1, col_c2, col_c3 = st.columns(3)
                    with col_c1:
                        st.metric("Medici", selected_run["num_doctors"])
                        st.metric("Asistente", selected_run["num_nurses"])
                        st.metric("Durată Simulare", f"{selected_run['simulation_duration']} min")
                    with col_c2:
                        st.metric("Rată Sosire (pacienți/oră)", selected_run["arrival_rate"])
                        st.metric("Replicări", selected_run["num_replications"])
                        st.metric("Seed Aleator", selected_run["random_seed"])
                    with col_c3:
                        st.metric("Multiplicator Ore Vârf", f"x{selected_run['peak_multiplier']}")
                        st.metric("Start Vârf", f"Minutul {selected_run['peak_start_min']}")
                        st.metric("Durată Vârf", f"{selected_run['peak_duration_min']} min")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("🔄 Încarcă rezultatele în grafice", key="load_run_btn", use_container_width=True, type="primary"):
                            with st.spinner("Se încarcă rezultatele..."):
                                # 1. Incarcare in session state
                                st.session_state.current_results = selected_run["results_json"]
                                st.session_state.current_run_name = selected_run["run_name"]
                                
                                # 2. Restaurare parametri in sidebar
                                st.session_state.num_doctors = selected_run["num_doctors"]
                                st.session_state.num_nurses = selected_run["num_nurses"]
                                st.session_state.arrival_rate = selected_run["arrival_rate"]
                                st.session_state.peak_multiplier = selected_run["peak_multiplier"]
                                st.session_state.peak_start = selected_run["peak_start_min"]
                                st.session_state.peak_duration = selected_run["peak_duration_min"]
                                
                                td = selected_run["triage_distribution"]
                                st.session_state.p_red = int(td.get(1, 0) * 100)
                                st.session_state.p_yellow = int(td.get(2, 0) * 100)
                                st.session_state.p_green = int(td.get(3, 0) * 100)
                                st.session_state.p_blue = int(td.get(4, 0) * 100)
                                st.session_state.p_white = int(td.get(5, 0) * 100)
                                
                                tt = selected_run["treatment_times"]
                                st.session_state.t_red = tt.get(1, [45])[0]
                                st.session_state.t_yellow = tt.get(2, [30])[0]
                                st.session_state.t_green = tt.get(3, [20])[0]
                                st.session_state.t_blue = tt.get(4, [15])[0]
                                st.session_state.t_white = tt.get(5, [10])[0]
                                
                                st.session_state.sim_duration = selected_run["simulation_duration"]
                                st.session_state.replications = selected_run["num_replications"]
                                
                                # 3. Regenerare rezultate comparative pe disc
                                summary = analyze_results(st.session_state.current_results, output_dir="results")
                                st.session_state.current_summary = summary
                                
                                st.success("Rezultatele au fost încărcate în grafice cu succes!")
                                st.rerun()
                                
                    with col_btn2:
                        if st.button("🗑️ Șterge această rulare din istoric", key="del_run_btn", use_container_width=True, type="secondary"):
                            success_del, msg_del = delete_simulation_run(selected_run["id"], user_id)
                            if success_del:
                                st.success("Simularea a fost ștearsă din istoric.")
                                if st.session_state.current_run_name == selected_run["run_name"]:
                                    st.session_state.current_results = None
                                    st.session_state.current_summary = None
                                    st.session_state.current_run_name = None
                                st.rerun()
                            else:
                                st.error(f"Eroare la ștergerea simulării: {msg_del}")

        st.markdown("---")
        st.subheader("Rulare Simulare Nouă")
        
        col_name1, col_name2 = st.columns([2, 1])
        with col_name1:
            run_name_input = st.text_input("Nume Simulare (opțional)", placeholder="Lăsați gol pentru nume automat cu timestamp")
        
        if st.button("Rulează Simularea", type="primary", disabled=(total_p != 100)):
            with st.spinner("Rulare experimente în progres. Vă rugăm așteptați..."):
                # Generare config
                config = SimulationConfig(
                    num_doctors=num_doctors,
                    num_nurses=num_nurses,
                    arrival_rate=arrival_rate,
                    peak_multiplier=peak_multiplier,
                    peak_start_min=peak_start,
                    peak_duration_min=peak_duration,
                    simulation_duration=sim_duration,
                    num_replications=replications,
                    triage_distribution={
                        1: p_red / 100.0,
                        2: p_yellow / 100.0,
                        3: p_green / 100.0,
                        4: p_blue / 100.0,
                        5: p_white / 100.0,
                    },
                    treatment_times={
                        1: (t_red, max(1, int(t_red * 0.3))),
                        2: (t_yellow, max(1, int(t_yellow * 0.3))),
                        3: (t_green, max(1, int(t_green * 0.3))),
                        4: (t_blue, max(1, int(t_blue * 0.3))),
                        5: (t_white, max(1, int(t_white * 0.3))),
                    }
                )
                
                # Rulare backend
                all_results = run_all_experiments(config)
                summary = analyze_results(all_results, output_dir="results")
                
                # Determinare nume simulare
                actual_run_name = run_name_input.strip()
                if not actual_run_name:
                    actual_run_name = f"Simulare UPU - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # Salvare in baza de date
                success_db, msg_db = save_simulation_run(user_id, actual_run_name, config, all_results)
                
                # Salvare in session state
                st.session_state.current_results = all_results
                st.session_state.current_summary = summary
                st.session_state.current_run_name = actual_run_name
                
                if success_db:
                    st.success(f"Simularea '{actual_run_name}' a fost completată și salvată în baza de date cu succes.")
                else:
                    st.warning(f"Simularea a fost completată, dar a apărut o eroare la salvare: {msg_db}")
                    
        st.markdown("---")
        
        # Afisare Rezultate active
        if st.session_state.current_results is not None:
            # Filtram exclusiv rezultatele obtinute pentru strategia Priority + FIFO
            results_p_fifo = [r for r in st.session_state.current_results if r["strategy"] == "Priority + FIFO"]
            
            st.subheader(f"Rezultate Simulare Curentă: {st.session_state.current_run_name}")
            
            # --- KPIs ---
            avg_total_patients = np.mean([r["total_patients"] for r in results_p_fifo])
            avg_wait_time = np.mean([r["avg_waiting_time"] for r in results_p_fifo])
            avg_los = np.mean([r["avg_los"] for r in results_p_fifo])
            avg_compliance = np.mean([r["target_compliance"] for r in results_p_fifo])
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Total Pacienți Tratați (Medie)", f"{avg_total_patients:.1f}")
            with col_m2:
                st.metric("Timp Mediu Așteptare UPU", f"{avg_wait_time:.1f} min")
            with col_m3:
                st.metric("Timp Mediu Ședere (LOS)", f"{avg_los:.1f} min")
            with col_m4:
                st.metric("Conformitate Timp Țintă UPU", f"{avg_compliance:.1f}%")
                
            st.markdown("---")
            
            # --- TABEL COMPARATIV CU PRAGURILE ---
            st.subheader("Analiză Timpi Așteptare vs. Praguri Maxim Admise (Timp Țintă)")
            st.markdown("Comparație detaliată a timpilor medii de așteptare obținuți în simulare, raportați la limitele din protocolul național de triaj.")
            
            levels_info = []
            levels = [1, 2, 3, 4, 5]
            level_names = ["Cod Roșu (Resuscitare - Nivel 1)", "Cod Galben (Critic - Nivel 2)", "Cod Verde (Urgent - Nivel 3)", "Cod Albastru (Non-urgent - Nivel 4)", "Cod Alb (Consult - Nivel 5)"]
            targets = [0, 15, 60, 120, 180]
            
            for lvl, name, target in zip(levels, level_names, targets):
                col_wait = f"level_{lvl}_avg_wait"
                col_comp = f"level_{lvl}_target_compliance"
                
                wait_vals = [r[col_wait] for r in results_p_fifo if col_wait in r]
                comp_vals = [r[col_comp] for r in results_p_fifo if col_comp in r]
                
                avg_wait = np.mean(wait_vals) if wait_vals else 0
                avg_comp = np.mean(comp_vals) if comp_vals else 0
                
                if target == 0:
                    status = "✅ Conform" if avg_wait < 1.0 else "❌ Depășit"
                else:
                    status = "✅ Conform" if avg_wait <= target else "❌ Depășit"
                    
                levels_info.append({
                    "Cod Triaj (Nivel)": name,
                    "Timp Mediu Așteptare (min)": round(avg_wait, 2),
                    "Prag / Timp Țintă (min)": f"Imediat (0)" if target == 0 else f"< {target} min",
                    "Rată Conformitate (%)": f"{avg_comp:.1f}%",
                    "Status": status
                })
                
            st.dataframe(pd.DataFrame(levels_info), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("Vizualizări Grafice Rezultate")
            
            # Desenare Grafic 1: Evolutia volumului de pacienti in coada (Aglomerarea in timp)
            time_data = {}
            for res in results_p_fifo:
                for log in res.get("congestion_logs", []):
                    t = log["time"]
                    if t not in time_data:
                        time_data[t] = []
                    time_data[t].append(log["doctors_queue"])
            
            times = sorted(time_data.keys())
            avg_queue = [np.mean(time_data[t]) for t in times]
            
            fig1, ax1 = plt.subplots(figsize=(10, 4.2))
            ax1.plot(times, avg_queue, color="#558A7A", linewidth=2.5, label="Pacienți în coadă la medic")
            ax1.set_xlabel("Timp de simulare (minute)")
            ax1.set_ylabel("Număr mediu de pacienți în coadă")
            ax1.set_title("Evoluția volumului de pacienți în coadă (Aglomerarea în timp)")
            ax1.grid(True, linestyle="--", alpha=0.5)
            ax1.legend(loc="upper left")
            plt.tight_layout()
            
            st.pyplot(fig1)
            plt.close(fig1)
            
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                # Desenare Grafic 2: Timp mediu de asteptare vs. Prag
                fig2, ax2 = plt.subplots(figsize=(8, 6))
                x = np.arange(len(levels))
                width = 0.35
                
                short_names = ["Rosu (1)", "Galben (2)", "Verde (3)", "Albastru (4)", "Alb (5)"]
                
                avg_waits = []
                for lvl in levels:
                    col_wait = f"level_{lvl}_avg_wait"
                    wait_vals = [r[col_wait] for r in results_p_fifo if col_wait in r]
                    avg_waits.append(np.mean(wait_vals) if wait_vals else 0)
                
                ax2.bar(x - width/2, avg_waits, width, label="Timp Mediu Simulat", color="#558A7A", edgecolor="white")
                ax2.bar(x + width/2, targets, width, label="Prag Timp Țintă", color="#BDC3C7", edgecolor="white")
                
                ax2.set_xticks(x)
                ax2.set_xticklabels(short_names)
                ax2.set_ylabel("Minute")
                ax2.set_title("Timp Mediu de Așteptare vs. Prag legal de triaj")
                ax2.legend()
                ax2.grid(True, linestyle="--", alpha=0.5)
                plt.tight_layout()
                
                st.pyplot(fig2)
                plt.close(fig2)
                
            with col_g2:
                # Desenare Grafic 3: Rata conformitate per nivel
                fig3, ax3 = plt.subplots(figsize=(8, 6))
                compliance_rates = []
                for lvl in levels:
                    col_comp = f"level_{lvl}_target_compliance"
                    comp_vals = [r[col_comp] for r in results_p_fifo if col_comp in r]
                    compliance_rates.append(np.mean(comp_vals) if comp_vals else 0)
                
                colors = ["#C25953", "#D4AC0D", "#52BE80", "#5DADE2", "#BDC3C7"]
                bars = ax3.bar(short_names, compliance_rates, color=colors, edgecolor="white", width=0.5)
                ax3.set_ylabel("Procent Conformitate (%)")
                ax3.set_title("Rata de conformitate cu timpul țintă (%)")
                ax3.set_ylim(0, 105)
                
                for bar in bars:
                    height = bar.get_height()
                    ax3.annotate(f'{height:.1f}%',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9)
                ax3.grid(True, linestyle="--", alpha=0.5)
                plt.tight_layout()
                
                st.pyplot(fig3)
                plt.close(fig3)
                
            st.markdown("---")
            # --- EXPORT / DOWNLOAD ---
            st.markdown("### Export Date Simulare UPU")
            st.markdown("Descărcați rezultatele complete (conțin datele pentru toate strategiile simulate pentru a le folosi în analizele comparative).")
            try:
                with open("results/results.csv", "rb") as f:
                    results_csv_data = f.read()
                with open("results/summary.csv", "rb") as f:
                    summary_csv_data = f.read()
                
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="📥 Descarcă Date Detaliate (Toate Strategiile - CSV)",
                        data=results_csv_data,
                        file_name=f"{st.session_state.current_run_name.replace(' ', '_')}_toate_detaliile.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col_dl2:
                    st.download_button(
                        label="📊 Descarcă Sumar (Toate Strategiile - CSV)",
                        data=summary_csv_data,
                        file_name=f"{st.session_state.current_run_name.replace(' ', '_')}_toate_sumar.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Eroare la încărcarea fișierelor pentru descărcare: {e}")
        else:
            st.info("Nu există rezultate active de afișat. Configurați parametrii din stânga și rulați o simulare nouă, sau alegeți o simulare salvată din istoric.")

    with tab_med:
        st.subheader("Administrare Conturi Medici")
        st.markdown("Creați noi conturi de medici pentru Urgențe sau Secții de specialitate și gestionați conturile existente.")
        
        # Formular Creare Cont
        with st.form("creare_cont_medic", clear_on_submit=True):
            st.write("#### Date Medic Nou")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                m_nume = st.text_input("Nume de familie")
                m_prenume = st.text_input("Prenume")
                m_email = st.text_input("Adresă Email")
            with col_m2:
                m_password = st.text_input("Parolă (minim 6 caractere)", type="password")
                m_role_sel = st.selectbox("Tip Medic / Rol", ["Medic Urgențe", "Medic Secție"])
                
                # Citire specializari din DB
                specialties = get_all_specialties()
                spec_options = {s["name"]: s["id"] for s in specialties}
                m_spec_sel = st.selectbox("Specializare (doar pentru Medic Secție)", list(spec_options.keys()))
                
            submit_medic = st.form_submit_button("Creează Cont Medic", use_container_width=True)
            
            if submit_medic:
                if not m_nume or not m_prenume or not m_email or not m_password:
                    st.error("Toate câmpurile sunt obligatorii.")
                elif len(m_password) < 6:
                    st.error("Parola trebuie să aibă cel puțin 6 caractere.")
                else:
                    target_role = "medic_urgente" if m_role_sel == "Medic Urgențe" else "medic_sectie"
                    target_spec_id = spec_options[m_spec_sel] if target_role == "medic_sectie" else None
                    
                    success_reg, msg_reg = register_user(
                        nume=m_nume,
                        prenume=m_prenume,
                        email=m_email,
                        password=m_password,
                        role=target_role,
                        specialty_id=target_spec_id
                    )
                    
                    if success_reg:
                        st.success(f"Contul medicului Dr. {m_prenume} {m_nume} ({m_role_sel}) a fost creat cu succes.")
                    else:
                        st.error(f"Eroare la crearea contului: {msg_reg}")
                        
        st.markdown("---")
        st.write("#### Conturi Medici Înregistrați")
        
        doctors = get_all_doctors()
        if not doctors:
            st.info("Nu există medici înregistrați în baza de date.")
        else:
            for doc in doctors:
                role_label = "Medic Urgențe" if doc["role"] == "medic_urgente" else f"Medic Secție ({doc['specialty']})"
                col_d1, col_d2, col_d3 = st.columns([3, 2, 1])
                with col_d1:
                    st.write(f"**Dr. {doc['prenume']} {doc['nume']}** ({doc['email']})")
                with col_d2:
                    st.write(role_label)
                with col_d3:
                    if st.button("Șterge", key=f"del_doc_{doc['id']}", type="secondary", use_container_width=True):
                        success_del, msg_del = delete_doctor(doc["id"])
                        if success_del:
                            st.success("Cont șters!")
                            st.rerun()
                        else:
                            st.error(msg_del)

else:
    # --- PANOU CONTROL MEDIC ---
    # Ecrane placeholder specifice pentru Medic Urgențe și Medic Secție
    st.sidebar.header("Utilizator conectat")
    st.sidebar.text(f"{st.session_state.user_info['prenume']} {st.session_state.user_info['nume']}")
    st.sidebar.text(st.session_state.user_info['email'])
    
    role_display = "Medic Urgențe" if user_role == "medic_urgente" else f"Medic Secție ({st.session_state.user_info.get('specialty', 'Nespecificat')})"
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
                "Nivel Triaj": ["Cod Roșu (1)", "Cod Galben (2)", "Cod Verde (3)"],
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
