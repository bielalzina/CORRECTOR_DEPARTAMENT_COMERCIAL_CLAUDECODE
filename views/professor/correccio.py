"""Vista de correcció automàtica per al professor."""

import streamlit as st
import pandas as pd

from modules.tasques_data import get_totes_tasques
from modules.alumnes_data import get_alumnes_per_grup
from modules.correccio import (
    executar_correccio, load_resultats, resoldre_ambigu, te_ambigus_pendents,
)
from modules.referencia_data import referencia_completa


GRAVETAT_COLOR = {
    "molt_greu": "🔴",
    "greu": "🟠",
    "lleu": "🟡",
}


def show():
    grup = st.session_state.grup
    _sidebar(grup)

    st.title(f"🔍 Correcció automàtica — {grup}")

    alumnes = get_alumnes_per_grup(grup)
    totes_tasques = get_totes_tasques(grup)

    if not totes_tasques:
        st.info("No hi ha cap tasca creada.")
        return

    # Selector de tasca
    opcions = [t["num_tasca"] for t in reversed(totes_tasques)]
    tasca_sel = st.selectbox("Selecciona la tasca:", opcions, key="correccio_tasca_sel")

    tasca_info = next((t for t in totes_tasques if t["num_tasca"] == tasca_sel), {})
    tasca_oberta = tasca_info.get("activa", False)

    # Comprovació de referència
    te_ref = referencia_completa(tasca_sel, grup, alumnes)
    if not te_ref:
        st.warning(
            "⚠️ Les dades de referència no estan carregades per a tots els alumnes. "
            "La correcció pot ser incompleta.",
            icon="⚠️",
        )

    if tasca_oberta:
        st.warning(
            "⚠️ La tasca encara és oberta. Pots executar la correcció, "
            "però els alumnes encara poden pujar o substituir llistats.",
            icon="⚠️",
        )

    # Botó d'execució
    col_btn, col_info = st.columns([2, 5])
    with col_btn:
        executar = st.button(
            "▶️ Executar correcció",
            type="primary",
            use_container_width=True,
            key="btn_executar_correccio",
        )

    if executar:
        with st.spinner("Executant la correcció..."):
            resultats = executar_correccio(tasca_sel, grup)
        st.success("Correcció executada correctament.")
        st.session_state[f"resultats_{tasca_sel}_{grup}"] = resultats
        st.rerun()

    # Carregar resultats existents
    resultats = st.session_state.get(f"resultats_{tasca_sel}_{grup}") or load_resultats(tasca_sel, grup)

    if not resultats:
        st.info("Encara no s'ha executat cap correcció per a aquesta tasca.")
        return

    st.caption(f"Darrera correcció: {resultats.get('data_correccio', '—')}")

    # Resum de notes
    _mostrar_resum(resultats, alumnes)

    st.divider()

    # Detall per alumne amb casos ambigus
    _mostrar_detall(resultats, tasca_sel, grup)


def _mostrar_resum(resultats: dict, alumnes: list[dict]) -> None:
    """Taula resum de notes de tots els alumnes."""
    st.subheader("Resum de notes")

    files = []
    alumnes_res = resultats.get("alumnes", {})

    for alumne in alumnes:
        exp = str(alumne["expedient"])
        res = alumnes_res.get(exp)
        if not res:
            files.append({
                "Alumne": alumne["nom"],
                "Nota": "—",
                "Penalització": "—",
                "Errors": "—",
                "Ambigus pendents": "—",
                "Llistats faltants": "—",
            })
            continue

        ambigus_pend = sum(
            1 for a in res.get("casos_ambigus", []) if a.get("resolucio") is None
        )
        files.append({
            "Alumne": res.get("nom", alumne["nom"]),
            "Nota": res.get("nota", 0),
            "Penalització": res.get("penalitzacio_total", 0),
            "Errors": len(res.get("errors", [])),
            "Ambigus pendents": ambigus_pend if ambigus_pend else "—",
            "Llistats faltants": ", ".join(res.get("llistats_faltants", [])) or "—",
        })

    if files:
        df = pd.DataFrame(files)
        st.dataframe(df, hide_index=True, use_container_width=True)

    if te_ambigus_pendents(resultats):
        st.warning("Hi ha casos ambigus pendents de resolució. Resoleu-los per recalcular les notes finals.")


