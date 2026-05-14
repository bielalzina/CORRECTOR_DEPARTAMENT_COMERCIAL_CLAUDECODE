import streamlit as st
from modules.tasques_data import get_tasques_obertes, is_fora_termini
from modules.fitxers import get_llistats_alumne

CODIS = ["01", "02", "03", "04", "05", "06", "07", "08"]
NOM_CURT = {
    "01": "Com.C", "02": "Recep", "03": "Fac.C",
    "04": "Com.V", "05": "Entr", "06": "Fac.V",
    "07": "Stock", "08": "Hist",
}


def show():
    alumne = st.session_state.user
    grup = st.session_state.grup

    with st.sidebar:
        st.markdown(f"**{alumne['nom']}**")
        st.caption(f"{alumne['rao_social']}")
        st.divider()
        if st.button("Tancar sessió", use_container_width=True):
            _logout()

    st.title("📋 Portal d'entregues")
    tasques = get_tasques_obertes(grup)

    if not tasques:
        st.info("No hi ha cap tasca oberta en aquest moment. Consulta amb el teu professor.")
        return

    for t in tasques:
        num = t["num_tasca"]
        fora = is_fora_termini(t)
        llistats = get_llistats_alumne(num, grup, alumne["expedient"])
        n = len(llistats)

        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"### Tasca {num}")
                icona = "🔴" if fora else "🟢"
                st.caption(f"{icona} Termini: {t.get('data_tancament', '—')}")
            with c2:
                st.metric("Llistats entregats", f"{n} / 8")
            with c3:
                st.write("")
                st.write("")
                if st.button("Gestionar entrega", key=f"btn_{num}",
                             use_container_width=True, type="primary"):
                    st.session_state.tasca_sel = num
                    st.session_state.page = "lliurament"
                    st.rerun()

            # Mini-graella d'estat per codi
            cols = st.columns(8)
            for i, codi in enumerate(CODIS):
                with cols[i]:
                    if codi in llistats:
                        fora_t = llistats[codi].get("fora_termini", False)
                        icon = "⚠️" if fora_t else "✅"
                    else:
                        icon = "⬜"
                    st.markdown(
                        f"<div style='text-align:center;font-size:1.2em'>{icon}</div>"
                        f"<div style='text-align:center;font-size:0.7em'>{NOM_CURT[codi]}</div>",
                        unsafe_allow_html=True,
                    )


def _logout():
    for k in ["role", "user", "grup", "page", "tasca_sel"]:
        st.session_state[k] = None
    st.rerun()
