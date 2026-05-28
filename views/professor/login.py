import streamlit as st
from modules.auth import professor_configurat, verificar_professor, configurar_password


def show():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Tornar"):
            st.session_state.role = None
            st.rerun()

        st.title("👨‍🏫 Accés professor")
        st.divider()

        grup = st.radio("Grup", ["ADG21", "ADG32"], horizontal=True)

        if not professor_configurat(grup):
            _mostrar_configuracio_inicial(grup)
        else:
            _mostrar_login(grup)


def _mostrar_login(grup: str):
    password = st.text_input("Contrasenya", type="password")
    if st.button("Entrar", type="primary", width='stretch'):
        prof = verificar_professor(grup, password)
        if prof:
            st.session_state.user = prof
            st.session_state.grup = grup
            st.session_state.page = "tauler"
            st.rerun()
        else:
            st.error("Contrasenya incorrecta.")


def _mostrar_configuracio_inicial(grup: str):
    st.info(
        "És la primera vegada que accediu. "
        "Establiu una contrasenya per al grup **" + grup + "**."
    )
    p1 = st.text_input("Nova contrasenya", type="password", key="p1")
    p2 = st.text_input("Confirma la contrasenya", type="password", key="p2")
    if st.button("Establir contrasenya i entrar", type="primary", width='stretch'):
        if not p1:
            st.error("La contrasenya no pot estar buida.")
        elif p1 != p2:
            st.error("Les contrasenyes no coincideixen.")
        elif len(p1) < 6:
            st.error("La contrasenya ha de tenir almenys 6 caràcters.")
        else:
            configurar_password(grup, p1)
            prof = verificar_professor(grup, p1)
            st.session_state.user = prof
            st.session_state.grup = grup
            st.session_state.page = "tauler"
            st.rerun()
