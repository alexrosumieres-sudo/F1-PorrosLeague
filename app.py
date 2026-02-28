import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. CONFIGURACIONES BÁSICAS
PILOTOS_2026 = sorted([
    "Norris", "Piastri", "Antonelli", "Russell", "Verstappen", "Hadjar",
    "Leclerc", "Hamilton", "Albon", "Sainz Jr.", "Lawson", "Lindblad",
    "Alonso", "Stroll", "Ocon", "Bearman", "Bortoleto", "Hülkenberg",
    "Gasly", "Colapinto", "Perez", "Bottas"
])

EQUIPOS_2026 = sorted([
    "McLaren", "Mercedes", "Red Bull", "Ferrari", "Williams", 
    "Racing Bulls", "Aston Martin", "Haas", "Audi", "Alpine", "Cadillac"
])

GPS = [
    "01. GP de Australia", "02. GP de China", "03. GP de Japón", "04. GP de Baréin",
    "05. GP de Arabia Saudita", "06. GP de Miami", "07. GP de Canadá", "08. GP de Mónaco",
    "09. GP de Barcelona-Cataluña", "10. GP de Austria", "11. GP de Gran Bretaña", "12. GP de Bélgica",
    "13. GP de Hungría", "14. GP de los Países Bajos", "15. GP de Italia", "16. GP de España (Madrid)",
    "17. GP de Azerbaiyán", "18. GP de Singapur", "19. GP de Estados Unidos", "20. GP de Ciudad de México",
    "21. GP de São Paulo", "22. GP de Las Vegas", "23. GP de Catar", "24. GP de Abu Dabi"
]

