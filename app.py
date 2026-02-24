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
    tab1, tab2, tab3, tab4 = st.tabs(["✍️ Mis Apuestas", "📊 Clasificación", "🏆 Mundial", "⚙️ Admin"])

    with tab1:
        st.header(f"Tus predicciones - {gp_sel}")
        with st.form("apuestas"):
            c1, c2 = st.columns(2)
            q = [c1.selectbox(f"Q{i+1}", PILOTOS_2026, key=f"q{i}") for i in range(5)]
            c = [c2.selectbox(f"C{i+1}", PILOTOS_2026, key=f"c{i}") for i in range(5)]
            al = st.number_input("Pos. Alonso", 1, 22, 14)
            sa = st.number_input("Pos. Sainz Jr.", 1, 22, 5)
            sf = st.selectbox("Safety Car", ["SI", "NO"])
            rf = st.selectbox("Bandera Roja", ["SI", "NO"])
            if st.form_submit_button("Guardar"):
                data = []
                for i, v in enumerate(q): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                for i, v in enumerate(c): data.append({"Usuario": st.session_state.user, "GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                data.extend([{"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Alonso", "Valor": str(al)},
                             {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Sainz", "Valor": str(sa)},
                             {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "Safety", "Valor": sf},
                             {"Usuario": st.session_state.user, "GP": gp_sel, "Variable": "RedFlag", "Valor": rf}])
                df_p = pd.concat([df_p[~((df_p['Usuario']==st.session_state.user) & (df_p['GP']==gp_sel))], pd.DataFrame(data)])
                conn.update(worksheet="Predicciones", data=df_p)
                st.success("Guardado")

    with tab2:
        st.header("🏆 Ranking General")
        df_u_rank = leer_datos("Usuarios")
        ranking = []
        for user in df_u_rank['Usuario'].unique():
            pts = sum([calcular_puntos_gp(df_p[(df_p['Usuario']==user) & (df_p['GP']==g)], df_r[df_r['GP']==g]) for g in GPS])
            ranking.append({"Piloto": user, "Puntos": pts})
        st.table(pd.DataFrame(ranking).sort_values("Puntos", ascending=False))

    with tab3: # PESTAÑA MUNDIAL (DENTRO DEL ELSE)
        st.header("🏆 Predicciones de Temporada 2026")
        if MUNDIAL_BLOQUEADO: st.warning("Las apuestas de temporada están cerradas.")
        df_temp = leer_datos("Temporada")
        with st.form("form_temporada"):
            col_p, col_e = st.columns(2)
            with col_p:
                st.subheader("🔝 Top 22 Pilotos")
                pred_p = []
                for i in range(22):
                    val_prev = PILOTOS_2026[0]
                    if not df_temp.empty:
                        match = df_temp[(df_temp['Usuario'] == st.session_state.user) & (df_temp['Variable'] == f"P{i+1}")]
                        if not match.empty: val_prev = match.iloc[0]['Valor']
                    idx = PILOTOS_2026.index(val_prev) if val_prev in PILOTOS_2026 else 0
                    p = st.selectbox(f"P{i+1}", PILOTOS_2026, index=idx, key=f"temp_p{i}", disabled=MUNDIAL_BLOQUEADO)
                    pred_p.append(p)
            with col_e:
                st.subheader("🏭 Top 11 Constructores")
                pred_e = []
                for i in range(11):
                    val_prev = EQUIPOS_2026[0]
                    if not df_temp.empty:
                        match = df_temp[(df_temp['Usuario'] == st.session_state.user) & (df_temp['Variable'] == f"E{i+1}")]
                        if not match.empty: val_prev = match.iloc[0]['Valor']
                    idx = EQUIPOS_2026.index(val_prev) if val_prev in EQUIPOS_2026 else 0
                    e = st.selectbox(f"E{i+1}", EQUIPOS_2026, index=idx, key=f"temp_e{i}", disabled=MUNDIAL_BLOQUEADO)
                    pred_e.append(e)

            if st.form_submit_button("💾 Guardar Mundial", disabled=MUNDIAL_BLOQUEADO):
                if len(set(pred_p)) < 22 or len(set(pred_e)) < 11:
                    st.error("⚠️ No puedes repetir pilotos o escuderías.")
                else:
                    nuevas_temp = []
                    for i, v in enumerate(pred_p): nuevas_temp.append({"Usuario": st.session_state.user, "Variable": f"P{i+1}", "Valor": v})
                    for i, v in enumerate(pred_e): nuevas_temp.append({"Usuario": st.session_state.user, "Variable": f"E{i+1}", "Valor": v})
                    df_temp = pd.concat([df_temp[df_temp['Usuario'] != st.session_state.user], pd.DataFrame(nuevas_temp)])
                    conn.update(worksheet="Temporada", data=df_temp)
                    st.success("✅ Mundial guardado.")

    with tab4: # ADMIN
        if st.session_state.rol == 'admin':
            st.header("🔧 Panel de Administración")
            with st.form("admin"):
                st.subheader(f"Resultados Reales {gp_sel}")
                aq = [st.selectbox(f"Q{i+1} Real", PILOTOS_2026, key=f"rq{i}") for i in range(5)]
                ac = [st.selectbox(f"C{i+1} Real", PILOTOS_2026, key=f"rc{i}") for i in range(5)]
                aal = st.number_input("Alonso Real", 1, 22)
                asa = st.number_input("Sainz Real", 1, 22)
                asf = st.selectbox("SC Real", ["SI", "NO"])
                arf = st.selectbox("RF Real", ["SI", "NO"])
                if st.form_submit_button("Publicar Resultados"):
                    res = []
                    for i, v in enumerate(aq): res.append({"GP": gp_sel, "Variable": f"Q{i+1}", "Valor": v})
                    for i, v in enumerate(ac): res.append({"GP": gp_sel, "Variable": f"C{i+1}", "Valor": v})
                    res.extend([{"GP": gp_sel, "Variable": "Alonso", "Valor": str(aal)},
                                {"GP": gp_sel, "Variable": "Sainz", "Valor": str(asa)},
                                {"GP": gp_sel, "Variable": "Safety", "Valor": asf},
                                {"GP": gp_sel, "Variable": "RedFlag", "Valor": arf}])
                    df_r = pd.concat([df_r[df_r['GP'] != gp_sel], pd.DataFrame(res)])
                    conn.update(worksheet="Resultados", data=df_r)
                    st.success("Resultados actualizados")
        else:
            st.warning("No tienes permisos de administrador.")
