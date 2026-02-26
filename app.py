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
    "Audi": {"emoji": "🔘", "color": "#F50A25", "logo": "https://www.audi.com/content/dam/gbp2/experience-audi/audi-sport/audi-f1/1920x1080-logo-audi-f1.jpg"},
    "Cadillac": {"emoji": "🟡", "color": "#FFD700", "logo": "https://upload.wikimedia.org/wikipedia/commons/4/44/Cadillac_logo.svg"}
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

    # --- LÓGICA DE BLOQUEO ---
    st.sidebar.title(f"Piloto: {st.session_state.user}")
    gp_sel = st.sidebar.selectbox("Gran Premio", GPS)
    es_sprint = gp_sel in SPRINT_GPS
    cal_row = df_cal[df_cal['GP'] == gp_sel]
    now = datetime.now()
    q_bloq, s_bloq, c_bloq = False, False, False
    if not cal_row.empty:
        q_lim = pd.to_datetime(cal_row.iloc[0]['LimiteQualy'])
        c_lim = pd.to_datetime(cal_row.iloc[0]['LimiteCarrera'])
        q_bloq, c_bloq = now > q_lim, now > c_lim
        st.sidebar.markdown(f"**⏱️ Qualy:** {'🔴 Cerrada' if q_bloq else '🟢 Abierta'}")
        if es_sprint:
            s_lim = pd.to_datetime(cal_row.iloc[0]['LimiteSprint'])
            s_bloq = now > s_lim
            st.sidebar.markdown(f"**🏎️ Sprint:** {'🔴 Cerrada' if s_bloq else '🟢 Abierta'}")
        st.sidebar.markdown(f"**🏁 Carrera:** {'🔴 Cerrada' if c_bloq else '🟢 Abierta'}")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✍️ Mis Apuestas", "📊 Clasificación", "🏆 Mundial", "⚙️ Admin", "🔍 El Muro"])

    with tab1:
        st.header(f"✍️ Predicciones - {gp_sel}")
        if st.session_state.rol == 'admin':
            st.warning("⚠️ Los administradores no apuestan.")
        else:
            user_gp_preds = df_p[(df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel)]
            def get_val(var):
                match = user_gp_preds[user_gp_preds['Variable'] == var]
                return match.iloc[0]['Valor'] if not match.empty else "- Seleccionar -"

            with st.form("form_gp_global"):
                st.subheader("⏱️ Clasificación (Top 5)")
                cq = st.columns(5)
                q_res_raw = [cq[i].selectbox(f"P{i+1} Q", PILOTOS_CON_EMOJI, index=get_idx_emoji(get_val(f"Q{i+1}")), key=f"q_u_{i}", disabled=q_bloq) for i in range(5)]
                
                s_res_raw = []
                if es_sprint:
                    st.divider()
                    st.subheader("🏎️ Carrera Sprint (Top 3)")
                    cs = st.columns(3)
                    s_res_raw = [cs[i].selectbox(f"P{i+1} S", PILOTOS_CON_EMOJI, index=get_idx_emoji(get_val(f"S{i+1}")), key=f"s_u_{i}", disabled=s_bloq) for i in range(3)]

                st.divider()
                st.subheader("🏁 Carrera y Extras")
                cc1, cc2 = st.columns(2)
                with cc1:
                    c_res_raw = [st.selectbox(f"P{i+1} Carrera", PILOTOS_CON_EMOJI, index=get_idx_emoji(get_val(f"C{i+1}")), key=f"c_u_{i}", disabled=c_bloq) for i in range(5)]
                with cc2:
                    OPCIONES_BINARIAS = ["- Seleccionar -", "SI", "NO"]
                    POSICIONES_CARRERA = ["- Seleccionar -", "DNF"] + [str(i) for i in range(1, 23)]
                    alo = st.selectbox("Pos. Alonso", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Alonso")), disabled=c_bloq)
                    sai = st.selectbox("Pos. Sainz Jr.", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Sainz")), disabled=c_bloq)
                    saf = st.selectbox("¿Safety Car?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("Safety")), disabled=c_bloq)
                    red = st.selectbox("¿Bandera Roja?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("RedFlag")), disabled=c_bloq)

                if st.form_submit_button("💾 Guardar Todo"):
                    # Limpiar emojis para guardar solo el nombre
                    q_res = [p.split(" ", 1)[-1] for p in q_res_raw]
                    s_res = [p.split(" ", 1)[-1] for p in s_res_raw]
                    c_res = [p.split(" ", 1)[-1] for p in c_res_raw]
                    
                    if "- Seleccionar -" in q_res + s_res + c_res + [alo, sai, saf, red]:
                        st.error("⚠️ Rellena todos los campos.")
                    else:
                        data = []
                        for i, v in enumerate(q_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        for i, v in enumerate(s_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"S{i+1}", "Valor": v})
                        for i, v in enumerate(c_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        data.extend([{"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Alonso", "Valor": alo},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Sainz", "Valor": sai},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Safety", "Valor": saf},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "RedFlag", "Valor": red}])
                        df_p = pd.concat([df_p[~((df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel))], pd.DataFrame(data)])
                        conn.update(worksheet="Predicciones", data=df_p)
                        st.success("✅ ¡Guardado!")

    with tab2:
        # --- ESTILOS CSS PEDESTAL PRO ---
        st.markdown("""
            <style>
            /* Contenedor principal del podio */
            .podium-container { 
                display: flex; 
                align-items: flex-end; 
                justify-content: center; 
                gap: 10px; 
                padding: 40px 0 20px 0; 
                margin-bottom: 20px;
            }
            
            /* Tarjeta base */
            .podium-card { 
                text-align: center; 
                padding: 20px 10px; 
                border-radius: 10px 10px 5px 5px; 
                background: #1a1a24; 
                width: 100%; 
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                position: relative;
            }

            /* Alturas diferenciadas: P1 el más alto sobresaliendo */
            .p1 { height: 320px; border-top: 8px solid #FFD700; z-index: 2; }
            .p2 { height: 260px; border-top: 8px solid #C0C0C0; opacity: 0.9; }
            .p3 { height: 230px; border-top: 8px solid #CD7F32; opacity: 0.8; }

            /* Limpieza total de los títulos (Eliminar barra roja lateral de las fotos) */
            .podium-card h2, .podium-card h3, .podium-card p, .podium-card div { 
                border-left: none !important; 
                padding-left: 0 !important; 
                margin: 0 !important;
                font-style: normal !important;
            }

            .rank-label { font-size: 2.2em; font-weight: 900; color: #fff; font-family: 'Orbitron'; }
            .driver-name { font-size: 1.3em; color: #ffffff; font-weight: 700; margin-top: 15px !important; }
            
            /* Puntos: subidos para que no toquen el borde */
            .points-label { 
                font-size: 1.5em; 
                color: #00ff00; 
                font-weight: 900; 
                font-family: 'Orbitron';
                padding-bottom: 15px !important; 
            }

            /* Tarjetas inferiores (P4+) */
            .driver-card { 
                display: flex; align-items: center; justify-content: space-between; 
                padding: 12px 25px; margin: 10px 0; border-radius: 5px; 
                background: #15151e; border-left: 10px solid; color: white;
            }
            </style>
        """, unsafe_allow_html=True)

        subtab_gen, subtab_gp = st.tabs(["🌎 CLASIFICACIÓN MUNDIAL", "🏁 RACE CONTROL"])

        # --- LÓGICA DE DATOS ---
        df_users_ranking = leer_datos("Usuarios")
        if not df_users_ranking.empty:
            participantes = df_users_ranking[df_users_ranking['Rol'] == 'user']['Usuario'].unique()
            ranking_list = []
            for u in participantes:
                p_gps = sum([calcular_puntos_gp(df_p[(df_p['Usuario']==u) & (df_p['GP']==g)], df_r[df_r['GP']==g]) for g in GPS])
                p_mundial = calcular_puntos_mundial(df_temp[df_temp['Usuario']==u], df_r_mundial)
                ranking_list.append({"Piloto": u, "TOTAL": p_gps + p_mundial})
            
            df_final = pd.DataFrame(ranking_list).sort_values("TOTAL", ascending=False)
            
            def get_team_info(usuario):
                row = df_users_ranking[df_users_ranking['Usuario'] == usuario]
                team = row['Equipo'].values[0] if not row.empty and 'Equipo' in row.columns else "McLaren"
                return EQUIPOS_DATA.get(team, EQUIPOS_DATA["McLaren"])

        with subtab_gen:
            if not df_final.empty:
                top_3 = df_final.head(3).to_dict('records')
                n_jugadores = len(top_3)
                
                # Usamos el contenedor con el estilo pedestal
                st.markdown('<div class="podium-container">', unsafe_allow_html=True)
                cols = st.columns([1, 1.2, 1])
                
                orden_podio = [
                    {"rank_idx": 1, "css": "p2", "label": "P2"}, # Izquierda
                    {"rank_idx": 0, "css": "p1", "label": "P1"}, # Centro
                    {"rank_idx": 2, "css": "p3", "label": "P3"}  # Derecha
                ]

                for i, conf in enumerate(orden_podio):
                    idx = conf["rank_idx"]
                    if idx < n_jugadores:
                        d = top_3[idx]
                        team = get_team_info(d['Piloto'])
                        with cols[i]:
                            st.markdown(f"""
                                <div class="podium-card {conf['css']}">
                                    <div class="rank-label">{conf['label']}</div>
                                    <div style="flex-grow: 1; display: flex; align-items: center; justify-content: center;">
                                        <img src="{team['logo']}" width="80">
                                    </div>
                                    <div class="driver-name">{d['Piloto']}</div>
                                    <div class="points-label">{int(d['TOTAL'])} PTS</div>
                                </div>
                            """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.divider()

                # Resto de la parrilla
                if len(df_final) > 3:
                    rest_parrilla = df_final.iloc[3:]
                    for idx, row in rest_parrilla.iterrows():
                        team = get_team_info(row['Piloto'])
                        pos = list(df_final['Piloto']).index(row['Piloto']) + 1
                        st.markdown(f"""
                            <div class="driver-card" style="border-left-color: {team['color']};">
                                <div style="display:flex; align-items:center; gap:20px;">
                                    <span style="font-family:Orbitron; font-size:1.6em; width:45px; font-weight:800;">{pos}</span>
                                    <img src="{team['logo']}" width="40">
                                    <span style="font-size:1.2em; font-weight:700;">{row['Piloto']}</span>
                                </div>
                                <div style="text-align:right;">
                                    <span style="font-family:Orbitron; color:#00ff00; font-size:1.4em; font-weight:800;">{int(row['TOTAL'])} PTS</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

    with tab3:
        st.header("🏆 Mundial de Temporada")
        if st.session_state.rol == 'admin':
            st.warning("⚠️ Los administradores no participan en el Mundial.")
        else:
            if MUNDIAL_BLOQUEADO:
                st.info("🔒 El mercado de fichajes está cerrado. Estas son tus apuestas:")
                df_u_temp = df_temp[df_temp['Usuario'] == st.session_state.user]
                if not df_u_temp.empty:
                    st.dataframe(df_u_temp[['Variable', 'Valor']], use_container_width=True, hide_index=True)
                else:
                    st.error("No realizaste predicciones antes del cierre.")
            else:
                st.success(f"⏳ Tienes hasta el {FECHA_LIMITE_TEMPORADA.strftime('%d/%m %H:%M')} para configurar tu parrilla.")
                df_u_temp = df_temp[df_temp['Usuario'] == st.session_state.user]
                
                with st.form("form_mundial_completo"):
                    c_pil, c_equ = st.columns(2)
                    
                    with c_pil:
                        st.subheader("👤 Top Pilotos")
                        res_p_raw = []
                        for i in range(22):
                            v_actual = df_u_temp[df_u_temp['Variable'] == f"P{i+1}"]['Valor'].values
                            idx = get_idx_emoji(v_actual[0]) if len(v_actual)>0 else 0
                            res_p_raw.append(st.selectbox(f"P{i+1}", PILOTOS_CON_EMOJI, index=idx, key=f"m_p_{i}"))
                    
                    with c_equ:
                        st.subheader("🏎️ Top Equipos")
                        res_e = []
                        for i in range(11):
                            v_actual = df_u_temp[df_u_temp['Variable'] == f"E{i+1}"]['Valor'].values
                            idx = (EQUIPOS_2026.index(v_actual[0])+1) if (len(v_actual)>0 and v_actual[0] in EQUIPOS_2026) else 0
                            res_e.append(st.selectbox(f"E{i+1}", ["- Seleccionar -"] + EQUIPOS_2026, index=idx, key=f"m_e_{i}"))
                    
                    if st.form_submit_button("💾 Guardar Mundial 2026"):
                        # Limpiamos emojis
                        res_p = [p.split(" ", 1)[-1] for p in res_p_raw]
                        if "- Seleccionar -" in res_p or "- Seleccionar -" in res_e:
                            st.error("⚠️ Debes completar todas las posiciones.")
                        elif len(set(res_p)) < 22 or len(set(res_e)) < 11:
                            st.error("⚠️ ¡Hay duplicados! Revisa que no hayas repetido pilotos o equipos.")
                        else:
                            new_m = []
                            for i, v in enumerate(res_p): new_m.append({"Usuario": st.session_state.user, "Variable": f"P{i+1}", "Valor": v})
                            for i, v in enumerate(res_e): new_m.append({"Usuario": st.session_state.user, "Variable": f"E{i+1}", "Valor": v})
                            df_temp = pd.concat([df_temp[df_temp['Usuario'] != st.session_state.user], pd.DataFrame(new_m)])
                            conn.update(worksheet="Temporada", data=df_temp)
                            st.success("✅ ¡Mundial guardado! Nos vemos en Abu Dabi.")


    with tab4:
        if st.session_state.rol == 'admin':
            adm_gp, adm_final, adm_fechas = st.tabs(["🏁 Resultados GP", "🌎 Mundial Final", "📅 Fechas Límite"])
            
            with adm_gp:
                st.subheader(f"Publicar Resultados Reales: {gp_sel}")
                with st.form("admin_gp_results"):
                    ac1, ac2 = st.columns(2)
                    with ac1:
                        st.markdown("**Top 5 Clasificación**")
                        aq = [st.selectbox(f"Q{i+1} Real", ["- Seleccionar -"] + PILOTOS_2026, index=0, key=f"arq{i}") for i in range(5)]
                        st.markdown("**Top 5 Carrera**")
                        ac = [st.selectbox(f"C{i+1} Real", ["- Seleccionar -"] + PILOTOS_2026, index=0, key=f"arc{i}") for i in range(5)]
                    
                    with ac2:
                        st.markdown("**Eventos y Españoles**")
                        res_alo = st.selectbox("Alonso Real", POSICIONES_CARRERA, index=0, key="ara_adm")
                        res_sai = st.selectbox("Sainz Real", POSICIONES_CARRERA, index=0, key="ars_adm")
                        res_sf = st.selectbox("Safety / VSC Real", ["- Seleccionar -", "SI", "NO"], index=0, key="arsf_adm")
                        res_rf = st.selectbox("Red Flag Real", ["- Seleccionar -", "SI", "NO"], index=0, key="arrf_adm")
                        
                        as_res = []
                        if es_sprint:
                            st.markdown("---")
                            st.markdown("**Top 3 Sprint**")
                            as_res = [st.selectbox(f"S{i+1} Real", ["- Seleccionar -"] + PILOTOS_2026, index=0, key=f"arsprint{i}") for i in range(3)]
                    
                    if st.form_submit_button("📢 Publicar Resultados"):
                        check_list = aq + ac + as_res + [res_alo, res_sai, res_sf, res_rf]
                        if "- Seleccionar -" in check_list:
                            st.error("⚠️ Error: El Admin debe seleccionar todos los campos reales.")
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

            with adm_final:
                st.subheader("Resultados Finales del Campeonato")
                st.info("Solo rellenar tras el GP de Abu Dabi.")
                with st.form("admin_mundial_final"):
                    am1, am2 = st.columns(2)
                    f_p = [am1.selectbox(f"P{i+1} Mundial", ["- Seleccionar -"] + PILOTOS_2026, index=0, key=f"fin_p_{i}") for i in range(22)]
                    f_e = [am2.selectbox(f"E{i+1} Mundial", ["- Seleccionar -"] + EQUIPOS_2026, index=0, key=f"fin_e_{i}") for i in range(11)]
                    
                    if st.form_submit_button("🏆 Publicar Mundial Final"):
                        if "- Seleccionar -" in f_p or "- Seleccionar -" in f_e:
                            st.error("⚠️ Debes completar toda la parrilla final.")
                        else:
                            m_f = []
                            for i, v in enumerate(f_p): m_f.append({"Variable": f"P{i+1}", "Valor": v})
                            for i, v in enumerate(f_e): m_f.append({"Variable": f"E{i+1}", "Valor": v})
                            conn.update(worksheet="ResultadosMundial", data=pd.DataFrame(m_f))
                            st.success("🏆 Resultados del mundial guardados.")

            with adm_fechas:
                st.subheader("Configurar Horarios de Cierre")
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