# --- CONFIGURACIÓN VISUAL F1 ---
EQUIPOS_DATA = {
    "McLaren": {"emoji": "🟠", "color": "#FF8000", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/mclaren-logo.png"},
    "Ferrari": {"emoji": "🔴", "color": "#E80020", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/ferrari-logo.png"},
    "Mercedes": {"emoji": "⚪", "color": "#27F4D2", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/mercedes-logo.png"},
    "Aston Martin": {"emoji": "🟢", "color": "#229971", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/aston-martin-logo.png"},
    "Red Bull": {"emoji": "🔵", "color": "#3671C6", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/red-bull-racing-logo.png"},
    "Williams": {"emoji": "🔵", "color": "#64C4FF", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/williams-logo.png"},
    "Racing Bulls": {"emoji": "🔵", "color": "#6692FF", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/rb-logo.png"},
    "Haas": {"emoji": "⚪", "color": "#B6BABD", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/haas-f1-team-logo.png"},
    "Alpine": {"emoji": "🔵", "color": "#0093CC", "logo": "https://www.formula1.com/content/dam/fom-website/teams/2024/alpine-logo.png"},
    "Audi": {"emoji": "🔘", "color": "#F50A25", "logo": "data:image/jpeg;base64,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"},
    "Cadillac": {"emoji": "🟡", "color": "#FFD700", "logo": "https://media.formula1.com/image/upload/c_lfill,w_3392/q_auto/v1740000000/fom-website/2025/Cadillac%20(GM)/Formula%201%20header%20templates%20-%202025-05-04T004129.094.webp"}
}

PILOTO_A_EQUIPO = {
    "Norris": "McLaren", "Piastri": "McLaren", "Antonelli": "Mercedes", "Russell": "Mercedes",
    "Verstappen": "Red Bull", "Hadjar": "Red Bull", "Leclerc": "Ferrari", "Hamilton": "Ferrari",
    "Albon": "Williams", "Sainz Jr.": "Williams", "Lawson": "Racing Bulls", "Lindblad": "Racing Bulls",
    "Alonso": "Aston Martin", "Stroll": "Aston Martin", "Ocon": "Haas", "Bearman": "Haas",
    "Bortoleto": "Audi", "Hülkenberg": "Audi", "Gasly": "Alpine", "Colapinto": "Alpine",
    "Perez": "Cadillac", "Bottas": "Cadillac"
}

PILOTOS_CON_EMOJI = ["- Seleccionar -"] + [f"{EQUIPOS_DATA[PILOTO_A_EQUIPO[p]]['emoji']} {p}" for p in PILOTOS_2026]

# --- LISTAS DE OPCIONES GLOBALES (Para que el Admin no dé error) ---
OPCIONES_PILOTOS = ["- Seleccionar -"] + PILOTOS_2026
OPCIONES_EQUIPOS = ["- Seleccionar -"] + EQUIPOS_2026
OPCIONES_BINARIAS = ["- Seleccionar -", "SI", "NO"]
POSICIONES_CARRERA = ["- Seleccionar -", "DNF"] + [str(i) for i in range(1, 23)]

# Fecha límite Mundial
FECHA_LIMITE_TEMPORADA = datetime(2026, 3, 8, 5, 0)
MUNDIAL_BLOQUEADO = datetime.now() > FECHA_LIMITE_TEMPORADA

# 2. FUNCIONES DE CÁLCULO
def calcular_puntos_gp(u_preds, gp_results, detalle=False):
    pts = 0.0
    desglose = {"Qualy": 0.0, "Sprint": 0.0, "Carrera": 0.0, "Extras": 0.0}
    if u_preds.empty or gp_results.empty: return desglose if detalle else 0.0
    real_q = gp_results[gp_results['Variable'].str.contains('Q')].sort_values('Variable')['Valor'].tolist()
    real_s = gp_results[gp_results['Variable'].str.contains('S')].sort_values('Variable')['Valor'].tolist()
    real_c = gp_results[gp_results['Variable'].str.contains('C')].sort_values('Variable')['Valor'].tolist()

    for _, row in u_preds.iterrows():
        var, val_p = row['Variable'], row['Valor']
        res_row = gp_results[gp_results['Variable'] == var]
        if res_row.empty: continue
        val_r = res_row.iloc[0]['Valor']
        puntos_esta_var = 0.0
        if var.startswith('Q') or var.startswith('C'):
            lista_real = real_q if var.startswith('Q') else real_c
            try:
                pos_pred = int(var[1:])
                if val_p == val_r: puntos_esta_var = 2.0
                elif val_p in lista_real:
                    pos_real = lista_real.index(val_p) + 1
                    puntos_esta_var = 1.5 if abs(pos_pred - pos_real) == 1 else 0.5
            except: pass
            if var.startswith('Q'): desglose["Qualy"] += puntos_esta_var
            else: desglose["Carrera"] += puntos_esta_var
        elif var.startswith('S'):
            if val_p == val_r: puntos_esta_var = 1.0
            desglose["Sprint"] += puntos_esta_var
        elif var in ['Alonso', 'Sainz']:
            try:
                if str(val_p) == str(val_r): puntos_esta_var = 2.0
                elif val_p != "DNF" and val_r != "DNF" and abs(int(val_p) - int(val_r)) == 1: puntos_esta_var = 1.0
            except: pass
            desglose["Extras"] += puntos_esta_var
        elif var in ['Safety', 'RedFlag']:
            if str(val_p).lower() == str(val_r).lower(): puntos_esta_var = 2.0
            desglose["Extras"] += puntos_esta_var
        pts += puntos_esta_var
    return desglose if detalle else pts

def calcular_puntos_mundial(u_preds_temp, mundial_results):
    pts = 0.0
    if u_preds_temp.empty or mundial_results.empty: return 0.0
    real_p = mundial_results[mundial_results['Variable'].str.startswith('P')].sort_values('Variable')['Valor'].tolist()
    real_e = mundial_results[mundial_results['Variable'].str.startswith('E')].sort_values('Variable')['Valor'].tolist()
    for _, row in u_preds_temp.iterrows():
        var, val_p = row['Variable'], row['Valor']
        res_row = mundial_results[mundial_results['Variable'] == var]
        if res_row.empty: continue
        val_r = res_row.iloc[0]['Valor']
        try:
            pos_pred = int(var[1:])
            if val_p == val_r: pts += 5.0
            else:
                if var.startswith('P') and val_p in real_p:
                    pos_real = real_p.index(val_p) + 1
                    distancia = abs(pos_pred - pos_real)
                    if distancia == 1: pts += 2.0
                    elif distancia == 2: pts += 1.0
                elif var.startswith('E') and val_p in real_e:
                    pos_real = real_e.index(val_p) + 1
                    if abs(pos_pred - pos_real) == 1: pts += 2.0
        except: pass
    return pts

def get_idx_emoji(pilot_name):
    if pilot_name == "- Seleccionar -": return 0
    for i, p_emoji in enumerate(PILOTOS_CON_EMOJI):
        if p_emoji.endswith(pilot_name): return i
    return 0

def comprobar_duplicados(lista_seleccionada):
    # Filtramos el valor por defecto
    filtrada = [x for x in lista_seleccionada if x != "- Seleccionar -"]
    # Retorna True si hay elementos repetidos
    return len(filtrada) != len(set(filtrada))

# 3. INTERFAZ Y LOGIN
st.set_page_config(page_title="F1 Porra 2026", page_icon="🏎️", layout="wide")

# --- INYECCIÓN DE CSS F1 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; text-transform: uppercase; font-style: italic; color: #e10600 !important; border-left: 8px solid #e10600; padding-left: 15px; margin-top: 20px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #15151e; border-radius: 4px 20px 0px 0px; color: white; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { border-bottom: 4px solid #e10600 !important; background-color: #1e1e27; }
    [data-testid="stMetricValue"] { font-family: 'Orbitron', sans-serif; color: #00ff00 !important; background: black; padding: 10px; border-radius: 5px; border: 1px solid #e10600; }
    .stForm { border: 1px solid #333 !important; border-top: 4px solid #e10600 !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos(pestana):
    try: return conn.read(worksheet=pestana, ttl=0)
    except: return pd.DataFrame()

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏎️ F1 Pro Predictor")
    tab_login, tab_registro = st.tabs(["🔐 Entrar", "📝 Registrarse"])
    with tab_login:
        with st.form("Login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                df_u = leer_datos("Usuarios")
                if not df_u.empty and u in df_u['Usuario'].values:
                    user_row = df_u[df_u['Usuario']==u]
                    if p == str(user_row['Password'].values[0]):
                        st.session_state.auth, st.session_state.user = True, u
                        st.session_state.rol = user_row['Rol'].values[0]
                        st.rerun()
                st.error("Usuario o contraseña incorrectos")
    with tab_registro:
        with st.form("Registro"):
            new_u = st.text_input("Nombre de Piloto (Usuario)")
            new_p = st.text_input("Contraseña", type="password")
            fav_team = st.selectbox("Tu Escudería Favorita", list(EQUIPOS_DATA.keys()))
            confirm_p = st.text_input("Confirma contraseña", type="password")
            if st.form_submit_button("🏎️ Unirse a la Parrilla"):
                df_u = leer_datos("Usuarios")
                if not new_u or not new_p: st.warning("Rellena todo.")
                elif new_p != confirm_p: st.error("Passwords no coinciden.")
                elif not df_u.empty and new_u in df_u['Usuario'].values: st.error("El usuario ya existe")
                else:
                    nuevo_reg = pd.DataFrame([{"Usuario": new_u, "Password": new_p, "Rol": "user", "Equipo": fav_team}])
                    conn.update(worksheet="Usuarios", data=pd.concat([df_u, nuevo_reg], ignore_index=True))
                    st.success("✅ ¡Fichaje completado!")

else:
    # 4. CARGA DE DATOS
    df_p = leer_datos("Predicciones")
    df_r = leer_datos("Resultados")
    df_temp = leer_datos("Temporada")
    df_cal = leer_datos("Calendario")
    df_r_mundial = leer_datos("ResultadosMundial")
    SPRINT_GPS = ["02. GP de China", "06. GP de Miami", "07. GP de Canadá", "11. GP de Gran Bretaña", "14. GP de los Países Bajos", "18. GP de Singapur"]

    if df_p.empty: df_p = pd.DataFrame(columns=['Usuario', 'GP', 'Variable', 'Valor'])
    if df_r.empty: df_r = pd.DataFrame(columns=['GP', 'Variable', 'Valor'])
    if df_temp.empty: df_temp = pd.DataFrame(columns=['Usuario', 'Variable', 'Valor'])
    if df_cal.empty: df_cal = pd.DataFrame(columns=['GP', 'LimiteQualy', 'LimiteSprint', 'LimiteCarrera'])

    # --- LÓGICA DE BARRA LATERAL Y BLOQUEO CON COUNTDOWN ---
    st.sidebar.title(f"Piloto: {st.session_state.user}")
    gp_sel = st.sidebar.selectbox("Gran Premio", GPS)
    
    es_sprint = gp_sel in SPRINT_GPS
    cal_row = df_cal[df_cal['GP'] == gp_sel]
    now = datetime.now()

    q_bloq, s_bloq, c_bloq = False, False, False
    
    if not cal_row.empty:
        q_lim = pd.to_datetime(cal_row.iloc[0]['LimiteQualy'])
        c_lim = pd.to_datetime(cal_row.iloc[0]['LimiteCarrera'])
        
        def obtener_countdown(fecha_limite):
            diff = fecha_limite - now
            if diff.total_seconds() <= 0: return "🔴 Cerrada"
            dias = diff.days
            horas, rem = divmod(diff.seconds, 3600)
            minutos, _ = divmod(rem, 60)
            if dias > 0: return f"🟢 Cierra en {dias}d {horas}h"
            elif horas > 0: return f"⏳ ¡Date prisa! Cierra en {horas}h {minutos}m"
            else: return f"🔥 ¡ÚLTIMOS MINUTOS! {minutos}m restantes"

        q_bloq = now > q_lim
        c_bloq = now > c_lim

        st.sidebar.markdown("---")
        st.sidebar.subheader("⏱️ Clasificación")
        st.sidebar.markdown(f"**{obtener_countdown(q_lim)}**")
        
        if es_sprint:
            s_lim = pd.to_datetime(cal_row.iloc[0]['LimiteSprint'])
            s_bloq = now > s_lim
            st.sidebar.subheader("🏎️ Sprint")
            st.sidebar.markdown(f"**{obtener_countdown(s_lim)}**")

        st.sidebar.subheader("🏁 Carrera")
        st.sidebar.markdown(f"**{obtener_countdown(c_lim)}**")
        st.sidebar.markdown("---")
    else:
        st.sidebar.warning("⚠️ Horarios no configurados")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # --- DEFINICIÓN DE PESTAÑAS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✍️ Mis Apuestas", "📊 Clasificación", "🏆 Mundial", "⚙️ Admin", "🔍 El Muro"])

    with tab1:
        st.header(f"✍️ Predicciones - {gp_sel}")
        if st.session_state.rol == 'admin':
            st.warning("⚠️ Los administradores no apuestan.")
        else:
            # Obtener predicciones actuales del usuario para este GP
            user_gp_preds = df_p[(df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel)]
            
            def get_val(var):
                match = user_gp_preds[user_gp_preds['Variable'] == var]
                return match.iloc[0]['Valor'] if not match.empty else "- Seleccionar -"

            with st.form("form_gp_global"):
                # --- SECCIÓN QUALY ---
                st.subheader("⏱️ Clasificación (Top 5)")
                cq = st.columns(5)
                q_raw = [cq[i].selectbox(f"P{i+1} Q", PILOTOS_CON_EMOJI, index=get_idx_emoji(get_val(f"Q{i+1}")), key=f"q_u_{i}", disabled=q_bloq) for i in range(5)]
                
                # --- SECCIÓN SPRINT ---
                s_raw = []
                if es_sprint:
                    st.divider()
                    st.subheader("🏎️ Carrera Sprint (Top 3)")
                    cs = st.columns(3)
                    s_raw = [cs[i].selectbox(f"P{i+1} S", PILOTOS_CON_EMOJI, index=get_idx_emoji(get_val(f"S{i+1}")), key=f"s_u_{i}", disabled=s_bloq) for i in range(3)]

                # --- SECCIÓN CARRERA Y EXTRAS ---
                st.divider()
                st.subheader("🏁 Carrera y Extras")
                cc1, cc2 = st.columns(2)
                with cc1:
                    c_raw = [st.selectbox(f"P{i+1} Carrera", PILOTOS_CON_EMOJI, index=get_idx_emoji(get_val(f"C{i+1}")), key=f"c_u_{i}", disabled=c_bloq) for i in range(5)]
                with cc2:
                    alo = st.selectbox("Pos. Alonso", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Alonso")), disabled=c_bloq)
                    sai = st.selectbox("Pos. Sainz Jr.", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Sainz")), disabled=c_bloq)
                    saf = st.selectbox("¿Safety Car?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("Safety")), disabled=c_bloq)
                    red = st.selectbox("¿Bandera Roja?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("RedFlag")), disabled=c_bloq)

                # --- LÓGICA DE DETECCIÓN DE DUPLICADOS ---
                q_names = [p.split(" ", 1)[-1] for p in q_raw]
                c_names = [p.split(" ", 1)[-1] for p in c_raw]
                s_names = [p.split(" ", 1)[-1] for p in s_raw]
                
                hay_duplicados = False
                if comprobar_duplicados(q_names):
                    st.error("❌ Error: Has repetido pilotos en el Top 5 de Clasificación.")
                    hay_duplicados = True
                if comprobar_duplicados(c_names):
                    st.error("❌ Error: Has repetido pilotos en el Top 5 de Carrera.")
                    hay_duplicados = True
                if es_sprint and comprobar_duplicados(s_names):
                    st.error("❌ Error: Has repetido pilotos en la Sprint.")
                    hay_duplicados = True

                # El botón se bloquea automáticamente si hay duplicados
                if st.form_submit_button("💾 Guardar Todo", disabled=hay_duplicados):
                    if "- Seleccionar -" in q_names + c_names + [alo, sai, saf, red]:
                        st.error("⚠️ Por favor, rellena todos los campos antes de guardar.")
                    else:
                        data = []
                        for i, v in enumerate(q_names): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        for i, v in enumerate(s_names): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"S{i+1}", "Valor": v})
                        for i, v in enumerate(c_names): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        data.extend([
                            {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Alonso", "Valor": alo},
                            {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Sainz", "Valor": sai},
                            {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Safety", "Valor": saf},
                            {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "RedFlag", "Valor": red}
                        ])
                        df_p = pd.concat([df_p[~((df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel))], pd.DataFrame(data)])
                        conn.update(worksheet="Predicciones", data=df_p)
                        st.success("✅ ¡Tus apuestas han sido registradas!")

    with tab2:
        # --- ESTILOS CSS PEDESTAL + RACE CONTROL ---
        st.markdown("""
            <style>
            .podium-container { display: flex; align-items: flex-end; justify-content: center; gap: 10px; padding: 40px 0 20px 0; }
            .podium-card { 
                text-align: center; padding: 20px 10px; border-radius: 10px 10px 5px 5px; 
                background: #1a1a24; width: 100%; display: flex; flex-direction: column;
                justify-content: space-between; box-shadow: 0 10px 30px rgba(0,0,0,0.5); position: relative;
            }
            .p1 { height: 320px; border-top: 8px solid #FFD700; z-index: 2; }
            .p2 { height: 260px; border-top: 8px solid #C0C0C0; opacity: 0.9; }
            .p3 { height: 230px; border-top: 8px solid #CD7F32; opacity: 0.8; }
            
            .podium-card h2, .podium-card h3, .podium-card p, .podium-card div { 
                border-left: none !important; padding-left: 0 !important; margin: 0 !important; font-style: normal !important;
            }
            .rank-label { font-size: 2.2em; font-weight: 900; color: #fff; font-family: 'Orbitron'; }
            .driver-name { font-size: 1.3em; color: #ffffff; font-weight: 700; margin-top: 15px !important; }
            .points-label { font-size: 1.5em; color: #00ff00; font-weight: 900; font-family: 'Orbitron'; padding-bottom: 15px !important; }

            /* Estilo para las filas de clasificación y Race Control */
            .driver-card { 
                display: flex; align-items: center; justify-content: space-between; 
                padding: 12px 25px; margin: 10px 0; border-radius: 5px; 
                background: #15151e; border-left: 10px solid; color: white;
            }
            .telemetry-box { display: flex; gap: 15px; font-size: 0.85em; opacity: 0.8; margin-right: 20px; }
            .telemetry-box b { color: #e10600; }
            </style>
        """, unsafe_allow_html=True)

        subtab_gen, subtab_gp = st.tabs(["🌎 CLASIFICACIÓN MUNDIAL", "🏁 RACE CONTROL"])

        # --- LÓGICA DE DATOS ---
        df_users_ranking = leer_datos("Usuarios")
        if not df_users_ranking.empty:
            participantes = df_users_ranking[df_users_ranking['Rol'] == 'user']['Usuario'].unique()
            
            def get_team_info(usuario):
                row = df_users_ranking[df_users_ranking['Usuario'] == usuario]
                team = row['Equipo'].values[0] if not row.empty and 'Equipo' in row.columns else "McLaren"
                return EQUIPOS_DATA.get(team, EQUIPOS_DATA["McLaren"])

        # --- SUBPESTAÑA 1: MUNDIAL ---
        with subtab_gen:
            ranking_list = []
            for u in participantes:
                p_gps = sum([calcular_puntos_gp(df_p[(df_p['Usuario']==u) & (df_p['GP']==g)], df_r[df_r['GP']==g]) for g in GPS])
                p_mundial = calcular_puntos_mundial(df_temp[df_temp['Usuario']==u], df_r_mundial)
                ranking_list.append({"Piloto": u, "TOTAL": p_gps + p_mundial})
            
            df_final = pd.DataFrame(ranking_list).sort_values("TOTAL", ascending=False)

            if not df_final.empty:
                top_3 = df_final.head(3).to_dict('records')
                st.markdown('<div class="podium-container">', unsafe_allow_html=True)
                cols = st.columns([1, 1.2, 1])
                orden = [{"idx": 1, "css": "p2", "lbl": "P2"}, {"idx": 0, "css": "p1", "lbl": "P1"}, {"idx": 2, "css": "p3", "lbl": "P3"}]
                
                for i, c in enumerate(orden):
                    if c["idx"] < len(top_3):
                        d = top_3[c["idx"]]
                        team = get_team_info(d['Piloto'])
                        with cols[i]:
                            st.markdown(f"""
                                <div class="podium-card {c['css']}">
                                    <div class="rank-label">{c['lbl']}</div>
                                    <div style="flex-grow: 1; display: flex; align-items: center; justify-content: center;">
                                        <img src="{team['logo']}" width="80">
                                    </div>
                                    <div class="driver-name">{d['Piloto']}</div>
                                    <div class="points-label">{int(d['TOTAL'])} PTS</div>
                                </div>
                            """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()

                if len(df_final) > 3:
                    for i, row in df_final.iloc[3:].iterrows():
                        team = get_team_info(row['Piloto'])
                        st.markdown(f"""
                            <div class="driver-card" style="border-left-color: {team['color']};">
                                <div style="display:flex; align-items:center; gap:20px;">
                                    <span style="font-family:Orbitron; font-size:1.6em; width:45px; font-weight:800;">{list(df_final['Piloto']).index(row['Piloto'])+1}</span>
                                    <img src="{team['logo']}" width="40">
                                    <span style="font-size:1.2em; font-weight:700;">{row['Piloto']}</span>
                                </div>
                                <div style="text-align:right;">
                                    <span style="font-family:Orbitron; color:#00ff00; font-size:1.4em; font-weight:800;">{int(row['TOTAL'])} PTS</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

        # --- SUBPESTAÑA 2: RACE CONTROL (GP ESPECÍFICO) ---
        with subtab_gp:
            gp_sel_rank = st.selectbox("Analizar Gran Premio:", GPS, key="gp_rank_control")
            res_real = df_r[df_r['GP'] == gp_sel_rank]
            
            if res_real.empty:
                st.info("📢 Resultados no disponibles. Esperando a que el Admin publique los datos oficiales.")
            else:
                detalles_gp = []
                for u in participantes:
                    # Usamos detalle=True para el desglose
                    d = calcular_puntos_gp(df_p[(df_p['Usuario']==u) & (df_p['GP']==gp_sel_rank)], res_real, detalle=True)
                    detalles_gp.append({"Piloto": u, **d, "Total": sum(d.values())})
                
                df_det = pd.DataFrame(detalles_gp).sort_values("Total", ascending=False)
                
                for i, r in df_det.iterrows():
                    team = get_team_info(r['Piloto'])
                    pos = list(df_det['Piloto']).index(r['Piloto']) + 1
                    
                    st.markdown(f"""
                        <div class="driver-card" style="border-left-color: {team['color']}; background: #0e0e12; margin: 5px 0;">
                            <div style="display:flex; align-items:center; gap:15px; flex-grow:1;">
                                <span style="font-family:Orbitron; font-size:1.2em; width:30px; opacity:0.6;">{pos}</span>
                                <img src="{team['logo']}" width="30">
                                <span style="font-weight:700;">{r['Piloto']}</span>
                            </div>
                            <div class="telemetry-box">
                                <span>Q:<b>{r['Qualy']}</b></span>
                                <span>S:<b>{r['Sprint']}</b></span>
                                <span>C:<b>{r['Carrera']}</b></span>
                                <span>+:<b>{r['Extras']}</b></span>
                            </div>
                            <div style="color:#00ff00; font-weight:800; font-family:Orbitron; font-size:1.1em; width:90px; text-align:right;">
                                {int(r['Total'])} PTS
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    with tab3:
        st.header("🏆 Mundial de Temporada")
        if st.session_state.rol == 'admin':
            st.warning("⚠️ Los administradores no participan en el Mundial.")
        elif MUNDIAL_BLOQUEADO:
            st.info("🔒 El mercado de fichajes está cerrado. Esta es tu apuesta:")
            df_u_mundial = df_temp[df_temp['Usuario'] == st.session_state.user]
            st.dataframe(df_u_mundial[['Variable', 'Valor']], use_container_width=True, hide_index=True)
        else:
            df_u_mundial = df_temp[df_temp['Usuario'] == st.session_state.user]
            
            with st.form("form_mundial"):
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("👤 Top Pilotos")
                    p_mundial_raw = []
                    for i in range(22):
                        v_actual = df_u_mundial[df_u_mundial['Variable'] == f"P{i+1}"]['Valor'].values
                        idx = get_idx_emoji(v_actual[0]) if len(v_actual) > 0 else 0
                        p_mundial_raw.append(st.selectbox(f"P{i+1}", PILOTOS_CON_EMOJI, index=idx, key=f"m_p_{i}"))
                
                with c2:
                    st.subheader("🏎️ Top Equipos")
                    e_mundial = []
                    for i in range(11):
                        v_actual = df_u_mundial[df_u_mundial['Variable'] == f"E{i+1}"]['Valor'].values
                        idx_e = (OPCIONES_EQUIPOS.index(v_actual[0])) if (len(v_actual) > 0 and v_actual[0] in OPCIONES_EQUIPOS) else 0
                        e_mundial.append(st.selectbox(f"E{i+1}", OPCIONES_EQUIPOS, index=idx_e, key=f"m_e_{i}"))

                # Validación de nombres limpios
                p_names_m = [p.split(" ", 1)[-1] for p in p_mundial_raw]
                
                error_mundial = False
                if comprobar_duplicados(p_names_m):
                    st.error("❌ Tienes pilotos repetidos en tu clasificación del Mundial.")
                    error_mundial = True
                if comprobar_duplicados(e_mundial):
                    st.error("❌ Tienes escuderías repetidas en tu clasificación del Mundial.")
                    error_mundial = True

                if st.form_submit_button("💾 Guardar Mundial", disabled=error_mundial):
                    if "- Seleccionar -" in p_names_m or "- Seleccionar -" in e_mundial:
                        st.error("⚠️ Debes completar las 22 posiciones de pilotos y 11 de equipos.")
                    else:
                        m_data = []
                        for i, v in enumerate(p_names_m): 
                            m_data.append({"Usuario": st.session_state.user, "Variable": f"P{i+1}", "Valor": v})
                        for i, v in enumerate(e_mundial): 
                            m_data.append({"Usuario": st.session_state.user, "Variable": f"E{i+1}", "Valor": v})
                        
                        df_temp = pd.concat([df_temp[df_temp['Usuario'] != st.session_state.user], pd.DataFrame(m_data)])
                        conn.update(worksheet="Temporada", data=df_temp)
                        st.success("✅ ¡Tu clasificación mundial ha sido guardada!")
                        
    with tab4:
        if st.session_state.rol == 'admin':
            adm_gp, adm_final, adm_fechas = st.tabs(["🏁 Resultados GP", "🌎 Mundial Final", "📅 Fechas Límite"])
            
            with adm_gp:
                st.subheader(f"Publicar Resultados Reales: {gp_sel}")
                with st.form("admin_gp_results"):
                    ac1, ac2 = st.columns(2)
                    with ac1:
                        st.markdown("**Top 5 Clasificación**")
                        aq_raw = [st.selectbox(f"Q{i+1} Real", PILOTOS_CON_EMOJI, index=0, key=f"arq{i}") for i in range(5)]
                        st.markdown("**Top 5 Carrera**")
                        ac_raw = [st.selectbox(f"C{i+1} Real", PILOTOS_CON_EMOJI, index=0, key=f"arc{i}") for i in range(5)]
                    
                    with ac2:
                        st.markdown("**Eventos y Españoles**")
                        res_alo = st.selectbox("Alonso Real", POSICIONES_CARRERA, index=0, key="ara_adm")
                        res_sai = st.selectbox("Sainz Real", POSICIONES_CARRERA, index=0, key="ars_adm")
                        res_sf = st.selectbox("Safety / VSC Real", OPCIONES_BINARIAS, index=0, key="arsf_adm")
                        res_rf = st.selectbox("Red Flag Real", OPCIONES_BINARIAS, index=0, key="arrf_adm")
                        
                        as_raw = []
                        if es_sprint:
                            st.markdown("---")
                            st.markdown("**Top 3 Sprint**")
                            as_raw = [st.selectbox(f"S{i+1} Real", PILOTOS_CON_EMOJI, index=0, key=f"arsprint{i}") for i in range(3)]
                    
                    if st.form_submit_button("📢 Publicar Resultados"):
                        # Limpiamos los emojis antes de guardar en la base de datos
                        aq = [v.split(" ", 1)[-1] for v in aq_raw]
                        ac = [v.split(" ", 1)[-1] for v in ac_raw]
                        as_res = [v.split(" ", 1)[-1] for v in as_raw]
                        
                        check_list = aq + ac + as_res + [res_alo, res_sai, res_sf, res_rf]
                        if "- Seleccionar -" in check_list:
                            st.error("⚠️ Error: Selecciona todos los resultados.")
                        else:
                            r_data = []
                            for i, v in enumerate(aq): r_data.append({"GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                            for i, v in enumerate(ac): r_data.append({"GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                            for i, v in enumerate(as_res): r_data.append({"GP": gp_sel, "Variable": f"S{i+1}", "Valor": v})
                            r_data.extend([
                                {"GP": gp_sel, "Variable": "Alonso", "Valor": res_alo},
                                {"GP": gp_sel, "Variable": "Sainz", "Valor": res_sai},
                                {"GP": gp_sel, "Variable": "Safety", "Valor": res_sf},
                                {"GP": gp_sel, "Variable": "RedFlag", "Valor": res_rf}
                            ])
                            df_r = pd.concat([df_r[df_r['GP'] != gp_sel], pd.DataFrame(r_data)])
                            conn.update(worksheet="Resultados", data=df_r)
                            st.success(f"✅ Resultados de {gp_sel} publicados.")
                            st.balloons()

            with adm_final:
                st.subheader("Resultados Finales del Campeonato")
                with st.form("admin_mundial_final"):
                    am1, am2 = st.columns(2)
                    f_p_raw = [am1.selectbox(f"P{i+1} Mundial", PILOTOS_CON_EMOJI, index=0, key=f"fin_p_{i}") for i in range(22)]
                    f_e = [am2.selectbox(f"E{i+1} Mundial", OPCIONES_EQUIPOS, index=0, key=f"fin_e_{i}") for i in range(11)]
                    if st.form_submit_button("🏆 Publicar Mundial Final"):
                        f_p = [v.split(" ", 1)[-1] for v in f_p_raw]
                        if "- Seleccionar -" in f_p or "- Seleccionar -" in f_e:
                            st.error("⚠️ Parrilla incompleta.")
                        else:
                            m_f = []
                            for i, v in enumerate(f_p): m_f.append({"Variable": f"P{i+1}", "Valor": v})
                            for i, v in enumerate(f_e): m_f.append({"Variable": f"E{i+1}", "Valor": v})
                            conn.update(worksheet="ResultadosMundial", data=pd.DataFrame(m_f))
                            st.success("🏆 Resultados mundiales guardados.")

            with adm_fechas:
                st.subheader("Configurar Horarios")
                with st.form("f_cal_admin"):
                    f_gp = st.selectbox("Gran Premio", GPS, key="f_gp_cal")
                    c_q, c_s, c_c = st.columns(3)
                    dq, tq = c_q.date_input("Fecha Qualy"), c_q.time_input("Hora Qualy")
                    ds, ts = c_s.date_input("Fecha Sprint"), c_s.time_input("Hora Sprint")
                    dc, tc = c_c.date_input("Fecha Carrera"), c_c.time_input("Hora Carrera")
                    if st.form_submit_button("📅 Guardar Calendario"):
                        c_data = {
                            "GP": f_gp, 
                            "LimiteQualy": datetime.combine(dq, tq).strftime('%Y-%m-%d %H:%M:%S'),
                            "LimiteSprint": datetime.combine(ds, ts).strftime('%Y-%m-%d %H:%M:%S'),
                            "LimiteCarrera": datetime.combine(dc, tc).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        df_cal = pd.concat([df_cal[df_cal['GP'] != f_gp], pd.DataFrame([c_data])])
                        conn.update(worksheet="Calendario", data=df_cal)
                        st.success(f"✅ Horarios para {f_gp} actualizados.")
        else:
            st.error("⛔ Acceso restringido.")

    with tab5:
        st.header("🔍 El Muro de la Verdad")
        df_muro = df_p[df_p['GP'] == gp_sel].copy()
        if not df_muro.empty:
            # Creamos el pivote
            df_piv = df_muro.pivot(index='Usuario', columns='Variable', values='Valor')
            
            # Definimos el orden lógico de las columnas
            orden_columnas = (
                [f"Q{i+1}" for i in range(5)] + 
                ([f"S{i+1}" for i in range(3)] if es_sprint else []) + 
                [f"C{i+1}" for i in range(5)] + 
                ["Alonso", "Sainz", "Safety", "RedFlag"]
            )
            
            # Solo mostramos las columnas que realmente existan en el DF
            cols_a_mostrar = [c for c in orden_columnas if c in df_piv.columns]
            
            st.dataframe(
                df_piv[cols_a_mostrar], 
                use_container_width=True,
                column_config={
                    "Usuario": st.column_config.TextColumn("Piloto")
                }
            )
        else:
            st.info("Todavía no hay apuestas registradas para este Gran Premio.")
