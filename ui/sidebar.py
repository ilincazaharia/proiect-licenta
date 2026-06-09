import streamlit as st

class SidebarView:
    @staticmethod
    def render(logout_callback) -> dict:
        """Randează sidebar-ul cu utilizatorul conectat și parametrii de configurare."""
        st.sidebar.header("Utilizator conectat")
        st.sidebar.text(f"{st.session_state.user_info['prenume']} {st.session_state.user_info['nume']}")
        st.sidebar.text(st.session_state.user_info['email'])
        
        role_label = "Manager" if st.session_state.user_info['role'] == 'manager' else "Medic"
        st.sidebar.text(f"Rol: {role_label}")
        
        if st.sidebar.button("Deconectare", type="secondary", use_container_width=True):
            logout_callback()
        st.sidebar.markdown("---")
 
        st.sidebar.header("Configurare Parametri")
        
        st.sidebar.subheader("Resurse Umane")
        with st.sidebar.container(border=True):
            num_doctors = st.number_input("Număr Medici", min_value=1, value=int(st.session_state.num_doctors), step=1)
            st.session_state.num_doctors = num_doctors
     
            num_nurses = st.number_input("Număr Asistente", min_value=1, value=int(st.session_state.num_nurses), step=1)
            st.session_state.num_nurses = num_nurses
     
        st.sidebar.subheader("Flux Pacienți")
        with st.sidebar.container(border=True):
            arrival_rate = st.number_input("Rata de sosire în pacienți pe oră", min_value=1.0, value=float(st.session_state.arrival_rate), step=1.0)
            st.session_state.arrival_rate = arrival_rate
     
            st.markdown("**Ore de Vârf**")
            peak_multiplier = st.number_input("Multiplicator rată sosire", min_value=1.0, max_value=5.0, value=float(st.session_state.peak_multiplier), step=0.1)
            st.session_state.peak_multiplier = peak_multiplier
     
            peak_start = st.number_input("Început oră de vârf la minutul", min_value=0, value=int(st.session_state.peak_start), step=30)
            st.session_state.peak_start = peak_start
     
            peak_duration = st.number_input("Durată oră de vârf în minute", min_value=0, value=int(st.session_state.peak_duration), step=30)
            st.session_state.peak_duration = peak_duration
     
        st.sidebar.subheader("Distribuție Coduri Triaj")
        with st.sidebar.container(border=True):
            st.markdown('<span style="color:#D32F2F; font-weight:bold;">■ Cod Roșu (Nivel 1)</span>', unsafe_allow_html=True)
            p_red = st.slider(
                "Procent Cod Roșu", 
                min_value=0, 
                max_value=100, 
                value=int(st.session_state.p_red),
                key="slider_p_red",
                label_visibility="collapsed"
            )
            st.session_state.p_red = p_red
     
            max_yellow = 100 - p_red
            st.markdown(f'<span style="color:#F39C12; font-weight:bold;">■ Cod Galben (Nivel 2)</span> (Maxim: {max_yellow}%)', unsafe_allow_html=True)
            val_yellow = min(int(st.session_state.p_yellow), max_yellow)
            p_yellow = st.slider(
                "Procent Cod Galben", 
                min_value=0, 
                max_value=max_yellow, 
                value=val_yellow,
                key="slider_p_yellow",
                label_visibility="collapsed"
            )
            st.session_state.p_yellow = p_yellow
     
            max_green = 100 - p_red - p_yellow
            st.markdown(f'<span style="color:#2ECC71; font-weight:bold;">■ Cod Verde (Nivel 3)</span> (Maxim: {max_green}%)', unsafe_allow_html=True)
            val_green = min(int(st.session_state.p_green), max_green)
            p_green = st.slider(
                "Procent Cod Verde", 
                min_value=0, 
                max_value=max_green, 
                value=val_green,
                key="slider_p_green",
                label_visibility="collapsed"
            )
            st.session_state.p_green = p_green
     
            max_blue = 100 - p_red - p_yellow - p_green
            st.markdown(f'<span style="color:#3498DB; font-weight:bold;">■ Cod Albastru (Nivel 4)</span> (Maxim: {max_blue}%)', unsafe_allow_html=True)
            val_blue = min(int(st.session_state.p_blue), max_blue)
            p_blue = st.slider(
                "Procent Cod Albastru", 
                min_value=0, 
                max_value=max_blue, 
                value=val_blue,
                key="slider_p_blue",
                label_visibility="collapsed"
            )
            st.session_state.p_blue = p_blue
     
            p_white = 100 - p_red - p_yellow - p_green - p_blue
            st.session_state.p_white = p_white
            st.markdown(f'<span style="color:#BDC3C7; font-weight:bold;">■ Cod Alb (Nivel 5)</span>: **{p_white}%**', unsafe_allow_html=True)
     
        st.sidebar.subheader("Timpi Medii Tratament")
        with st.sidebar.container(border=True):
            st.markdown('<span style="color:#D32F2F; font-weight:bold;">■ Timp Cod Roșu</span>', unsafe_allow_html=True)
            t_red = st.number_input("Timp Roșu", min_value=1, value=int(st.session_state.t_red), step=5, label_visibility="collapsed")
            st.session_state.t_red = t_red
     
            st.markdown('<span style="color:#F39C12; font-weight:bold;">■ Timp Cod Galben</span>', unsafe_allow_html=True)
            t_yellow = st.number_input("Timp Galben", min_value=1, value=int(st.session_state.t_yellow), step=5, label_visibility="collapsed")
            st.session_state.t_yellow = t_yellow
     
            st.markdown('<span style="color:#2ECC71; font-weight:bold;">■ Timp Cod Verde</span>', unsafe_allow_html=True)
            t_green = st.number_input("Timp Verde", min_value=1, value=int(st.session_state.t_green), step=5, label_visibility="collapsed")
            st.session_state.t_green = t_green
     
            st.markdown('<span style="color:#3498DB; font-weight:bold;">■ Timp Cod Albastru</span>', unsafe_allow_html=True)
            t_blue = st.number_input("Timp Albastru", min_value=1, value=int(st.session_state.t_blue), step=5, label_visibility="collapsed")
            st.session_state.t_blue = t_blue
     
            st.markdown('<span style="color:#BDC3C7; font-weight:bold;">■ Timp Cod Alb</span>', unsafe_allow_html=True)
            t_white = st.number_input("Timp Alb", min_value=1, value=int(st.session_state.t_white), step=5, label_visibility="collapsed")
            st.session_state.t_white = t_white
     
        st.sidebar.subheader("Parametri Simulare")
        with st.sidebar.container(border=True):
            sim_duration = st.number_input("Durata simulare în minute", min_value=60, value=int(st.session_state.sim_duration), step=60)
            st.session_state.sim_duration = sim_duration
            replications = st.number_input("Număr replicări", min_value=1, value=int(st.session_state.replications), step=1)
            st.session_state.replications = replications

        return {
            "num_doctors": num_doctors,
            "num_nurses": num_nurses,
            "arrival_rate": arrival_rate,
            "peak_multiplier": peak_multiplier,
            "peak_start": peak_start,
            "peak_duration": peak_duration,
            "p_red": p_red,
            "p_yellow": p_yellow,
            "p_green": p_green,
            "p_blue": p_blue,
            "p_white": p_white,
            "t_red": t_red,
            "t_yellow": t_yellow,
            "t_green": t_green,
            "t_blue": t_blue,
            "t_white": t_white,
            "sim_duration": sim_duration,
            "replications": replications,
        }
