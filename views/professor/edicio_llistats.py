"""Vista del professor per visualitzar i editar els llistats xlsx d'un alumne."""

import io
import streamlit as st
import pandas as pd
from pathlib import Path

from modules.fitxers import get_llistats_alumne, _entregues_dir
from modules.alumnes_data import get_alumnes_per_grup
from modules.utils import fmt_data

NOM_LLISTAT = {
    "01": "Comandes compres",
    "02": "Recepcions",
    "03": "Factures compra",
    "04": "Comandes vendes",
    "05": "Entregues",
    "06": "Factures venda",
    "07": "Stock",
    "08": "Historial",
}


def show():
    grup = st.session_state.grup
    num_tasca = st.session_state.get("tasca_edit")
    expedient = st.session_state.get("alumne_sel")

    _sidebar(grup)

    if not num_tasca or not expedient:
        st.error("No s'ha seleccionat cap alumne o tasca.")
        return

    alumnes = get_alumnes_per_grup(grup)
    alumne = next((a for a in alumnes if str(a["expedient"]) == str(expedient)), None)
    nom_alumne = alumne["nom"] if alumne else expedient

    st.title(f"📂 Llistats de {nom_alumne}")
    st.caption(f"Tasca {num_tasca} · Grup {grup} · Expedient {expedient}")

    llistats = get_llistats_alumne(num_tasca, grup, str(expedient))

    if not llistats:
        st.info("Aquest alumne encara no ha entregat cap llistat per aquesta tasca.")
        return

    codis_entregats = sorted(llistats.keys())
    noms_tabs = [f"{c} · {NOM_LLISTAT.get(c, c)}" for c in codis_entregats]
    tabs = st.tabs(noms_tabs)

    for tab, codi in zip(tabs, codis_entregats):
        with tab:
            _mostrar_llistat(num_tasca, grup, str(expedient), codi, llistats[codi])


def _mostrar_llistat(
    num_tasca: str, grup: str, expedient: str, codi: str, info: dict
) -> None:
    directori = _entregues_dir(num_tasca, grup, expedient)
    nom_fitxer = info.get("nom_fitxer", "")
    fitxer_path = directori / nom_fitxer

    fora_t = info.get("fora_termini", False)
    data_pujada = fmt_data(info.get("data_pujada", ""))
    st.caption(
        f"Fitxer: `{nom_fitxer}` · Pujat: {data_pujada}"
        + (" · ⚠️ Fora de termini" if fora_t else "")
    )

    if not fitxer_path.exists():
        st.error(f"No s'ha trobat el fitxer: {nom_fitxer}")
        return

    df = pd.read_excel(fitxer_path, dtype=str)
    df = df.fillna("")

    col_desc, col_btn = st.columns([6, 2])
    with col_desc:
        st.caption(f"{len(df)} files · {len(df.columns)} columnes")
    with col_btn:
        with open(fitxer_path, "rb") as f:
            st.download_button(
                "⬇️ Descarregar",
                data=f.read(),
                file_name=nom_fitxer,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{codi}",
            )

    edited_df = st.data_editor(
        df,
        key=f"editor_{codi}",
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
    )

    if st.button("💾 Guardar canvis", key=f"save_{codi}", type="primary"):
        _guardar_xlsx(edited_df, fitxer_path)
        st.success("Canvis guardats correctament.")
        st.rerun()


def _guardar_xlsx(df: pd.DataFrame, path: Path) -> None:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    path.write_bytes(buffer.getvalue())


def _sidebar(grup: str):
    prof = st.session_state.user
    with st.sidebar:
        st.markdown(f"**{prof.get('nom', grup)}**")
        st.caption(f"Grup: {grup}")
        st.divider()
        if st.button("📊 Tauler", width="stretch"):
            st.session_state.page = "tauler"
            st.rerun()
        if st.button("📋 Dades de referència", width="stretch"):
            st.session_state.page = "referencia"
            st.rerun()
        if st.button("🔍 Correcció", width="stretch"):
            st.session_state.page = "correccio"
            st.rerun()
        if st.button("⚙️ Gestió de tasques", width="stretch"):
            st.session_state.page = "tasques"
            st.rerun()
        st.divider()
        if st.button("Tancar sessió", width="stretch"):
            for k in ["role", "user", "grup", "page", "tasca_sel"]:
                st.session_state[k] = None
            st.rerun()
