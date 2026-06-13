import streamlit as st
import pandas as pd
import numpy as np
import datetime
from services.simulation_service import SimulationService
from experiments.config import SimulationConfig
from ui.charts import ChartsView

class SimulationView:
    @staticmethod
    def render(simulation_service: SimulationService, user_id: int, config_sidebar_data: dict):
        """Randează interfața principală a managerului pentru simulare, istoric și rezultate active."""
        
        # Mesaj de succes în caz de salvare recentă
        if "success_message" in st.session_state:
            st.success(st.session_state.success_message)
            del st.session_state.success_message

        st.subheader("Simulări Salvate în Istoric")
        saved_runs = simulation_service.get_user_history(user_id)
        
        with st.expander("Vizualizare Istoric Simulări", expanded=False):
            if not saved_runs:
                st.info("Nu aveți nicio simulare salvată în istoric. Rulați o simulare mai jos pentru a o salva automat.")
            else:
                run_options = {f"{r.run_name} - Salvat la {r.created_at}": r for r in saved_runs}
                selected_label = st.selectbox("Selectați o simulare salvată pentru încărcare:", list(run_options.keys()))
                
                if selected_label:
                    selected_run = run_options[selected_label]
                    
                    st.markdown("##### Detalii Configurație Simulare Selectată")
                    col_c1, col_c2, col_c3 = st.columns(3)
                    with col_c1:
                        st.metric("Medici", selected_run.num_doctors)
                        st.metric("Asistente", selected_run.num_nurses)
                        st.metric("Durată Simulare", f"{selected_run.simulation_duration} min")
                    with col_c2:
                        st.metric("Rată Sosire", f"{selected_run.arrival_rate} pacienți/oră")
                        st.metric("Replicări", selected_run.num_replications)
                        st.metric("Seed Aleator", selected_run.random_seed)
                    with col_c3:
                        st.metric("Multiplicator Ore Vârf", f"x{selected_run.peak_multiplier}")
                        st.metric("Start Vârf", f"Minutul {selected_run.peak_start_min}")
                        st.metric("Durată Vârf", f"{selected_run.peak_duration_min} min")
                    
                    # Secțiune Redenumire Simulare
                    st.markdown("##### Redenumire Simulare")
                    col_ren1, col_ren2 = st.columns([3, 1])
                    with col_ren1:
                        new_name_val = st.text_input("Nume nou", value=selected_run.run_name, key=f"rename_val_{selected_run.id}", label_visibility="collapsed")
                    with col_ren2:
                        if st.button("Redenumește", key=f"rename_btn_{selected_run.id}", use_container_width=True):
                            success_ren, msg_ren = simulation_service.rename_run(selected_run.id, user_id, new_name_val)
                            if success_ren:
                                st.success("Simularea a fost redenumită cu succes.")
                                if st.session_state.current_run_name == selected_run.run_name:
                                    st.session_state.current_run_name = new_name_val.strip()
                                st.rerun()
                            else:
                                st.error(msg_ren)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Încarcă rezultatele în grafice", key="load_run_btn", use_container_width=True, type="primary"):
                            with st.spinner("Se încarcă rezultatele..."):
                                # 1. Incarcare in session state
                                st.session_state.current_results = selected_run.results_json
                                st.session_state.current_run_name = selected_run.run_name
                                
                                # 2. Restaurare parametri in sidebar
                                st.session_state.num_doctors = selected_run.num_doctors
                                st.session_state.num_nurses = selected_run.num_nurses
                                st.session_state.arrival_rate = selected_run.arrival_rate
                                st.session_state.peak_multiplier = selected_run.peak_multiplier
                                st.session_state.peak_start = selected_run.peak_start_min
                                st.session_state.peak_duration = selected_run.peak_duration_min
                                
                                td = selected_run.triage_distribution
                                st.session_state.p_red = int(td.get(1, 0) * 100)
                                st.session_state.p_yellow = int(td.get(2, 0) * 100)
                                st.session_state.p_green = int(td.get(3, 0) * 100)
                                st.session_state.p_blue = int(td.get(4, 0) * 100)
                                st.session_state.p_white = int(td.get(5, 0) * 100)
                                
                                tt = selected_run.treatment_times
                                st.session_state.t_red = tt.get(1, [45])[0]
                                st.session_state.t_yellow = tt.get(2, [30])[0]
                                st.session_state.t_green = tt.get(3, [20])[0]
                                st.session_state.t_blue = tt.get(4, [15])[0]
                                st.session_state.t_white = tt.get(5, [10])[0]
                                
                                st.session_state.sim_duration = selected_run.simulation_duration
                                st.session_state.replications = selected_run.num_replications
                                
                                # 3. Regenerare rezultate active
                                summary = simulation_service.analyze_active_results(st.session_state.current_results)
                                st.session_state.current_summary = summary
                                
                                st.success("Rezultatele au fost încărcate cu succes!")
                                st.rerun()
                                
                    with col_btn2:
                        if st.button("Șterge această rulare din istoric", key="del_run_btn", use_container_width=True, type="secondary"):
                            success_del, msg_del = simulation_service.delete_run(selected_run.id, user_id)
                            if success_del:
                                st.success("Simularea a fost ștearsă din istoric.")
                                if st.session_state.current_run_name == selected_run.run_name:
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
            run_name_input = st.text_input("Nume Simulare", placeholder="Lăsați gol pentru nume automat cu timestamp")
        
        if st.button("Rulează Simularea", type="primary"):
            with st.spinner("Rulare experimente în progres. Vă rugăm așteptați..."):
                # Generare config folosind parametrii din sidebar
                config = SimulationConfig(
                    num_doctors=config_sidebar_data["num_doctors"],
                    num_nurses=config_sidebar_data["num_nurses"],
                    arrival_rate=config_sidebar_data["arrival_rate"],
                    peak_multiplier=config_sidebar_data["peak_multiplier"],
                    peak_start_min=config_sidebar_data["peak_start"],
                    peak_duration_min=config_sidebar_data["peak_duration"],
                    simulation_duration=config_sidebar_data["sim_duration"],
                    num_replications=config_sidebar_data["replications"],
                    triage_distribution={
                        1: config_sidebar_data["p_red"] / 100.0,
                        2: config_sidebar_data["p_yellow"] / 100.0,
                        3: config_sidebar_data["p_green"] / 100.0,
                        4: config_sidebar_data["p_blue"] / 100.0,
                        5: config_sidebar_data["p_white"] / 100.0,
                    },
                    treatment_times={
                        1: (config_sidebar_data["t_red"], max(1, int(config_sidebar_data["t_red"] * 0.3))),
                        2: (config_sidebar_data["t_yellow"], max(1, int(config_sidebar_data["t_yellow"] * 0.3))),
                        3: (config_sidebar_data["t_green"], max(1, int(config_sidebar_data["t_green"] * 0.3))),
                        4: (config_sidebar_data["t_blue"], max(1, int(config_sidebar_data["t_blue"] * 0.3))),
                        5: (config_sidebar_data["t_white"], max(1, int(config_sidebar_data["t_white"] * 0.3))),
                    }
                )
                
                # Rulare backend
                all_results = simulation_service.run_experiments(config)
                summary = simulation_service.analyze_active_results(all_results)
                
                # Determinare nume simulare
                actual_run_name = run_name_input.strip()
                if not actual_run_name:
                    actual_run_name = f"Simulare UPU - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # Salvare in baza de date
                success_db, msg_db = simulation_service.save_simulation(user_id, actual_run_name, config, all_results)
                
                # Salvare in session state
                st.session_state.current_results = all_results
                st.session_state.current_summary = summary
                st.session_state.current_run_name = actual_run_name
                
                if success_db:
                    st.session_state.success_message = "Simularea a fost salvată în istoric."
                    st.rerun()
                else:
                    st.warning(f"Simularea a fost completată, dar a apărut o eroare la salvare: {msg_db}")
                    
        st.markdown("---")
        
        # Afișare Rezultate Active
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
                st.metric("Medie Pacienți Tratați", f"{avg_total_patients:.1f}")
            with col_m2:
                st.metric("Timp Mediu Așteptare UPU", f"{avg_wait_time:.1f} min")
            with col_m3:
                st.metric("Timp Mediu Ședere", f"{avg_los:.1f} min")
            with col_m4:
                st.metric("Conformitate Timp Țintă UPU", f"{avg_compliance:.1f}%")
                
            st.markdown("---")
            
            # --- TABEL COMPARATIV CU PRAGURILE ---
            st.subheader("Analiză Timpi Așteptare vs. Praguri Maxim Admise")
            st.markdown("Comparație a timpilor medii de așteptare obținuți în simulare, raportați la limitele din protocolul național de triaj.")
            
            levels_info = []
            levels = [1, 2, 3, 4, 5]
            level_names = ["Cod Roșu", "Cod Galben", "Cod Verde", "Cod Albastru", "Cod Alb"]
            targets = [0, 15, 60, 120, 180]
            
            for lvl, name, target in zip(levels, level_names, targets):
                col_wait = f"level_{lvl}_avg_wait"
                col_comp = f"level_{lvl}_target_compliance"
                
                wait_vals = [r[col_wait] for r in results_p_fifo if col_wait in r]
                comp_vals = [r[col_comp] for r in results_p_fifo if col_comp in r]
                
                avg_wait = np.mean(wait_vals) if wait_vals else 0
                avg_comp = np.mean(comp_vals) if comp_vals else 0
                
                if target == 0:
                    status = "Conform" if avg_wait < 1.0 else "Depășit"
                else:
                    status = "Conform" if avg_wait <= target else "Depășit"
                    
                levels_info.append({
                    "Cod Triaj": name,
                    "Timp Mediu Așteptare": round(avg_wait, 2),
                    "Prag / Timp Țintă": "Imediat" if target == 0 else f"< {target} min",
                    "Rată Conformitate": f"{avg_comp:.1f}%",
                    "Status": status
                })
                
            # Construim tabelul HTML stilizat pentru rezultatele simulării
            html_rows = ""
            triage_colors = {
                "Cod Roșu": ("#ef4444", "#ffffff"),
                "Cod Galben": ("#f59e0b", "#ffffff"),
                "Cod Verde": ("#10b981", "#ffffff"),
                "Cod Albastru": ("#3b82f6", "#ffffff"),
                "Cod Alb": ("#6b7280", "#ffffff"),
            }
            
            for info in levels_info:
                name = info["Cod Triaj"]
                tr_color = triage_colors.get(name, ("#6b7280", "#ffffff"))
                triage_style = f"background-color: {tr_color[0]}; color: {tr_color[1]}; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;"
                
                if info["Status"] == "Conform":
                    status_style = "background-color: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;"
                else:
                    status_style = "background-color: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;"
                    
                html_rows += f"""<tr>
<td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.03); border-radius: 8px 0 0 8px; font-weight: 500;"><span style="{triage_style}">{name}</span></td>
<td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.03); font-weight: bold; color: #f0f2f6;">{info['Timp Mediu Așteptare']:.2f} min</td>
<td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.03); color: #a3a8b4;">{info['Prag / Timp Țintă']}</td>
<td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.03); color: #f0f2f6; font-weight: 500;">{info['Rată Conformitate']}</td>
<td style="padding: 12px 10px; background-color: rgba(255, 255, 255, 0.03); border-radius: 0 8px 8px 0;"><span style="{status_style}">{info['Status']}</span></td>
</tr>"""
                
            table_html = f"""<div style="background-color: rgba(255, 255, 255, 0.01); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); margin-top: 10px;">
<table style="width: 100%; border-collapse: separate; border-spacing: 0 6px; text-align: left; font-family: inherit;">
<thead>
<tr style="color: #a3a8b4; font-weight: 600; font-size: 0.9em;">
<th style="padding: 10px;">Cod Triaj</th>
<th style="padding: 10px;">Timp Mediu Așteptare</th>
<th style="padding: 10px;">Prag / Timp Țintă</th>
<th style="padding: 10px;">Rată Conformitate</th>
<th style="padding: 10px;">Status</th>
</tr>
</thead>
<tbody>
{html_rows}
</tbody>
</table>
</div>"""
            st.markdown(table_html, unsafe_allow_html=True)

            
            st.markdown("---")
            
            # Randare Grafice active
            ChartsView.render_all(results_p_fifo)
            
            st.markdown("---")
            
            # --- EXPORT / DOWNLOAD ---
            st.markdown("### Export Date Simulare UPU")
            st.markdown("Descărcați rezultatele simulării în format CSV.")
            try:
                results_csv_bytes = simulation_service.export_detailed_csv(st.session_state.current_results)
                summary_csv_bytes = simulation_service.export_summary_csv(st.session_state.current_results)
                
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="Descarcă Date Detaliate (CSV)",
                        data=results_csv_bytes,
                        file_name=f"{st.session_state.current_run_name.replace(' ', '_')}_detalii.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col_dl2:
                    st.download_button(
                        label="Descarcă Sumar (CSV)",
                        data=summary_csv_bytes,
                        file_name=f"{st.session_state.current_run_name.replace(' ', '_')}_sumar.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Eroare la generarea fișierelor pentru descărcare: {e}")
        else:
            st.info("Nu există rezultate active de afișat. Configurați parametrii din stânga și rulați o simulare nouă, sau alegeți o simulare salvată din istoric.")
