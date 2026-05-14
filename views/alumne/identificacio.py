import streamlit as st
from modules.alumnes_data import get_alumnes_per_grup


def show():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Tornar"):
            st.session_state.role = None
            st.rerun()

        st.title("👩‍🎓 Identificació d'alumne")
        st.divider()

        grup = st.radio("Grup", ["ADG21", "ADG32"], horizontal=True)
        alumnes = get_alumnes_per_grup(grup)

        if not alumnes:
            st.warning("No hi ha alumnes configurats per a aquest grup.")
            return

        opcions = {f"{a['nom']}  ({a['expedient']})": a for a in alumnes}
        seleccionat = st.selectbox("El teu nom", list(opcions.keys()))
        alumne = opcions[seleccionat]

        st.info(f"Correu registrat: **{alumne['correu']}**")
        correu = st.text_input("Confirma el teu correu electrònic")

        if st.button("Accedir", type="primary", use_container_width=True):
            if correu.strip().lower() == alumne["correu"].lower():
                st.session_state.user = alumne
                st.session_state.grup = grup
                st.session_state.page = "portal"
                st.rerun()
            else:
                st.error("El correu no coincideix. Comprova que l'has escrit correctament.")
