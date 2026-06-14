import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

class ChartsView:
    @staticmethod
    def render_all(results_p_fifo: list):
        """Randează toate cele 4 grafice din memorie într-un format de 2x2 în tab-ul principal."""
        st.subheader("Vizualizări Grafice Rezultate")
        
        # --- CALCUL METRICI UTILIZARE ---
        doc_utils = [r.get("doctor_utilization", 0) for r in results_p_fifo]
        nurse_utils = [r.get("nurse_utilization", 0) for r in results_p_fifo]
        
        avg_doc_util = np.mean(doc_utils) if doc_utils and any(doc_utils) else 0
        avg_nurse_util = np.mean(nurse_utils) if nurse_utils and any(nurse_utils) else 0
        
        # Dacă sunt 0 (simulare veche), calculăm retrospectiv folosind datele curente din session state
        if avg_doc_util == 0 and results_p_fifo:
            num_docs = st.session_state.get("num_doctors", 3)
            num_nurses = st.session_state.get("num_nurses", 2)
            duration = st.session_state.get("sim_duration", 480) - 60.0 # minus warmup
            
            tot_patients = np.mean([r["total_patients"] for r in results_p_fifo])
            avg_doc_util = min(95.0, (tot_patients * 21.0) / (num_docs * duration) * 100.0) if duration > 0 and num_docs > 0 else 0
            avg_nurse_util = min(95.0, (tot_patients * 5.0) / (num_nurses * duration) * 100.0) if duration > 0 and num_nurses > 0 else 0

        # --- RANDARE RÂNDUL 1: Aglomerare vs. Utilizare Resurse ---
        col_top1, col_top2 = st.columns(2)
        
        with col_top1:
            # 1. Grafic Evoluție aglomerare în coadă la medic
            time_data = {}
            for res in results_p_fifo:
                for log in res.get("congestion_logs", []):
                    t = log["time"]
                    if t not in time_data:
                        time_data[t] = []
                    time_data[t].append(log["doctors_queue"])
            
            times = sorted(time_data.keys())
            avg_queue = [np.mean(time_data[t]) for t in times]
            
            fig1, ax1 = plt.subplots(figsize=(8, 6))
            ax1.plot(times, avg_queue, color="#558A7A", linewidth=2.5, label="Pacienți în coadă la medic")
            ax1.set_xlabel("Timp de simulare (minute)")
            ax1.set_ylabel("Număr mediu de pacienți în coadă")
            ax1.set_title("Evoluția volumului de pacienți în coadă")
            ax1.grid(True, linestyle="--", alpha=0.5)
            ax1.legend(loc="upper left")
            plt.tight_layout()
            
            st.pyplot(fig1)
            plt.close(fig1)
            
        with col_top2:
            # 2. Grafic Utilizare Resurse (Vertical)
            fig4, ax4 = plt.subplots(figsize=(8, 6))
            resources = ["Asistente\n(Triaj)", "Medici\n(Tratament)"]
            utilizations = [avg_nurse_util, avg_doc_util]
            
            bars = ax4.bar(resources, utilizations, color=["#558A7A", "#3498DB"], edgecolor="white", width=0.4)
            ax4.set_ylabel("Grad de Utilizare")
            ax4.set_ylim(0, 105)
            ax4.set_title("Gradul mediu de utilizare a resurselor")
            ax4.grid(True, linestyle="--", alpha=0.5)
            
            # Adăugare etichete pe bare
            for bar in bars:
                height = bar.get_height()
                ax4.annotate(f'{height:.1f}%',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=10, weight="bold")
                            
            plt.tight_layout()
            st.pyplot(fig4)
            plt.close(fig4)

        st.markdown("---")

        # --- RANDARE RÂNDUL 2: Așteptare vs. Prag și Conformitate ---
        col_g1, col_g2 = st.columns(2)
        levels = [1, 2, 3, 4, 5]
        short_names = ["Roșu", "Galben", "Verde", "Albastru", "Alb"]
        targets = [0, 15, 60, 120, 180]
        
        with col_g1:
            # 3. Grafic Timp mediu de așteptare vs. Prag
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            x = np.arange(len(levels))
            width = 0.35
            
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
            ax2.set_title("Timp Mediu de Așteptare vs. Timp Țintă")
            ax2.legend()
            ax2.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
            
            st.pyplot(fig2)
            plt.close(fig2)
            
        with col_g2:
            # 4. Grafic Rata conformitate per nivel
            fig3, ax3 = plt.subplots(figsize=(8, 6))
            compliance_rates = []
            for lvl in levels:
                col_comp = f"level_{lvl}_target_compliance"
                comp_vals = [r[col_comp] for r in results_p_fifo if col_comp in r]
                compliance_rates.append(np.mean(comp_vals) if comp_vals else 0)
            
            colors = ["#C25953", "#D4AC0D", "#52BE80", "#5DADE2", "#BDC3C7"]
            bars = ax3.bar(short_names, compliance_rates, color=colors, edgecolor="white", width=0.5)
            ax3.set_ylabel("Procent Conformitate")
            ax3.set_title("Rata de conformitate cu timpul țintă")
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
