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

GPS = [
    "01. GP de Australia", 
    "02. GP de China", 
    "03. GP de Japón", 
    "04. GP de Baréin",
    "05. GP de Arabia Saudita", 
    "06. GP de Miami", 
    "07. GP de Canadá", 
    "08. GP de Mónaco",
    "09. GP de Barcelona-Cataluña", 
    "10. GP de Austria", 
    "11. GP de Gran Bretaña", 
    "12. GP de Bélgica",
    "13. GP de Hungría", 
    "14. GP de los Países Bajos", 
    "15. GP de Italia", 
    "16. GP de España (Madrid)",
    "17. GP de Azerbaiyán", 
    "18. GP de Singapur", 
    "19. GP de Estados Unidos", 
    "20. GP de Ciudad de México",
    "21. GP de São Paulo", 
    "22. GP de Las Vegas", 
    "23. GP de Catar", 
    "24. GP de Abu Dabi"
]

# También actualizamos la fecha límite del Mundial (Australia es el 8 de marzo)
# Ponemos el cierre el 8 de marzo a las 05:00 AM (antes de la carrera)
FECHA_LIMITE_TEMPORADA = datetime(2026, 3, 8, 5, 0)
MUNDIAL_BLOQUEADO = datetime.now() > FECHA_LIMITE_TEMPORADA
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

