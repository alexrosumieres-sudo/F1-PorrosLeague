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
# 2. FUNCIONES DE CÁLCULO DEFINITIVAS

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
        
        # --- LÓGICA QUALY (Q) Y CARRERA (C) ---
        if var.startswith('Q') or var.startswith('C'):
            lista_real = real_q if var.startswith('Q') else real_c
            try:
                pos_pred = int(var[1:])
                if val_p == val_r: 
                    puntos_esta_var = 2.0
                elif val_p in lista_real:
                    pos_real = lista_real.index(val_p) + 1
                    puntos_esta_var = 1.5 if abs(pos_pred - pos_real) == 1 else 0.5
            except: pass
            
            if var.startswith('Q'): desglose["Qualy"] += puntos_esta_var
            else: desglose["Carrera"] += puntos_esta_var

        # --- LÓGICA SPRINT (S) ---
        elif var.startswith('S'):
            if val_p == val_r:
                puntos_esta_var = 1.0
            desglose["Sprint"] += puntos_esta_var
            
        # --- LÓGICA ESPAÑOLES (Alonso/Sainz) ---
        elif var in ['Alonso', 'Sainz']:
            try:
                # Si es exacto (incluye DNF == DNF)
                if str(val_p) == str(val_r): 
                    puntos_esta_var = 2.0
                # Si falla por 1 (solo si ambos son números)
                elif val_p != "DNF" and val_r != "DNF":
                    if abs(int(val_p) - int(val_r)) == 1:
                        puntos_esta_var = 1.0
            except: pass
            desglose["Extras"] += puntos_esta_var

        # --- LÓGICA CAOS (Safety/RedFlag) ---
        elif var in ['Safety', 'RedFlag']:
            if str(val_p).lower() == str(val_r).lower(): 
                puntos_esta_var = 2.0
            desglose["Extras"] += puntos_esta_var
            
        pts += puntos_esta_var

    return desglose if detalle else pts

