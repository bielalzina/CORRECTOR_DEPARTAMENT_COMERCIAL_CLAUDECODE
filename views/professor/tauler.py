import streamlit as st
import pandas as pd
from modules.tasques_data import get_tasques_obertes
from modules.alumnes_data import get_alumnes_per_grup
from modules.fitxers import get_resum_entregues, get_llistats_alumne
from modules.referencia_data import referencia_completa
from modules.utils import fmt_data

CODIS = ["01", "02", "03", "04", "05", "06", "07", "08"]
NOM_LLISTAT = {
    "01": "Comandes compres", "02": "Recepcions", "03": "Factures compra",
    "04": "Comandes vendes", "05": "Entregues", "06": "Factures venda",
    "07": "Stock", "08": "Historial",
}


def show():
    grup = st.session_state.grup
    _sidebar(grup)

    st.title(f"📊 Tauler de control — {grup}")

    alumnes = get_alumnes_per_grup(grup)
    tasques_obertes = get_tasques_obertes(grup)

    if not tasques_obertes:
        st.info("No hi ha cap tasca activa. Crea'n una des de ⚙️ Gestió de tasques.")
        return

    for t in tasques_obertes:
        num = t["num_tasca"]
        resum = get_resum_entregues(num, grup, alumnes)
        te_referencia = referencia_completa(num, grup, alumnes)

        n_complets = sum(1 for r in resum if all(r[c] == "✅" for c in CODIS))
        n_fora = sum(1 for r in resum if "Sí" in r.get("fora_termini", ""))

        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Tasca", num)
            c2.metric("Termini", fmt_data(t.get("data_tancament", "—")))
            c3.metric("Entregues completes", f"{n_complets} / {len(alumnes)}")
            c4.metric("Fora de termini", n_fora)
            with c5:
                st.write("")
                if te_referencia:
                    st.success("✅ Ref. carregada")
                else:
                    if st.button("⚠️ Carregar ref.", key=f"ref_{num}", use_container_width=True):
                        st.session_state.page = "referencia"
                        st.rerun()

            tab1, tab2 = st.tabs(["Entregues", "Seguiment detallat"])

            with tab1:
                _tab_entregues(resum)

            with tab2:
                _tab_seguiment(num, grup, alumnes)


def _tab_entregues(resum: list[dict]) -> None:
    if not resum:
        st.info("Encara no hi ha entregues.")
        return
    df = pd.DataFrame(resum)
    cols_show = ["nom", "01", "02", "03", "04", "05", "06", "07", "08", "total", "fora_termini"]
    df = df[cols_show].rename(columns={
        "nom": "Alumne", "total": "Total", "fora_termini": "Fora termini",
    })
    st.dataframe(df, hide_index=True, use_container_width=True)


def _tab_seguiment(num_tasca: str, grup: str, alumnes: list[dict]) -> None:
    for alumne in alumnes:
        exp = str(alumne["expedient"])
        llistats = get_llistats_alumne(num_tasca, grup, exp)

        n = len(llistats)
        fora = any(v.get("fora_termini") for v in llistats.values())
        icona = "⚠️" if fora else ("✅" if n == 8 else "🔵" if n > 0 else "⬜")

        with st.expander(f"{icona} {alumne['nom']}  —  {n}/8 llistats"):
            if not llistats:
                st.caption("Cap llistat entregat.")
                continue
            cols = st.columns(4)
            for i, codi in enumerate(CODIS):
                with cols[i % 4]:
                    if codi in llistats:
                        info = llistats[codi]
                        fora_t = info.get("fora_termini", False)
                        icon = "⚠️" if fora_t else "✅"
                        data = fmt_data(info.get("data_pujada", ""))
                        st.markdown(f"{icon} **{codi}** {NOM_LLISTAT[codi]}")
                        st.caption(f"{data}" + (" *(fora termini)*" if fora_t else ""))
                    else:
                        st.markdown(f"⬜ **{codi}** {NOM_LLISTAT[codi]}")
                        st.caption("Pendent")


def _sidebar(grup: str):
    prof = st.session_state.user
    with st.sidebar:
        st.markdown(f"**{prof.get('nom', grup)}**")
        st.caption(f"Grup: {grup}")
        st.divider()
        if st.button("📊 Tauler", use_container_width=True):
            st.session_state.page = "tauler"
            st.rerun()
        if st.button("📋 Dades de referència", use_container_width=True):
            st.session_state.page = "referencia"
            st.rerun()
        if st.button("⚙️ Gestió de tasques", use_container_width=True):
            st.session_state.page = "tasques"
            st.rerun()
        st.divider()
        if st.button("Tancar sessió", use_container_width=True):
            for k in ["role", "user", "grup", "page", "tasca_sel"]:
                st.session_state[k] = None
            st.rerun()
