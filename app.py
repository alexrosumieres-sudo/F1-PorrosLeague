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
    df_cal = leer_datos("Calendario")
    df_r_mundial = leer_datos("ResultadosMundial")

    SPRINT_GPS = ["02. GP de China", "06. GP de Miami", "07. GP de Canadá", "11. GP de Gran Bretaña", "14. GP de los Países Bajos", "18. GP de Singapur"]

    # Blindaje de datos
    if df_p.empty: df_p = pd.DataFrame(columns=['Usuario', 'GP', 'Variable', 'Valor'])
    if df_r.empty: df_r = pd.DataFrame(columns=['GP', 'Variable', 'Valor'])
    if df_cal.empty: df_cal = pd.DataFrame(columns=['GP', 'LimiteQualy', 'LimiteSprint', 'LimiteCarrera'])
    
    df_p.columns = df_p.columns.str.strip()
    df_cal.columns = df_cal.columns.str.strip()

    # --- LÓGICA DE BLOQUEO TRIPLE ---
    st.sidebar.title(f"Piloto: {st.session_state.user}")
    gp_sel = st.sidebar.selectbox("Seleccionar Gran Premio", GPS)
    
    cal_row = df_cal[df_cal['GP'] == gp_sel]
    now = datetime.now()

    # Inicializamos bloqueos por defecto (abiertos)
    q_bloq, s_bloq, c_bloq = False, False, False
    q_lim, s_lim, c_lim = None, None, None

    if not cal_row.empty:
        q_lim = pd.to_datetime(cal_row.iloc[0]['LimiteQualy'])
        c_lim = pd.to_datetime(cal_row.iloc[0]['LimiteCarrera'])
        q_bloq = now > q_lim
        c_bloq = now > c_lim
        
        st.sidebar.markdown(f"**⏱️ Qualy:** {'🔴 Cerrada' if q_bloq else f'🟢 hasta {q_lim.strftime('%H:%M (%d/%m)')}'}")
        
        if gp_sel in SPRINT_GPS:
            s_lim = pd.to_datetime(cal_row.iloc[0]['LimiteSprint'])
            s_bloq = now > s_lim
            st.sidebar.markdown(f"**🏎️ Sprint:** {'🔴 Cerrada' if s_bloq else f'🟢 hasta {s_lim.strftime('%H:%M (%d/%m)')}'}")
        
        st.sidebar.markdown(f"**🏁 Carrera:** {'🔴 Cerrada' if c_bloq else f'🟢 hasta {c_lim.strftime('%H:%M (%d/%m)')}'}")
    else:
        st.sidebar.warning("⚠️ Fechas límite no configuradas")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # Listas de opciones
    OPCIONES_PILOTOS = ["- Seleccionar -"] + PILOTOS_2026
    OPCIONES_EQUIPOS = ["- Seleccionar -"] + EQUIPOS_2026
    OPCIONES_BINARIAS = ["- Seleccionar -", "SI", "NO"]
    POSICIONES_CARRERA = ["- Seleccionar -", "DNF"] + [str(i) for i in range(1, 23)]

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✍️ Apuestas", "📊 Clasificación", "🏆 Mundial", "⚙️ Admin", "🔍 El Muro"])

    with tab1:
        st.header(f"✍️ Predicciones - {gp_sel}")
        if st.session_state.rol == 'admin':
            st.warning("Los administradores no apuestan.")
        else:
            user_gp_preds = df_p[(df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel)]
            def get_val(var):
                match = user_gp_preds[user_gp_preds['Variable'] == var]
                return match.iloc[0]['Valor'] if not match.empty else "- Seleccionar -"

            with st.form("form_gp_complejo"):
                # SECCIÓN QUALY
                st.subheader("⏱️ Clasificación (Top 5)")
                if q_bloq: st.caption("🔒 Bloqueado")
                c1, c2, c3, c4, c5 = st.columns(5)
                q_res = [
                    c1.selectbox("P1 Q", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("Q1")), disabled=q_bloq),
                    c2.selectbox("P2 Q", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("Q2")), disabled=q_bloq),
                    c3.selectbox("P3 Q", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("Q3")), disabled=q_bloq),
                    c4.selectbox("P4 Q", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("Q4")), disabled=q_bloq),
                    c5.selectbox("P5 Q", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("Q5")), disabled=q_bloq)
                ]

                # SECCIÓN SPRINT
                s_res = []
                if gp_sel in SPRINT_GPS:
                    st.divider()
                    st.subheader("🏎️ Carrera Sprint (Top 3)")
                    if s_bloq: st.caption("🔒 Bloqueado")
                    cs1, cs2, cs3 = st.columns(3)
                    s_res = [
                        cs1.selectbox("P1 Sprint", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("S1")), disabled=s_bloq),
                        cs2.selectbox("P2 Sprint", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("S2")), disabled=s_bloq),
                        cs3.selectbox("P3 Sprint", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val("S3")), disabled=s_bloq)
                    ]

                # SECCIÓN CARRERA
                st.divider()
                st.subheader("🏁 Carrera Principal y Extras")
                if c_bloq: st.caption("🔒 Bloqueado")
                cc1, cc2 = st.columns(2)
                with cc1:
                    c_res = [st.selectbox(f"P{i+1} Carrera", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val(f"C{i+1}")), key=f"cr{i}", disabled=c_bloq) for i in range(5)]
                with cc2:
                    alo = st.selectbox("Pos. Alonso", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Alonso")), disabled=c_bloq)
                    sai = st.selectbox("Pos. Sainz Jr.", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Sainz")), disabled=c_bloq)
                    saf = st.selectbox("¿Safety Car?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("Safety")), disabled=c_bloq)
                    red = st.selectbox("¿Bandera Roja?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("RedFlag")), disabled=c_bloq)

                boton_bloqueado = q_bloq and (s_bloq if gp_sel in SPRINT_GPS else True) and c_bloq
                if st.form_submit_button("💾 Guardar Cambios", disabled=boton_bloqueado):
                    todas = q_res + s_res + c_res + [alo, sai, saf, red]
                    if "- Seleccionar -" in todas:
                        st.error("⚠️ No puedes dejar campos vacíos en las secciones abiertas.")
                    else:
                        # Preparamos datos (mantenemos lo bloqueado y actualizamos lo abierto)
                        new_data = []
                        for i, v in enumerate(q_res): new_data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        for i, v in enumerate(s_res): new_data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"S{i+1}", "Valor": v})
                        for i, v in enumerate(c_res): new_data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        new_data.extend([
                            {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Alonso", "Valor": alo},
                            {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Sainz", "Valor": sai},
                            {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Safety", "Valor": saf},
                            {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "RedFlag", "Valor": red}
                        ])
                        df_p = pd.concat([df_p[~((df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel))], pd.DataFrame(new_data)])
                        conn.update(worksheet="Predicciones", data=df_p)
                        st.success("✅ ¡Actualizado!")

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
            # Creamos las 3 sub-pestañas para el Admin
            adm_gp, adm_final, adm_fechas = st.tabs(["🏁 Resultados GP", "🌎 Mundial Final", "📅 Fechas Límite"])
            
            with adm_gp:
                st.subheader(f"Publicar Resultados Reales: {gp_sel}")
                with st.form("admin_gp_results"):
                    ac1, ac2 = st.columns(2)
                    with ac1:
                        st.markdown("**Top 5 Clasificación**")
                        aq = [st.selectbox(f"Q{i+1} Real", PILOTOS_2026, key=f"rq{i}") for i in range(5)]
                        st.markdown("**Top 5 Carrera**")
                        ac = [st.selectbox(f"C{i+1} Real", PILOTOS_2026, key=f"rc{i}") for i in range(5)]
                    
                    with ac2:
                        st.markdown("**Eventos y Españoles**")
                        res_alo = st.selectbox("Alonso Real", POSICIONES_CARRERA, key="ra_admin")
                        res_sai = st.selectbox("Sainz Real", POSICIONES_CARRERA, key="rs_admin")
                        res_sf = st.selectbox("Safety Car Real", ["SI", "NO"], key="rsf_admin")
                        res_rf = st.selectbox("Red Flag Real", ["SI", "NO"], key="rrf_admin")
                        
                        as_res = []
                        if es_sprint:
                            st.markdown("---")
                            st.markdown("**Top 3 Sprint**")
                            as_res = [st.selectbox(f"S{i+1} Real", PILOTOS_2026, key=f"rsprint{i}") for i in range(3)]
                    
                    if st.form_submit_button("📢 Publicar Resultados del GP"):
                        r_data = []
                        # Guardar Qualy
                        for i, v in enumerate(aq): r_data.append({"GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        # Guardar Carrera
                        for i, v in enumerate(ac): r_data.append({"GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        # Guardar Sprint si aplica
                        for i, v in enumerate(as_res): r_data.append({"GP": gp_sel, "Variable": f"S{i+1}", "Valor": v})
                        # Guardar Extras
                        r_data.extend([
                            {"GP": gp_sel, "Variable": "Alonso", "Valor": res_alo},
                            {"GP": gp_sel, "Variable": "Sainz", "Valor": res_sai},
                            {"GP": gp_sel, "Variable": "Safety", "Valor": res_sf},
                            {"GP": gp_sel, "Variable": "RedFlag", "Valor": res_rf}
                        ])
                        
                        # Actualizar la hoja de Resultados
                        df_r = pd.concat([df_r[df_r['GP'] != gp_sel], pd.DataFrame(r_data)])
                        conn.update(worksheet="Resultados", data=df_r)
                        st.success(f"✅ Resultados de {gp_sel} publicados y puntos actualizados.")

            with adm_final:
                st.subheader("Subir Clasificación Final de la Temporada 2026")
                st.info("Esto se rellena una vez terminado el mundial en Abu Dabi.")
                with st.form("admin_mundial_final"):
                    am1, am2 = st.columns(2)
                    final_p = [am1.selectbox(f"P{i+1} Final Mundial", PILOTOS_2026, key=f"fp{i}") for i in range(22)]
                    final_e = [am2.selectbox(f"E{i+1} Final Mundial", EQUIPOS_2026, key=f"fe{i}") for i in range(11)]
                    
                    if st.form_submit_button("🏆 Publicar Resultados Finales"):
                        m_final = []
                        for i, v in enumerate(final_p): m_final.append({"Variable": f"P{i+1}", "Valor": v})
                        for i, v in enumerate(final_e): m_final.append({"Variable": f"E{i+1}", "Valor": v})
                        conn.update(worksheet="ResultadosMundial", data=pd.DataFrame(m_final))
                        st.success("🏆 ¡Resultados finales del Mundial guardados!")

            with adm_fechas:
                st.subheader("Configurar Cierres de Apuestas")
                st.write("Configura cuándo se bloquea cada sesión del fin de semana.")
                with st.form("f_cal_admin"):
                    f_gp = st.selectbox("GP a configurar", GPS)
                    c_q, c_s, c_c = st.columns(3)
                    
                    with c_q:
                        st.markdown("**Cierre Qualy**")
                        dq = st.date_input("Fecha Q", key="dq")
                        tq = st.time_input("Hora Q", key="tq")
                    with c_s:
                        st.markdown("**Cierre Sprint**")
                        ds = st.date_input("Fecha S", key="ds")
                        ts = st.time_input("Hora S", key="ts")
                    with c_c:
                        st.markdown("**Cierre Carrera**")
                        dc = st.date_input("Fecha C", key="dc")
                        tc = st.time_input("Hora C", key="tc")
                    
                    if st.form_submit_button("📅 Guardar Fechas Límite"):
                        cal_data = {
                            "GP": f_gp,
                            "LimiteQualy": datetime.combine(dq, tq).strftime('%Y-%m-%d %H:%M:%S'),
                            "LimiteSprint": datetime.combine(ds, ts).strftime('%Y-%m-%d %H:%M:%S'),
                            "LimiteCarrera": datetime.combine(dc, tc).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        df_cal = pd.concat([df_cal[df_cal['GP'] != f_gp], pd.DataFrame([cal_data])])
                        conn.update(worksheet="Calendario", data=df_cal)
                        st.success(f"✅ Fechas para {f_gp} actualizadas correctamente.")
        else:
            st.error("⛔ Acceso restringido a administradores.")

    with tab5: # MURO
        st.header("🔍 El Muro")
        df_muro = df_p[df_p['GP'] == gp_sel].copy()
        if not df_muro.empty:
            df_piv = df_muro.pivot(index='Usuario', columns='Variable', values='Valor')
            # Ordenamos columnas: Q1..5, S1..3, C1..5, Extras
            cols = [f'Q{i+1}' for i in range(5)] + [f'S{i+1}' for i in range(3)] + [f'C{i+1}' for i in range(5)] + ['Alonso', 'Sainz', 'Safety', 'RedFlag']
            st.dataframe(df_piv[[c for c in cols if c in df_piv.columns]], use_container_width=True)
