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
    desglose = {"Qualy": 0.0, "Sprint": 0.0, "Carrera": 0.0, "Extras": 0.0}
    
    if u_preds.empty or gp_results.empty: 
        return desglose if detalle else 0.0
        
    real_q = gp_results[gp_results['Variable'].str.contains('Q')].sort_values('Variable')['Valor'].tolist()
    real_s = gp_results[gp_results['Variable'].str.contains('S')].sort_values('Variable')['Valor'].tolist()
    real_c = gp_results[gp_results['Variable'].str.contains('C')].sort_values('Variable')['Valor'].tolist()

    for _, row in u_preds.iterrows():
        var, val_p = row['Variable'], row['Valor']
        res_row = gp_results[gp_results['Variable'] == var]
        if res_row.empty: continue
        val_r = res_row.iloc[0]['Valor']
        
        puntos_esta_var = 0.0
        
        # Lógica para Qualy (Q), Sprint (S) y Carrera (C)
        if var[0] in ['Q', 'S', 'C']:
            lista_real = real_q if var[0] == 'Q' else (real_s if var[0] == 'S' else real_c)
            try:
                pos_pred = int(var[1:])
                if val_p == val_r: 
                    puntos_esta_var = 2.0
                elif val_p in lista_real:
                    pos_real = lista_real.index(val_p) + 1
                    puntos_esta_var = 1.5 if abs(pos_pred - pos_real) == 1 else 0.5
            except: pass
            
            if var.startswith('Q'): desglose["Qualy"] += puntos_esta_var
            elif var.startswith('S'): desglose["Sprint"] += puntos_esta_var
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
    df_r_mundial = leer_datos("ResultadosMundial") 

    SPRINT_GPS = ["02. GP de China", "06. GP de Miami", "07. GP de Canadá", "11. GP de Gran Bretaña", "14. GP de los Países Bajos", "18. GP de Singapur"]

    if df_p.empty: df_p = pd.DataFrame(columns=['Usuario', 'GP', 'Variable', 'Valor'])
    if df_r.empty: df_r = pd.DataFrame(columns=['GP', 'Variable', 'Valor'])
    if df_temp.empty: df_temp = pd.DataFrame(columns=['Usuario', 'Variable', 'Valor'])
    
    df_p.columns = df_p.columns.str.strip()
    df_r.columns = df_r.columns.str.strip()
    df_temp.columns = df_temp.columns.str.strip()

    OPCIONES_PILOTOS = ["- Seleccionar -"] + PILOTOS_2026
    OPCIONES_EQUIPOS = ["- Seleccionar -"] + EQUIPOS_2026
    OPCIONES_BINARIAS = ["- Seleccionar -", "SI", "NO"]
    POSICIONES_CARRERA = ["- Seleccionar -", "DNF"] + [str(i) for i in range(1, 23)]

    st.sidebar.title(f"Piloto: {st.session_state.user}")
    gp_sel = st.sidebar.selectbox("Gran Premio", GPS)
    es_sprint = gp_sel in SPRINT_GPS
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✍️ Apuestas", "📊 Clasificación", "🏆 Mundial", "⚙️ Admin", "🔍 El Muro"])

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
                    st.subheader("⏱️ Clasificación (Top 5)")
                    q_res = [st.selectbox(f"Q{i+1}", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val(f"Q{i+1}", "- Seleccionar -")), key=f"q{i}") for i in range(5)]
                with c2:
                    st.subheader("🏁 Carrera (Top 5)")
                    c_res = [st.selectbox(f"C{i+1}", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val(f"C{i+1}", "- Seleccionar -")), key=f"c{i}") for i in range(5)]
                
                s_res = []
                if es_sprint:
                    st.divider()
                    st.subheader("🏎️ Sprint Race (Top 3)")
                    cs1, cs2, cs3 = st.columns(3)
                    s_res.append(cs1.selectbox("S1 (Ganador)", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("S1", "- Seleccionar -"))))
                    s_res.append(cs2.selectbox("S2", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("S2", "- Seleccionar -"))))
                    s_res.append(cs3.selectbox("S3", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("S3", "- Seleccionar -"))))

                st.divider()
                c3, c4 = st.columns(2)
                with c3:
                    st.subheader("🇪🇸 Españoles")
                    alo = st.selectbox("Pos. Alonso", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Alonso", "- Seleccionar -")))
                    sai = st.selectbox("Pos. Sainz Jr.", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Sainz", "- Seleccionar -")))
                with c4:
                    st.subheader("🎲 Caos")
                    saf = st.selectbox("¿Safety Car?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("Safety", "- Seleccionar -")))
                    red = st.selectbox("¿Bandera Roja?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("RedFlag", "- Seleccionar -")))

                if st.form_submit_button("💾 Guardar"):
                    todo = q_res + c_res + s_res + [alo, sai, saf, red]
                    if "- Seleccionar -" in todo:
                        st.error("⚠️ Completa todos los campos.")
                    else:
                        data = []
                        for i, v in enumerate(q_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        for i, v in enumerate(c_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        for i, v in enumerate(s_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"S{i+1}", "Valor": v})
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
            ranking_list, evolution_data = [], []
            for u in participantes:
                p_acum = 0
                for g in GPS:
                    pts_gp = calcular_puntos_gp(df_p[(df_p['Usuario']==u) & (df_p['GP']==g)], df_r[df_r['GP']==g])
                    p_acum += pts_gp
                    evolution_data.append({"Usuario": u, "GP": g[:3], "Puntos": p_acum})
                ranking_list.append({"Piloto": u, "Puntos": p_acum})
            
            st.line_chart(pd.DataFrame(evolution_data).pivot(index="GP", columns="Usuario", values="Puntos"))
            df_f = pd.DataFrame(ranking_list).sort_values("Puntos", ascending=False)
            df_f.insert(0, "Pos", range(1, len(df_f) + 1))
            st.dataframe(df_f, use_container_width=True, hide_index=True)

            st.divider()
            u_v = st.selectbox("Historial Detallado Piloto", participantes)
            g_v = st.selectbox("Historial Detallado GP", GPS)
            det = calcular_puntos_gp(df_p[(df_p['Usuario']==u_v) & (df_p['GP']==g_v)], df_r[df_r['GP']==g_v], detalle=True)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Qualy", det["Qualy"])
            c2.metric("Sprint", det["Sprint"])
            c3.metric("Carrera", det["Carrera"])
            c4.metric("Extras", det["Extras"])
            c5.metric("Total", sum(det.values()))

    with tab3:
        st.header("🏆 Mundial de Temporada")
        st.warning("🔒 El periodo de predicciones para el Mundial ha finalizado.")
        df_u_temp = df_temp[df_temp['Usuario'] == st.session_state.user]
        if not df_u_temp.empty:
            st.dataframe(df_u_temp[['Variable', 'Valor']], use_container_width=True, hide_index=True)

    with tab4:
        if st.session_state.rol == 'admin':
            s1, s2 = st.tabs(["🏁 Resultados GP", "🌎 Final Mundial"])
            with s1:
                with st.form("admin_gp"):
                    st.subheader(f"Resultados Reales: {gp_sel}")
                    ac1, ac2 = st.columns(2)
                    aq = [ac1.selectbox(f"Q{i+1} Real", PILOTOS_2026, key=f"rq{i}") for i in range(5)]
                    ac = [ac1.selectbox(f"C{i+1} Real", PILOTOS_2026, key=f"rc{i}") for i in range(5)]
                    as_res = []
                    if es_sprint:
                        st.write("---")
                        as_res = [st.selectbox(f"S{i+1} Real", PILOTOS_2026, key=f"rs{i}") for i in range(3)]
                    ralo = ac2.selectbox("Alonso Real", POSICIONES_CARRERA)
                    rsai = ac2.selectbox("Sainz Real", POSICIONES_CARRERA)
                    rsaf = ac2.selectbox("Safety Real", ["SI", "NO"])
                    rred = ac2.selectbox("RedFlag Real", ["SI", "NO"])
                    if st.form_submit_button("📢 Publicar"):
                        r_data = []
                        for i, v in enumerate(aq): r_data.append({"GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        for i, v in enumerate(ac): r_data.append({"GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        for i, v in enumerate(as_res): r_data.append({"GP": gp_sel, "Variable": f"S{i+1}", "Valor": v})
                        r_data.extend([{"GP": gp_sel, "Variable": "Alonso", "Valor": ralo}, {"GP": gp_sel, "Variable": "Sainz", "Valor": rsai},
                                       {"GP": gp_sel, "Variable": "Safety", "Valor": rsaf}, {"GP": gp_sel, "Variable": "RedFlag", "Valor": rred}])
                        df_r = pd.concat([df_r[df_r['GP'] != gp_sel], pd.DataFrame(r_data)])
                        conn.update(worksheet="Resultados", data=df_r)
                        st.success("🏁 Resultados actualizados.")

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

with tab5:
        st.header("🔍 El Muro de la Verdad")
        df_muro = df_p[df_p['GP'] == gp_sel].copy()
        if not df_muro.empty:
            df_piv = df_muro.pivot(index='Usuario', columns='Variable', values='Valor')
            cols = [f'Q{i+1}' for i in range(5)] + ([f'S{i+1}' for i in range(3)] if es_sprint else []) + [f'C{i+1}' for i in range(5)] + ['Alonso', 'Sainz', 'Safety', 'RedFlag']
            st.dataframe(df_piv[[c for c in cols if c in df_piv.columns]], use_container_width=True)