def _mostrar_detall(resultats: dict, num_tasca: str, grup: str) -> None:
    """Detall d'errors i casos ambigus per alumne."""
    st.subheader("Detall per alumne")

    alumnes_res = resultats.get("alumnes", {})

    for exp, res in alumnes_res.items():
        errors = res.get("errors", [])
        ambigus = res.get("casos_ambigus", [])
        ambigus_pend = sum(1 for a in ambigus if a.get("resolucio") is None)
        nota = res.get("nota", 0)

        # Icona d'estat
        if ambigus_pend:
            icona = "❓"
        elif errors:
            icona = "❌"
        else:
            icona = "✅"

        titol = f"{icona} {res.get('nom', exp)}  —  Nota: **{nota}** / 10"
        with st.expander(titol, expanded=(ambigus_pend > 0)):
            # Llistats faltants
            faltants = res.get("llistats_faltants", [])
            if faltants:
                st.caption(f"Llistats no entregats: {', '.join(faltants)}")

            # Casos ambigus
            if ambigus:
                st.markdown("##### Casos ambigus")
                for a in ambigus:
                    _mostrar_ambigu(a, exp, num_tasca, grup)

            # Errors
            if errors:
                st.markdown("##### Errors detectats")
                _mostrar_taula_errors(errors)
            elif not ambigus:
                st.success("Cap error detectat.")


def _mostrar_ambigu(a: dict, expedient: str, num_tasca: str, grup: str) -> None:
    """Mostra un cas ambigu i els botons per resoldre'l."""
    resolucio = a.get("resolucio")
    aid = a["id"]

    if resolucio == "acceptat":
        estat = "✅ Acceptat"
        color = "green"
    elif resolucio == "rebutjat":
        estat = "❌ Rebutjat"
        color = "red"
    else:
        estat = "❓ Pendent"
        color = "orange"

    with st.container(border=True):
        col_desc, col_acc = st.columns([4, 2])
        with col_desc:
            st.markdown(f"**{a.get('llistat', '')}** — {a.get('descripcio', '')}")
            st.caption(
                f"Valor alumne: `{a.get('valor_alumne', '—')}` "
                f"| Esperat: `{a.get('valor_esperat', '—')}` "
                f"| Penalització si rebutjat: {a.get('penalitzacio_si_rebutjat', 0.5)}"
            )
            st.markdown(f"*Estat: :{color}[{estat}]*")

        with col_acc:
            if resolucio is None:
                st.write("")
                if st.button("✅ Acceptar", key=f"acc_{aid}", use_container_width=True):
                    _resoldre(num_tasca, grup, expedient, aid, "acceptat")
                if st.button("❌ Rebutjar", key=f"reb_{aid}", use_container_width=True):
                    _resoldre(num_tasca, grup, expedient, aid, "rebutjat")
            else:
                st.write("")
                if st.button("↩️ Desfer", key=f"desfer_{aid}", use_container_width=True):
                    _resoldre(num_tasca, grup, expedient, aid, None)


def _resoldre(num_tasca: str, grup: str, expedient: str, ambigu_id: str, resolucio) -> None:
    """Aplica la resolució d'un cas ambigu i refresca."""
    try:
        resultats = resoldre_ambigu(num_tasca, grup, expedient, ambigu_id, resolucio)
        st.session_state[f"resultats_{num_tasca}_{grup}"] = resultats
    except Exception as e:
        st.error(f"Error en resoldre el cas: {e}")
    st.rerun()


def _mostrar_taula_errors(errors: list[dict]) -> None:
    """Mostra una taula compacta dels errors."""
    files = []
    for e in errors:
        icona = GRAVETAT_COLOR.get(e.get("gravetat", ""), "⚪")
        files.append({
            "": icona,
            "Llistat": e.get("llistat", ""),
            "Tipus": e.get("tipus", ""),
            "Descripció": e.get("descripcio", ""),
            "Penalització": e.get("penalitzacio", 0),
            "Camp": e.get("camp", "") or "",
            "Valor alumne": str(e.get("valor_alumne", "") or ""),
            "Valor esperat": str(e.get("valor_esperat", "") or ""),
        })
    if files:
        df = pd.DataFrame(files)
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
        if st.button("📋 Dades de referència", use_container_width=True):
            st.session_state.page = "referencia"
            st.rerun()
        if st.button("🔍 Correcció", use_container_width=True):
            st.session_state.page = "correccio"
            st.rerun()
        if st.button("⚙️ Gestió de tasques", use_container_width=True):
            st.session_state.page = "tasques"
            st.rerun()
        st.divider()
        if st.button("Tancar sessió", use_container_width=True):
            for k in ["role", "user", "grup", "page", "tasca_sel"]:
                st.session_state[k] = None
            st.rerun()
