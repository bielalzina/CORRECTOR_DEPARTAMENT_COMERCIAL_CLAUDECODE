import streamlit as st
from modules.tasques_data import load_tasca, is_fora_termini
from modules.validacio import validar_estructura, NOMS_LLISTATS
from modules.fitxers import guardar_llistat, get_llistats_alumne
from modules.utils import fmt_data

CODIS = ["01", "02", "03", "04", "05", "06", "07", "08"]
NOM_CURT = {
    "01_COMANDES_COMPRES": "Comandes compres",
    "02_RECEPCIONS": "Recepcions",
    "03_FACTURES_COMPRA": "Factures compra",
    "04_COMANDES_VENDES": "Comandes vendes",
    "05_ENTREGUES": "Entregues",
    "06_FACTURES_VENDA": "Factures venda",
    "07_STOCK": "Stock",
    "08_HISTORIAL_ENTRADES_SORTIDES": "Historial",
}


def show():
    alumne = st.session_state.user
    grup = st.session_state.grup
    num_tasca = st.session_state.tasca_sel

    if not num_tasca:
        st.session_state.page = "portal"
        st.rerun()
        return

    config = load_tasca(num_tasca, grup)
    if not config:
        st.error("No s'ha trobat la configuració d'aquesta tasca.")
        return

    fora_termini = is_fora_termini(config)

    with st.sidebar:
        st.markdown(f"**{alumne['nom']}**")
        st.caption(f"{alumne['rao_social']}")
        st.divider()
        if st.button("← Tornar al portal", width='stretch'):
            st.session_state.page = "portal"
            st.rerun()
        if st.button("Tancar sessió", width='stretch'):
            for k in ["role", "user", "grup", "page", "tasca_sel"]:
                st.session_state[k] = None
            st.rerun()

    st.title(f"📤 Lliurament — Tasca {num_tasca}")

    if fora_termini:
        st.warning(
            f"⚠️ **Estàs fora de termini.** El termini era el "
            f"**{fmt_data(config.get('data_tancament', '—'))}**. "
            "Els llistats s'acceptaran, però el professor decidirà si els corregeix."
        )
    else:
        st.success(f"✅ Termini obert fins al **{fmt_data(config.get('data_tancament', '—'))}**")

    llistats_actuals = get_llistats_alumne(num_tasca, grup, alumne["expedient"])

    # ── Zona de pujada ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Puja els fitxers xlsx exportats des d'ODOO")
    st.caption(
        "Pots pujar fins a 8 fitxers de cop. "
        "L'app detecta automàticament el tipus de cada fitxer."
    )

    fitxers_pujats = st.file_uploader(
        "xlsx",
        type=["xlsx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if fitxers_pujats:
        # Llegir tots els streams d'un cop (no es poden rellegir)
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

        # Botó únic per guardar tots els vàlids
        if valids:
            n_subs = sum(
                1 for _, _, r in valids
                if r.tipus and r.tipus.split("_")[0] in llistats_actuals
            )
            label = f"💾 Guardar {len(valids)} fitxer(s) vàlid(s)"
            if n_subs:
                label += f"  ({n_subs} substitució(ons))"
            st.write("")
            if st.button(label, type="primary", width='stretch'):
                for _, contingut, r in valids:
                    guardar_llistat(
                        contingut, num_tasca, grup,
                        alumne["expedient"], r.tipus, fora_termini,
                    )
                st.success(f"✅ {len(valids)} fitxer(s) guardats correctament.")
                st.rerun()

        if n_errors:
            st.info(
                f"ℹ️ {n_errors} fitxer(s) amb errors no s'han guardat. "
                "Corregeix-los a ODOO i torna a pujar-los."
            )

    # ── Estat actual ─────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Estat actual dels llistats")
    _mostrar_estat(get_llistats_alumne(num_tasca, grup, alumne["expedient"]))


def _mostrar_estat(llistats: dict):
    cols = st.columns(4)
    for i, tipus in enumerate(NOM_CURT):
        codi = tipus.split("_")[0]
        with cols[i % 4]:
            if codi in llistats:
                info = llistats[codi]
                fora = info.get("fora_termini", False)
                icon = "⚠️" if fora else "✅"
                data = fmt_data(info.get("data_pujada", ""))
                st.markdown(f"{icon} **{codi}** {NOM_CURT[tipus]}")
                st.caption(f"{data}" + (" *(fora termini)*" if fora else ""))
            else:
                st.markdown(f"⬜ **{codi}** {NOM_CURT[tipus]}")
                st.caption("Pendent")
