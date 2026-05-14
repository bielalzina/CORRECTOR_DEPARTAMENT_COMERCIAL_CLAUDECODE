import streamlit as st
import pandas as pd
from modules.tasques_data import get_tasques_obertes, get_totes_tasques
from modules.alumnes_data import get_alumnes_per_grup
from modules.fitxers import get_resum_entregues


def show():
    grup = st.session_state.grup
    _sidebar(grup)

    st.title(f"📊 Tauler de control — {grup}")

    alumnes = get_alumnes_per_grup(grup)
    tasques_obertes = get_tasques_obertes(grup)

    if not tasques_obertes:
        st.info(
            "No hi ha cap tasca activa. "
            "Crea'n una des de **⚙️ Gestió de tasques**."
        )
        return

    for t in tasques_obertes:
        num = t["num_tasca"]
        resum = get_resum_entregues(num, grup, alumnes)

        n_complets = sum(
            1 for r in resum
            if all(r[c] == "✅" for c in ["01", "02", "03", "04", "05", "06", "07", "08"])
        )
        n_fora = sum(1 for r in resum if "Sí" in r.get("fora_termini", ""))

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tasca", num)
            c2.metric("Termini", t.get("data_tancament", "—"))
            c3.metric("Entregues completes", f"{n_complets} / {len(alumnes)}")
            c4.metric("Fora de termini", n_fora)

            if resum:
                df = pd.DataFrame(resum)
                cols_show = ["nom", "01", "02", "03", "04", "05", "06", "07", "08", "total", "fora_termini"]
                df = df[cols_show].rename(columns={
                    "nom": "Alumne",
                    "total": "Total",
                    "fora_termini": "Fora termini",
                })
                st.dataframe(df, hide_index=True, use_container_width=True)


def _sidebar(grup: str):
    prof = st.session_state.user
    with st.sidebar:
        st.markdown(f"**{prof.get('nom', grup)}**")
        st.caption(f"Grup: {grup}")
        st.divider()
        if st.button("📊 Tauler", use_container_width=True):
            st.session_state.page = "tauler"
            st.rerun()
        if st.button("⚙️ Gestió de tasques", use_container_width=True):
            st.session_state.page = "tasques"
            st.rerun()
        st.divider()
        if st.button("Tancar sessió", use_container_width=True):
            for k in ["role", "user", "grup", "page", "tasca_sel"]:
                st.session_state[k] = None
            st.rerun()
