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
