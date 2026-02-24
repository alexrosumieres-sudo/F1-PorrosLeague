import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. CONFIGURACIONES
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

FECHA_LIMITE_TEMPORADA = datetime(2026, 3, 1, 10, 0)
MUNDIAL_BLOQUEADO = datetime.now() > FECHA_LIMITE_TEMPORADA
GPS = ["GP Bahrein", "GP Arabia Saudí", "GP Australia", "GP Japón", "GP China", "GP Miami", "GP Mónaco", "GP España"]

# 2. FUNCIONES DE CÁLCULO
def calcular_puntos_gp(u_preds, gp_results):
    pts = 0.0
    if u_preds.empty or gp_results.empty: return 0.0
    real_q = gp_results[gp_results['Variable'].str.contains('Q')].sort_values('Variable')['Valor'].tolist()
    real_c = gp_results[gp_results['Variable'].str.contains('C')].sort_values('Variable')['Valor'].tolist()
    for _, row in u_preds.iterrows():
        var, val_p = row['Variable'], row['Valor']
        res_row = gp_results[gp_results['Variable'] == var]
        if res_row.empty: continue
        val_r = res_row.iloc[0]['Valor']
        if var.startswith('Q') or var.startswith('C'):
            lista_real = real_q if var.startswith('Q') else real_c
            try:
                pos_pred = int(var[1:])
                if val_p == val_r: pts += 2.0
                elif val_p in lista_real:
                    pos_real = lista_real.index(val_p) + 1
                    pts += 1.5 if abs(pos_pred - pos_real) == 1 else 0.5
            except: pass
        elif var in ['Alonso', 'Sainz']:
            try:
                if int(val_p) == int(val_r): pts += 1.0
                elif abs(int(val_p) - int(val_r)) == 1: pts += 0.5
            except: pass
        elif var in ['Safety', 'RedFlag', 'DNF', 'DOTD']:
            if str(val_p).lower() == str(val_r).lower(): pts += 2.0
    return pts

