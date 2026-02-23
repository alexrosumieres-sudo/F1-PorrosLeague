import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN ---
PILOTOS = [
    "Verstappen", "Perez", "Hamilton", "Russell", "Leclerc", 
    "Sainz", "Norris", "Piastri", "Alonso", "Stroll",
    "Gasly", "Ocon", "Albon", "Colapinto", "Hulkenberg", 
    "Bearman", "Tsunoda", "Ricciardo", "Bottas", "Zhou"
]

GPS = ["GP Bahrein", "GP Arabia Saudí", "GP Australia", "GP Japón", "GP España"]

# --- LÓGICA DE PUNTUACIÓN ---
def calcular_puntos_f1(tipo, variable, valor_pred, valor_real):
    """
    tipo: 'TOP5', 'ESPAÑOL', 'CAOS'
    variable: 'Q1..Q5', 'C1..C5', 'Alonso', 'Safety', etc.
    """
    try:
        # 1. Lógica TOP 5 (Qualy y Carrera)
        if tipo == "TOP5":
            v_pred = str(valor_pred)
            # El valor_real para TOP5 debe ser una lista de los 5 primeros [P1, P2, P3, P4, P5]
            if v_pred == valor_real[int(variable[1])-1]: # Variable es 'Q1', 'C3', etc.
                return 2.0  # Posición Exacta
            
            pos_real = -1
            if v_pred in valor_real:
                pos_real = valor_real.index(v_pred) + 1
                pos_pred = int(variable[1])
                if abs(pos_pred - pos_real) == 1:
                    return 1.5  # Error +-1
                return 0.5  # Está en el top 5 pero lejos
            return 0.0

        # 2. Lógica Españoles (Alonso / Sainz)
        if tipo == "ESPAÑOL":
            p_pred = int(valor_pred)
            p_real = int(valor_real)
            if p_pred == p_real: return 1.0
            if abs(p_pred - p_real) == 1: return 0.5
            return 0.0

        # 3. Lógica Caos (Safety, Red Flag, DNF, DOTD)
        if tipo == "CAOS":
            if str(valor_pred).lower() == str(valor_real).lower():
                return 2.0
            return 0.0
            
    except:
        return 0.0
    return 0.0

# --- APP ---
st.title("🏎️ F1 Pro Predictor 2026")

tab1, tab2, tab3 = st.tabs(["✍️ Apuestas", "📊 Clasificación", "⚙️ Admin"])

with tab1:
    gp_sel = st.selectbox("Selecciona Gran Premio", GPS)
    
    st.header("⏱️ Clasificación (Sábado)")
    q_preds = []
    cols = st.columns(5)
    for i in range(5):
        p = cols[i].selectbox(f"P{i+1} Qualy", ["-"] + PILOTOS, key=f"q{i}")
        q_preds.append(p)

    st.header("🏁 Carrera (Domingo)")
    c_preds = []
    cols_c = st.columns(5)
    for i in range(5):
        p = cols_c[i].selectbox(f"P{i+1} Carrera", ["-"] + PILOTOS, key=f"c{i}")
        c_preds.append(p)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🇪🇸 Armada Española")
        pos_as = st.number_input("Posición Alonso", 1, 20, 14)
        pos_cs = st.number_input("Posición Sainz", 1, 20, 5)
    
    with col2:
        st.subheader("⚠️ Eventos")
        sc = st.checkbox("¿Safety Car?")
        rf = st.checkbox("¿Bandera Roja?")
        dnf = st.number_input("Número de DNFs", 0, 20, 2)
        dotd = st.selectbox("Piloto del Día", PILOTOS)

    if st.button("Guardar Predicción"):
        st.success(f"Predicciones para {gp_sel} enviadas correctamente.")

with tab2:
    st.info("Aquí se mostrará el ranking procesando los puntos con la función calcular_puntos_f1")

with tab3: # Pestaña Admin
    if st.session_state.rol == "admin":
        st.header("Actualizar Resultados Oficiales")
        gp_admin = st.selectbox("GP a actualizar", GPS, key="gp_admin")
        
        # Formulario para meter los resultados reales
        with st.form("form_admin"):
            col1, col2 = st.columns(2)
            with col1:
                res_q = [st.selectbox(f"Q{i+1} Real", PILOTOS, key=f"rq{i}") for i in range(5)]
                res_c = [st.selectbox(f"C{i+1} Real", PILOTOS, key=f"rc{i}") for i in range(5)]
            with col2:
                res_alonso = st.number_input("Alonso Real", 1, 20)
                res_sainz = st.number_input("Sainz Real", 1, 20)
                res_sc = st.radio("Safety Car", ["SI", "NO"])
                res_rf = st.radio("Bandera Roja", ["SI", "NO"])
                res_dnf = st.number_input("DNFs Real", 0, 20)
                res_dotd = st.selectbox("DOTD Real", PILOTOS)
            
            if st.form_submit_button("Publicar Resultados Oficiales"):
                # Aquí crearías un DataFrame con todos estos datos 
                # y usarías conn.update() para mandarlo a la pestaña 'Resultados'
                st.success("Resultados publicados. Los puntos se recalcularán.")