def calcular_puntos_gp(u_preds, gp_results, detalle=False):
    pts = 0.0
    desglose = {"Qualy": 0.0, "Carrera": 0.0, "Extras": 0.0}
    
    if u_preds.empty or gp_results.empty: 
        return desglose if detalle else 0.0
        
    real_q = gp_results[gp_results['Variable'].str.contains('Q')].sort_values('Variable')['Valor'].tolist()
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
            
        elif var in ['Alonso', 'Sainz']:
            try:
                if str(val_p) == str(val_r): puntos_esta_var = 1.0
                elif val_p != "DNF" and val_r != "DNF" and abs(int(val_p) - int(val_r)) == 1:
                    puntos_esta_var = 0.5
            except: pass
            desglose["Extras"] += puntos_esta_var
        elif var in ['Safety', 'RedFlag']:
            if str(val_p).lower() == str(val_r).lower(): puntos_esta_var = 2.0
            desglose["Extras"] += puntos_esta_var
            
        pts += puntos_esta_var

    return desglose if detalle else pts


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
    # 4. CARGA DE DATOS
    df_p = leer_datos("Predicciones")
    df_r = leer_datos("Resultados")
    df_temp = leer_datos("Temporada")
    # Intentamos leer la hoja de resultados finales del mundial
    df_r_mundial = leer_datos("ResultadosMundial") 

    # Blindaje: Si las hojas están vacías, creamos DataFrames con columnas mínimas
    if df_p.empty: df_p = pd.DataFrame(columns=['Usuario', 'GP', 'Variable', 'Valor'])
    if df_r.empty: df_r = pd.DataFrame(columns=['GP', 'Variable', 'Valor'])
    if df_temp.empty: df_temp = pd.DataFrame(columns=['Usuario', 'Variable', 'Valor'])
    if df_r_mundial.empty: df_r_mundial = pd.DataFrame(columns=['Variable', 'Valor'])
    
    # Limpieza: quitamos espacios raros en los nombres de las columnas
    df_p.columns = df_p.columns.str.strip()
    df_r.columns = df_r.columns.str.strip()
    df_temp.columns = df_temp.columns.str.strip()
    if not df_r_mundial.empty:
        df_r_mundial.columns = df_r_mundial.columns.str.strip()

    # DEFINICIÓN DE LISTAS DE OPCIONES (Blindado contra NameError)
    OPCIONES_PILOTOS = ["- Seleccionar -"] + PILOTOS_2026
    OPCIONES_EQUIPOS = ["- Seleccionar -"] + EQUIPOS_2026
    OPCIONES_BINARIAS = ["- Seleccionar -", "SI", "NO"]
    POSICIONES_CARRERA = ["- Seleccionar -", "DNF"] + [str(i) for i in range(1, 23)]

    # Sidebar
    st.sidebar.title(f"Piloto: {st.session_state.user}")
    gp_sel = st.sidebar.selectbox("Gran Premio", GPS)
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # Definición de las 4 pestañas principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✍️ Mis Apuestas", "📊 Clasificación", "🏆 Mundial", "⚙️ Admin", "🔍 El Muro"])

    with tab1:
        st.header(f"✍️ Mis Apuestas - {gp_sel}")
        if st.session_state.rol == 'admin':
            st.warning("⚠️ Los administradores no participan en las apuestas.")
        else:
            user_gp_preds = df_p[(df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel)]
            def get_val(var, default_val):
                match = user_gp_preds[user_gp_preds['Variable'] == var]
                return match.iloc[0]['Valor'] if not match.empty else default_val

            with st.form("apuestas_gp"):
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("⏱️ Clasificación")
                    q_res = [st.selectbox(f"P{i+1} Qualy", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val(f"Q{i+1}", "- Seleccionar -")), key=f"q{i}") for i in range(5)]
                with c2:
                    st.subheader("🏁 Carrera")
                    c_res = [st.selectbox(f"P{i+1} Carrera", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val(f"C{i+1}", "- Seleccionar -")), key=f"c{i}") for i in range(5)]
                
                st.divider()
                c3, c4 = st.columns(2)
                with c3:
                    st.subheader("🇪🇸 Españoles")
                    alo = st.selectbox("Pos. Alonso", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Alonso", "- Seleccionar -")))
                    sai = st.selectbox("Pos. Sainz Jr.", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Sainz", "- Seleccionar -")))
                with c4:
                    st.subheader("🎲 Caos")
                    saf = st.selectbox("¿Habrá Safety Car?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("Safety", "- Seleccionar -")))
                    red = st.selectbox("¿Habrá Bandera Roja?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("RedFlag", "- Seleccionar -")))

                if st.form_submit_button("💾 Guardar Predicción GP"):
                    if "- Seleccionar -" in q_res + c_res + [alo, sai, saf, red]:
                        st.error("⚠️ Completa todos los campos.")
                    else:
                        data = []
                        for i, v in enumerate(q_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        for i, v in enumerate(c_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        data.extend([{"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Alonso", "Valor": alo},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Sainz", "Valor": sai},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Safety", "Valor": saf},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "RedFlag", "Valor": red}])
                        df_p = pd.concat([df_p[~((df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel))], pd.DataFrame(data)])
                        conn.update(worksheet="Predicciones", data=df_p)
                        st.success("✅ Guardado.")

    with tab2:
        st.header("📊 Clasificación General")
        df_u_rank = leer_datos("Usuarios")
        if not df_u_rank.empty:
            participantes = df_u_rank[df_u_rank['Rol'] == 'user']['Usuario'].unique()
            
            # --- LÓGICA DE RANKING Y EVOLUCIÓN ---
            ranking_list = []
            evolution_data = [] # Para el gráfico
            
            for u in participantes:
                p_acumulados = 0
                for g in GPS:
                    u_p = df_p[(df_p['Usuario'] == u) & (df_p['GP'] == g)]
                    g_r = df_r[df_r['GP'] == g]
                    pts_gp = calcular_puntos_gp(u_p, g_r)
                    p_acumulados += pts_gp
                    evolution_data.append({"Usuario": u, "GP": g[:3], "Puntos": p_acumulados}) # g[:3] para que no sea muy ancho
                
                ranking_list.append({"Piloto": u, "Puntos": p_acumulados})

            # 1. Gráfico de Evolución
            st.subheader("📈 Evolución del Campeonato")
            df_evol = pd.DataFrame(evolution_data)
            st.line_chart(df_evol.pivot(index="GP", columns="Usuario", values="Puntos"))

            # 2. Tabla de Clasificación
            st.subheader("🏁 Puntuación Actual")
            df_final_rank = pd.DataFrame(ranking_list).sort_values("Puntos", ascending=False)
            df_final_rank.insert(0, "Pos", range(1, len(df_final_rank) + 1))
            st.dataframe(df_final_rank, use_container_width=True, hide_index=True)

            # 3. Historial de Puntos por GP (Desglose)
            st.divider()
            st.subheader("🧐 Historial Detallado")
            col_u, col_g = st.columns(2)
            u_ver = col_u.selectbox("Selecciona Piloto", participantes)
            g_ver = col_g.selectbox("Selecciona GP", GPS)
            
            det = calcular_puntos_gp(df_p[(df_p['Usuario']==u_ver) & (df_p['GP']==g_ver)], df_r[df_r['GP']==g_ver], detalle=True)
            
            c_q, c_c, c_e, c_t = st.columns(4)
            c_q.metric("Qualy", det["Qualy"])
            c_c.metric("Carrera", det["Carrera"])
            c_e.metric("Extras", det["Extras"])
            c_t.metric("Total GP", sum(det.values()))

    with tab3:
        st.header("🏆 Mundial de Temporada")
        st.warning("🔒 El periodo de predicciones para el Mundial ha finalizado.")
        df_u_temp = df_temp[df_temp['Usuario'] == st.session_state.user]
        if not df_u_temp.empty:
            st.write("Tus predicciones guardadas:")
            st.dataframe(df_u_temp[['Variable', 'Valor']], use_container_width=True, hide_index=True)
        else:
            st.info("No realizaste predicciones de temporada.")

    with tab4: # ADMIN
        if st.session_state.rol == 'admin':
            sub_tab_gp, sub_tab_mundial = st.tabs(["🏁 Resultados GP", "🌎 Resultados Mundial Final"])
            with sub_tab_gp:
                with st.form("admin_gp"):
                    st.subheader(f"Resultados Reales: {gp_sel}")
                    ac1, ac2 = st.columns(2)
                    res_q = [ac1.selectbox(f"Q{i+1} Real", PILOTOS_2026, key=f"rq{i}") for i in range(5)]
                    res_c = [ac1.selectbox(f"C{i+1} Real", PILOTOS_2026, key=f"rc{i}") for i in range(5)]
                    res_alo = ac2.selectbox("Alonso Real", POSICIONES_CARRERA, key="ra")
                    res_sai = ac2.selectbox("Sainz Real", POSICIONES_CARRERA, key="rs")
                    res_sf = ac2.selectbox("Safety Real", OPCIONES_BINARIAS[1:], key="rsf")
                    res_rf = ac2.selectbox("Red Flag Real", OPCIONES_BINARIAS[1:], key="rrf")
                    if st.form_submit_button("📢 Publicar Resultados GP"):
                        r_data = []
                        for i, v in enumerate(res_q): r_data.append({"GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        for i, v in enumerate(res_c): r_data.append({"GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        r_data.extend([{"GP": gp_sel, "Variable": "Alonso", "Valor": res_alo}, {"GP": gp_sel, "Variable": "Sainz", "Valor": res_sai},
                                       {"GP": gp_sel, "Variable": "Safety", "Valor": res_sf}, {"GP": gp_sel, "Variable": "RedFlag", "Valor": res_rf}])
                        df_r = pd.concat([df_r[df_r['GP'] != gp_sel], pd.DataFrame(r_data)])
                        conn.update(worksheet="Resultados", data=df_r)
                        st.success("🏁 Resultados publicados.")

            with sub_tab_mundial:
                st.subheader("Subir Clasificación Final de la Temporada 2026")
                with st.form("admin_mundial_final"):
                    am1, am2 = st.columns(2)
                    final_p = [am1.selectbox(f"P{i+1} Final Mundial", PILOTOS_2026, key=f"fp{i}") for i in range(22)]
                    final_e = [am2.selectbox(f"E{i+1} Final Mundial", EQUIPOS_2026, key=f"fe{i}") for i in range(11)]
                    if st.form_submit_button("🏆 Publicar Resultados Mundial"):
                        m_final = []
                        for i, v in enumerate(final_p): m_final.append({"Variable": f"P{i+1}", "Valor": v})
                        for i, v in enumerate(final_e): m_final.append({"Variable": f"E{i+1}", "Valor": v})
                        conn.update(worksheet="ResultadosMundial", data=pd.DataFrame(m_final))
                        st.success("🏆 Resultados finales del Mundial guardados.")
        else:
            st.error("⛔ Solo administradores pueden ver esta sección.")

with tab5: # TRANSPARENCIA
        st.header("🔍 El Muro de la Verdad")
        st.info("Aquí puedes ver qué han apostado tus rivales para el GP seleccionado.")
        
        # Filtramos predicciones para el GP seleccionado
        df_muro = df_p[df_p['GP'] == gp_sel].copy()
        
        if df_muro.empty:
            st.warning("Nadie ha apostado todavía para este Gran Premio.")
        else:
            # Pivotamos la tabla para que los usuarios sean filas y las variables columnas
            df_pivot = df_muro.pivot(index='Usuario', columns='Variable', values='Valor')
            
            # Reordenamos las columnas para que tengan sentido
            cols_ordenadas = [f'Q{i+1}' for i in range(5)] + [f'C{i+1}' for i in range(5)] + ['Alonso', 'Sainz', 'Safety', 'RedFlag']
            # Solo columnas que existan en el pivot
            cols_finales = [c for c in cols_ordenadas if c in df_pivot.columns]
            
            st.dataframe(df_pivot[cols_finales], use_container_width=True)