# 3. INTERFAZ Y LOGIN
st.set_page_config(page_title="F1 Porra 2026", page_icon="🏎️", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos(pestana):
    try: return conn.read(worksheet=pestana, ttl=0)
    except: return pd.DataFrame()

if 'auth' not in st.session_state: 
    st.session_state.auth = False

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
                    pwd = str(df_u[df_u['Usuario']==u]['Password'].values[0])
                    if p == pwd:
                        st.session_state.auth, st.session_state.user = True, u
                        st.session_state.rol = df_u[df_u['Usuario']==u]['Rol'].values[0]
                        st.rerun()
                st.error("Usuario o contraseña incorrectos")

    with tab_registro:
        with st.form("Registro"):
            new_u = st.text_input("Elige nombre de usuario")
            new_p = st.text_input("Elige contraseña", type="password")
            confirm_p = st.text_input("Confirma contraseña", type="password")
            if st.form_submit_button("Crear cuenta"):
                df_u = leer_datos("Usuarios")
                if not new_u or not new_p: st.warning("Rellena todos los campos")
                elif new_p != confirm_p: st.error("Las contraseñas no coinciden")
                elif not df_u.empty and new_u in df_u['Usuario'].values: st.error("El usuario ya existe")
                else:
                    nuevo_registro = pd.DataFrame([{"Usuario": new_u, "Password": new_p, "Rol": "user"}])
                    if df_u.empty: df_u = pd.DataFrame(columns=["Usuario", "Password", "Rol"])
                    conn.update(worksheet="Usuarios", data=pd.concat([df_u, nuevo_registro], ignore_index=True))
                    st.success("✅ ¡Registro completado!")
else:
    # 4. CARGA DE DATOS Y DEFINICIÓN DE TABS
    df_p = leer_datos("Predicciones")
    df_r = leer_datos("Resultados")
    
    st.sidebar.title(f"Piloto: {st.session_state.user}")
    gp_sel = st.sidebar.selectbox("Gran Premio", GPS)
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()
    
    # DEFINICIÓN DE LAS 4 TABS CORRECCIÓN AQUÍ
    # Definición de las 4 pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs(["✍️ Mis Apuestas", "📊 Clasificación", "🏆 Mundial", "⚙️ Admin"])

    with tab1:
        st.header(f"✍️ Mis Apuestas - {gp_sel}")
        
        # REGLA 1: El Admin no puede realizar predicciones
        if st.session_state.rol == 'admin':
            st.warning("⚠️ Los administradores no participan en las apuestas para mantener la limpieza de la competición.")
        else:
            # REGLA 4: Cargar predicciones previas si existen
            user_gp_preds = df_p[(df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel)]
            
            def get_val(var, default_val):
                match = user_gp_preds[user_gp_preds['Variable'] == var]
                return match.iloc[0]['Valor'] if not match.empty else default_val

            with st.form("apuestas_gp"):
                c1, c2 = st.columns(2)
                
                with c1:
                    st.subheader("⏱️ Clasificación")
                    q_res = []
                    for i in range(5):
                        saved_q = get_val(f"Q{i+1}", PILOTOS_2026[0])
                        idx_q = PILOTOS_2026.index(saved_q) if saved_q in PILOTOS_2026 else 0
                        q_res.append(st.selectbox(f"P{i+1} Qualy", PILOTOS_2026, index=idx_q, key=f"q_sel_{i}"))
                
                with c2:
                    st.subheader("🏁 Carrera")
                    c_res = []
                    for i in range(5):
                        saved_c = get_val(f"C{i+1}", PILOTOS_2026[0])
                        idx_c = PILOTOS_2026.index(saved_c) if saved_c in PILOTOS_2026 else 0
                        c_res.append(st.selectbox(f"P{i+1} Carrera", PILOTOS_2026, index=idx_c, key=f"c_sel_{i}"))

                st.divider()
                c3, c4 = st.columns(2)
                with c3:
                    st.subheader("🇪🇸 Españoles")
                    # REGLA 3: Valores predeterminados no son fijos, son los guardados
                    val_alo = int(get_val("Alonso", 14))
                    val_sai = int(get_val("Sainz", 5))
                    alo = st.number_input("Pos. Alonso", 1, 22, val_alo)
                    sai = st.number_input("Pos. Sainz Jr.", 1, 22, val_sai)
                with c4:
                    st.subheader("🎲 Caos")
                    val_sf = get_val("Safety", "NO")
                    val_rf = get_val("RedFlag", "NO")
                    saf = st.selectbox("¿Habrá Safety Car?", ["SI", "NO"], index=0 if val_sf == "SI" else 1)
                    red = st.selectbox("¿Habrá Bandera Roja?", ["SI", "NO"], index=0 if val_rf == "SI" else 1)

                if st.form_submit_button("💾 Guardar Predicción GP"):
                    data_env = []
                    for i, v in enumerate(q_res): data_env.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                    for i, v in enumerate(c_res): data_env.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                    data_env.extend([
                        {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Alonso", "Valor": str(alo)},
                        {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Sainz", "Valor": str(sai)},
                        {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Safety", "Valor": saf},
                        {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "RedFlag", "Valor": red}
                    ])
                    # Limpiar anteriores y concatenar
                    df_p = pd.concat([df_p[~((df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel))], pd.DataFrame(data_env)])
                    conn.update(worksheet="Predicciones", data=df_p)
                    st.success("✅ Predicciones de GP guardadas correctamente.")

    with tab2:
        st.header("📊 Clasificación General")
        df_u_rank = leer_datos("Usuarios", conn)
        if not df_u_rank.empty:
            # Filtramos solo usuarios que no sean admin para el ranking
            participantes = df_u_rank[df_u_rank['Rol'] != 'admin']['Usuario'].unique()
            ranking = []
            for u in participantes:
                p_total = sum([calcular_puntos_gp(df_p[(df_p['Usuario'] == u) & (df_p['GP'] == g)], df_r[df_r['GP'] == g]) for g in GPS])
                ranking.append({"Piloto": u, "Puntos": p_total})
            
            df_final_rank = pd.DataFrame(ranking).sort_values("Puntos", ascending=False)
            st.table(df_final_rank)
        else:
            st.info("Aún no hay pilotos registrados.")

    with tab3:
        st.header("🏆 Mundial de Temporada")
        if MUNDIAL_BLOQUEADO:
            st.warning("🔒 Las apuestas de temporada están cerradas.")
        
        # Cargar guardados de temporada
        df_u_temp = df_t[df_t['Usuario'] == st.session_state.user]
        
        with st.form("form_temporada"):
            col_pil, col_equ = st.columns(2)
            
            with col_pil:
                st.subheader("👤 Mundial Pilotos")
                pred_p = []
                for i in range(22):
                    # Cargar guardado o primer piloto
                    match_p = df_u_temp[df_u_temp['Variable'] == f"P{i+1}"]
                    default_p = match_p.iloc[0]['Valor'] if not match_p.empty else PILOTOS_2026[i]
                    p_sel = st.selectbox(f"P{i+1}", PILOTOS_2026, index=PILOTOS_2026.index(default_p), key=f"tp_{i}", disabled=MUNDIAL_BLOQUEADO)
                    pred_p.append(p_sel)

            with col_equ:
                st.subheader("🏎️ Mundial Equipos")
                pred_e = []
                for i in range(11):
                    # Cargar guardado o primer equipo
                    match_e = df_u_temp[df_u_temp['Variable'] == f"E{i+1}"]
                    default_e = match_e.iloc[0]['Valor'] if not match_e.empty else EQUIPOS_2026[i]
                    e_sel = st.selectbox(f"E{i+1}", EQUIPOS_2026, index=EQUIPOS_2026.index(default_e), key=f"te_{i}", disabled=MUNDIAL_BLOQUEADO)
                    pred_e.append(e_sel)

            if st.form_submit_button("💾 Guardar Mundial", disabled=MUNDIAL_BLOQUEADO):
                # REGLA 2: Validación de duplicados
                if len(set(pred_p)) < 22:
                    st.error("⚠️ Error: Has seleccionado al mismo piloto en varias posiciones.")
                elif len(set(pred_e)) < 11:
                    st.error("⚠️ Error: Has seleccionado a la misma escudería en varias posiciones.")
                else:
                    m_env = []
                    for i, v in enumerate(pred_p): m_env.append({"Usuario": st.session_state.user, "Variable": f"P{i+1}", "Valor": v})
                    for i, v in enumerate(pred_e): m_env.append({"Usuario": st.session_state.user, "Variable": f"E{i+1}", "Valor": v})
                    
                    df_t = pd.concat([df_t[df_t['Usuario'] != st.session_state.user], pd.DataFrame(m_env)])
                    conn.update(worksheet="Temporada", data=df_t)
                    st.success("✅ Tu apuesta para el Mundial ha sido guardada.")

    with tab4:
        if st.session_state.rol == 'admin':
            st.header("⚙️ Panel de Control Admin")
            with st.form("admin_results"):
                st.subheader(f"Publicar Resultados Reales: {gp_sel}")
                ac1, ac2 = st.columns(2)
                with ac1:
                    res_q = [st.selectbox(f"Q{i+1} Real", PILOTOS_2026, key=f"rq{i}") for i in range(5)]
                    res_c = [st.selectbox(f"C{i+1} Real", PILOTOS_2026, key=f"rc{i}") for i in range(5)]
                with ac2:
                    res_alo = st.number_input("Alonso Real", 1, 22, key="ra")
                    res_sai = st.number_input("Sainz Real", 1, 22, key="rs")
                    res_sf = st.selectbox("Safety Car Real", ["SI", "NO"], key="rsf")
                    res_rf = st.selectbox("Red Flag Real", ["SI", "NO"], key="rrf")
                
                if st.form_submit_button("📢 Publicar Resultados"):
                    r_data = []
                    for i, v in enumerate(res_q): r_data.append({"GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                    for i, v in enumerate(res_c): r_data.append({"GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                    r_data.extend([
                        {"GP": gp_sel, "Variable": "Alonso", "Valor": str(res_alo)},
                        {"GP": gp_sel, "Variable": "Sainz", "Valor": str(res_sai)},
                        {"GP": gp_sel, "Variable": "Safety", "Valor": res_sf},
                        {"GP": gp_sel, "Variable": "RedFlag", "Valor": res_rf}
                    ])
                    df_r = pd.concat([df_r[df_r['GP'] != gp_sel], pd.DataFrame(r_data)])
                    conn.update(worksheet="Resultados", data=df_r)
                    st.success("🏁 Resultados publicados y puntos actualizados.")
        else:
            st.error("⛔ No tienes permisos para acceder a esta sección.")