def calcular_puntos_mundial(u_preds_temp, mundial_results):
    pts = 0.0
    if u_preds_temp.empty or mundial_results.empty:
        return 0.0
    
    # Listas reales para calcular distancias
    real_p = mundial_results[mundial_results['Variable'].str.startswith('P')].sort_values('Variable')['Valor'].tolist()
    real_e = mundial_results[mundial_results['Variable'].str.startswith('E')].sort_values('Variable')['Valor'].tolist()
    
    for _, row in u_preds_temp.iterrows():
        var, val_p = row['Variable'], row['Valor']
        res_row = mundial_results[mundial_results['Variable'] == var]
        if res_row.empty: continue
        val_r = res_row.iloc[0]['Valor']
        
        try:
            pos_pred = int(var[1:])
            if val_p == val_r:
                pts += 5.0 # Exacto (Pilotos y Equipos)
            else:
                # Lógica de aproximación
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

    # Constante de GPs con formato Sprint
    SPRINT_GPS = ["02. GP de China", "06. GP de Miami", "07. GP de Canadá", "11. GP de Gran Bretaña", "14. GP de los Países Bajos", "18. GP de Singapur"]

    # Blindaje de datos y columnas
    if df_p.empty: df_p = pd.DataFrame(columns=['Usuario', 'GP', 'Variable', 'Valor'])
    if df_r.empty: df_r = pd.DataFrame(columns=['GP', 'Variable', 'Valor'])
    if df_temp.empty: df_temp = pd.DataFrame(columns=['Usuario', 'Variable', 'Valor'])
    if df_cal.empty: df_cal = pd.DataFrame(columns=['GP', 'LimiteQualy', 'LimiteSprint', 'LimiteCarrera'])
    
    df_p.columns = df_p.columns.str.strip()
    df_r.columns = df_r.columns.str.strip()
    df_temp.columns = df_temp.columns.str.strip()
    df_cal.columns = df_cal.columns.str.strip()

    # --- LÓGICA DE SELECCIÓN Y BLOQUEO ---
    st.sidebar.title(f"Piloto: {st.session_state.user}")
    gp_sel = st.sidebar.selectbox("Gran Premio", GPS)
    
    # Definimos es_sprint aquí arriba para que esté disponible en TODA la app (Evita NameError)
    es_sprint = gp_sel in SPRINT_GPS
    
    cal_row = df_cal[df_cal['GP'] == gp_sel]
    now = datetime.now()

    # Inicializamos bloqueos
    q_bloq, s_bloq, c_bloq = False, False, False
    
    if not cal_row.empty:
        q_lim = pd.to_datetime(cal_row.iloc[0]['LimiteQualy'])
        c_lim = pd.to_datetime(cal_row.iloc[0]['LimiteCarrera'])
        q_bloq = now > q_lim
        c_bloq = now > c_lim
        
        st.sidebar.markdown(f"**⏱️ Qualy:** {'🔴 Cerrada' if q_bloq else f'🟢 hasta {q_lim.strftime('%H:%M (%d/%m)')}'}")
        
        if es_sprint:
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

    # Definición de las 5 pestañas principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✍️ Mis Apuestas", "📊 Clasificación", "🏆 Mundial", "⚙️ Admin", "🔍 El Muro"])

    with tab1:
        st.header(f"✍️ Predicciones - {gp_sel}")
        if st.session_state.rol == 'admin':
            st.warning("⚠️ Los administradores no participan en las apuestas.")
        else:
            user_gp_preds = df_p[(df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel)]
            def get_val(var):
                match = user_gp_preds[user_gp_preds['Variable'] == var]
                return match.iloc[0]['Valor'] if not match.empty else "- Seleccionar -"

            with st.form("form_gp_global"):
                # QUALY
                st.subheader("⏱️ Clasificación (Top 5)")
                if q_bloq: st.caption("🔒 Sección bloqueada")
                cq = st.columns(5)
                q_res = [cq[i].selectbox(f"P{i+1} Q", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val(f"Q{i+1}")), key=f"q_u_{i}", disabled=q_bloq) for i in range(5)]

                # SPRINT
                s_res = []
                if es_sprint:
                    st.divider()
                    st.subheader("🏎️ Carrera Sprint (Top 3)")
                    if s_bloq: st.caption("🔒 Sección bloqueada")
                    cs = st.columns(3)
                    s_res = [cs[i].selectbox(f"P{i+1} S", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val(f"S{i+1}")), key=f"s_u_{i}", disabled=s_bloq) for i in range(3)]

                # CARRERA
                st.divider()
                st.subheader("🏁 Carrera y Extras")
                if c_bloq: st.caption("🔒 Sección bloqueada")
                cc1, cc2 = st.columns(2)
                with cc1:
                    c_res = [st.selectbox(f"P{i+1} Carrera", OPCIONES_PILOTOS, index=OPCIONES_PILOTOS.index(get_val(f"C{i+1}")), key=f"c_u_{i}", disabled=c_bloq) for i in range(5)]
                with cc2:
                    alo = st.selectbox("Pos. Alonso", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Alonso")), disabled=c_bloq)
                    sai = st.selectbox("Pos. Sainz Jr.", POSICIONES_CARRERA, index=POSICIONES_CARRERA.index(get_val("Sainz")), disabled=c_bloq)
                    saf = st.selectbox("¿Safety Car?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("Safety")), disabled=c_bloq)
                    red = st.selectbox("¿Bandera Roja?", OPCIONES_BINARIAS, index=OPCIONES_BINARIAS.index(get_val("RedFlag")), disabled=c_bloq)

                enviar_bloqueado = q_bloq and (s_bloq if es_sprint else True) and c_bloq
                if st.form_submit_button("💾 Guardar Todo", disabled=enviar_bloqueado):
                    # Solo validamos lo que está abierto
                    campos_a_validar = []
                    if not q_bloq: campos_a_validar += q_res
                    if es_sprint and not s_bloq: campos_a_validar += s_res
                    if not c_bloq: campos_a_validar += c_res + [alo, sai, saf, red]
                    
                    if "- Seleccionar -" in campos_a_validar:
                        st.error("⚠️ Por favor, rellena todos los campos de las secciones abiertas.")
                    else:
                        data = []
                        # IMPORTANTE: Guardamos siempre todo (lo nuevo y lo que ya estaba bloqueado)
                        for i, v in enumerate(q_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                        for i, v in enumerate(s_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"S{i+1}", "Valor": v})
                        for i, v in enumerate(c_res): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                        data.extend([{"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Alonso", "Valor": alo},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Sainz", "Valor": sai},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Safety", "Valor": saf},
                                     {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "RedFlag", "Valor": red}])
                        
                        df_p = pd.concat([df_p[~((df_p['Usuario'] == st.session_state.user) & (df_p['GP'] == gp_sel))], pd.DataFrame(data)])
                        conn.update(worksheet="Predicciones", data=df_p)
                        st.success("✅ Predicciones actualizadas.")

    with tab2:
        st.header("📊 Clasificación General")
        df_u_rank = leer_datos("Usuarios")
        if not df_u_rank.empty:
            participantes = df_u_rank[df_u_rank['Rol'] == 'user']['Usuario'].unique()
            ranking_list = []
            
            for u in participantes:
                # 1. Suma de todos los GPs
                p_gps = sum([calcular_puntos_gp(df_p[(df_p['Usuario']==u) & (df_p['GP']==g)], df_r[df_r['GP']==g]) for g in GPS])
                
                # 2. Suma del Mundial Final
                p_mundial = calcular_puntos_mundial(df_temp[df_temp['Usuario']==u], df_r_mundial)
                
                ranking_list.append({
                    "Piloto": u, 
                    "Puntos GPs": p_gps, 
                    "Bonus Mundial": p_mundial, 
                    "TOTAL": p_gps + p_mundial
                })
            
            df_f = pd.DataFrame(ranking_list).sort_values("TOTAL", ascending=False)
            df_f.insert(0, "Pos", range(1, len(df_f) + 1))
            st.dataframe(df_f, use_container_width=True, hide_index=True)

    with tab3:
        st.header("🏆 Mundial de Temporada")
        st.warning("🔒 El periodo de predicciones para el Mundial ha finalizado.")
        df_u_temp = df_temp[df_temp['Usuario'] == st.session_state.user]
        if not df_u_temp.empty:
            st.write("Tus predicciones guardadas:")
            st.dataframe(df_u_temp[['Variable', 'Valor']], use_container_width=True, hide_index=True)
        else:
            st.info("No realizaste predicciones para el Mundial.")

    with tab4:
        if st.session_state.rol == 'admin':
            # Sub-pestañas del Admin
            adm_gp, adm_final, adm_fechas = st.tabs(["🏁 Resultados GP", "🌎 Mundial Final", "📅 Fechas Límite"])
            
            with adm_gp:
                st.subheader(f"Publicar Resultados Reales: {gp_sel}")
                with st.form("admin_gp_results"):
                    ac1, ac2 = st.columns(2)
                    with ac1:
                        st.markdown("**Top 5 Q y C**")
                        # Usamos OPCIONES_PILOTOS e index=0 para que aparezca "- Seleccionar -"
                        aq = [st.selectbox(f"Q{i+1} Real", OPCIONES_PILOTOS, index=0, key=f"arq{i}") for i in range(5)]
                        ac = [st.selectbox(f"C{i+1} Real", PILOTOS_2026, index=0, key=f"arc{i}") for i in range(5)]
                    with ac2:
                        st.markdown("**Extras**")
                        # Usamos las listas con valor neutro e index=0
                        res_alo = st.selectbox("Alonso Real", POSICIONES_CARRERA, index=0, key="ara_adm")
                        res_sai = st.selectbox("Sainz Real", POSICIONES_CARRERA, index=0, key="ars_adm")
                        res_sf = st.selectbox("Safety Real", OPCIONES_BINARIAS, index=0, key="arsf_adm")
                        res_rf = st.selectbox("Red Flag Real", OPCIONES_BINARIAS, index=0, key="arrf_adm")
                        
                        as_res = []
                        if es_sprint:
                            st.markdown("---")
                            st.markdown("**Top 3 Sprint**")
                            as_res = [st.selectbox(f"S{i+1} Real", OPCIONES_PILOTOS, index=0, key=f"arsprint{i}") for i in range(3)]
                    
                    if st.form_submit_button("📢 Publicar Resultados"):
                        # VALIDACIÓN: Comprobar si hay algún "- Seleccionar -"
                        check_list = aq + ac + as_res + [res_alo, res_sai, res_sf, res_rf]
                        if "- Seleccionar -" in check_list:
                            st.error("⚠️ Error: El Admin debe seleccionar todos los resultados reales antes de publicar.")
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
                            st.success(f"✅ Resultados de {gp_sel} publicados con éxito.")

            with adm_final:
                st.subheader("Resultados Finales del Campeonato")
                st.info("Solo rellenar al final de la temporada.")
                with st.form("admin_mundial_final"):
                    am1, am2 = st.columns(2)
                    # Usamos listas OPCIONES con index=0
                    f_p = [am1.selectbox(f"P{i+1} Mundial", OPCIONES_PILOTOS, index=0, key=f"fp{i}") for i in range(22)]
                    f_e = [am2.selectbox(f"E{i+1} Mundial", OPCIONES_EQUIPOS, index=0, key=f"fe{i}") for i in range(11)]
                    
                    if st.form_submit_button("🏆 Publicar Mundial Final"):
                        if "- Seleccionar -" in f_p or "- Seleccionar -" in f_e:
                            st.error("⚠️ Debes completar toda la parrilla final.")
                        else:
                            m_f = []
                            for i, v in enumerate(f_p): m_f.append({"Variable": f"P{i+1}", "Valor": v})
                            for i, v in enumerate(f_e): m_f.append({"Variable": f"E{i+1}", "Valor": v})
                            conn.update(worksheet="ResultadosMundial", data=pd.DataFrame(m_f))
                            st.success("🏆 Resultados finales guardados correctamente.")

            with adm_fechas:
                st.subheader("Configurar Cierres")
                with st.form("f_cal_admin"):
                    f_gp = st.selectbox("GP", GPS, key="f_gp_cal")
                    c_q, c_s, c_c = st.columns(3)
                    dq, tq = c_q.date_input("Fecha Q"), c_q.time_input("Hora Q")
                    ds, ts = c_s.date_input("Fecha S"), c_s.time_input("Hora S")
                    dc, tc = c_c.date_input("Fecha C"), c_c.time_input("Hora C")
                    
                    if st.form_submit_button("📅 Guardar Fechas"):
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
            st.error("⛔ No tienes permisos de administrador.")

    with tab5: # MURO
        st.header("🔍 El Muro de la Verdad")
        df_muro = df_p[df_p['GP'] == gp_sel].copy()
        if not df_muro.empty:
            df_piv = df_muro.pivot(index='Usuario', columns='Variable', values='Valor')
            cols = [f'Q{i+1}' for i in range(5)] + ([f'S{i+1}' for i in range(3)] if es_sprint else []) + [f'C{i+1}' for i in range(5)] + ['Alonso', 'Sainz', 'Safety', 'RedFlag']
            st.dataframe(df_piv[[c for c in cols if c in df_piv.columns]], use_container_width=True)
        else: st.info("Nadie ha apostado aún.")
