import streamlit as st
from modules.alumnes_data import verificar_alumne


def show():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Tornar"):
            st.session_state.role = None
            st.rerun()

        st.title("👩‍🎓 Accés d'alumne")
        st.divider()

        correu = st.text_input("Correu electrònic", placeholder="expedient.nom@cifpjoantaix.cat")
        password = st.text_input("Contrasenya", type="password")

        if st.button("Accedir", type="primary", width='stretch'):
            if not correu.strip() or not password:
                st.error("Introdueix el correu electrònic i la contrasenya.")
            else:
                alumne = verificar_alumne(correu.strip(), password)
                if alumne is None:
                    st.error("Correu o contrasenya incorrectes.")
                elif not alumne.get("actiu", True):
                    st.error("Aquest compte no està actiu. Contacta amb el teu professor.")
                else:
                    st.session_state.user = alumne
                    st.session_state.grup = alumne["grup"]
                    st.session_state.page = "portal"
                    st.rerun()
