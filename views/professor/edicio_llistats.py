"""Vista del professor per visualitzar, editar i pujar llistats xlsx d'un alumne."""

import io
import streamlit as st
import pandas as pd
from pathlib import Path

from modules.fitxers import get_llistats_alumne, guardar_llistat, _entregues_dir
from modules.alumnes_data import get_alumnes_per_grup
from modules.validacio import validar_estructura, NOMS_LLISTATS
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

    tab_pujada, tab_llistats = st.tabs(["📤 Pujar llistats", "📂 Veure / Editar llistats"])

    with tab_pujada:
        _tab_pujada(num_tasca, grup, str(expedient), llistats)

    with tab_llistats:
        if not llistats:
            st.info("Aquest alumne encara no ha entregat cap llistat per aquesta tasca.")
        else:
            codis_entregats = sorted(llistats.keys())
            noms_subtabs = [f"{c} · {NOM_LLISTAT.get(c, c)}" for c in codis_entregats]
            subtabs = st.tabs(noms_subtabs)
            for subtab, codi in zip(subtabs, codis_entregats):
                with subtab:
                    _mostrar_llistat(num_tasca, grup, str(expedient), codi, llistats[codi])


def _tab_pujada(
    num_tasca: str, grup: str, expedient: str, llistats_actuals: dict
) -> None:
    st.markdown("Puja fitxers xlsx en nom d'aquest alumne. La validació és idèntica a la de l'alumne.")
    st.caption("El professor pot pujar llistats independentment del termini de la tasca.")

    fitxers_pujats = st.file_uploader(
        "xlsx",
        type=["xlsx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"uploader_prof_{expedient}_{num_tasca}",
    )

    if fitxers_pujats:
        dades = [(f.name, f.read()) for f in fitxers_pujats]
        resultats = [(nom, ct, validar_estructura(ct, nom)) for nom, ct in dades]

        st.divider()
        st.markdown("#### Resultat de la validació")

        valids: list[tuple] = []
        n_errors = 0

        for nom, contingut, r in resultats:
            codi = r.tipus.split("_")[0] if r.tipus else None
            nom_tipus = NOMS_LLISTATS.get(r.tipus, "") if r.tipus else ""
            ja_entregat = codi in llistats_actuals

            with st.container(border=True):
                if r.valid:
                    etiqueta = "⚠️ Substituirà l'entrega anterior" if ja_entregat else "✅ Vàlid"
                    st.markdown(f"**{etiqueta} — {nom}**")
                    st.caption(f"Identificat com: **{nom_tipus}**")
                    for avis in r.avisos:
                        st.warning(avis)
                    valids.append((nom, contingut, r))
                else:
                    n_errors += 1
                    st.markdown(f"**❌ {nom}**")
                    if r.tipus:
                        st.caption(f"Sembla: {nom_tipus}")
                    for error in r.errors:
                        st.error(error)
                    for avis in r.avisos:
                        st.warning(avis)

        if valids:
            n_subs = sum(
                1 for _, _, r in valids
                if r.tipus and r.tipus.split("_")[0] in llistats_actuals
            )
            label = f"💾 Guardar {len(valids)} fitxer(s) vàlid(s)"
            if n_subs:
                label += f"  ({n_subs} substitució(ons))"
            st.write("")
            if st.button(label, type="primary", width="stretch", key=f"btn_guardar_{expedient}"):
                for _, contingut, r in valids:
                    guardar_llistat(
                        contingut, num_tasca, grup,
                        expedient, r.tipus, fora_termini=False,
                    )
                st.success(f"✅ {len(valids)} fitxer(s) guardats correctament.")
                st.rerun()

        if n_errors:
            st.info(f"ℹ️ {n_errors} fitxer(s) amb errors no s'han guardat.")


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
        if st.button("← Tornar al seguiment", width="stretch"):
            st.session_state.torna_seguiment = True
            st.session_state.page = "tauler"
            st.rerun()
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
