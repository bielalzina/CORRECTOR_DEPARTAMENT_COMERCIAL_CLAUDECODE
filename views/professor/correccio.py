"""Vista de correcció automàtica per al professor."""

import streamlit as st
import pandas as pd

from modules.tasques_data import get_totes_tasques
from modules.alumnes_data import get_alumnes_per_grup
from modules.correccio import (
    executar_correccio, load_resultats, resoldre_ambigu, te_ambigus_pendents,
)
from modules.referencia_data import referencia_completa
from modules.utils import fmt_data


GRAVETAT_ICONA = {
    "molt_greu": "🔴",
    "greu":      "🟠",
    "lleu":      "🟡",
}

# Llistats per bloc
LLISTATS_COMPRES  = {"01_COMANDES_COMPRES", "02_RECEPCIONS", "03_FACTURES_COMPRA", "COMPRES"}
LLISTATS_VENDES   = {"04_COMANDES_VENDES", "05_ENTREGUES", "06_FACTURES_VENDA", "VENDES"}
LLISTATS_MAGATZEM = {"07_STOCK", "08_HISTORIAL_ENTRADES_SORTIDES"}

NOM_LLISTAT = {
    "01_COMANDES_COMPRES":           "01 Comandes compres",
    "02_RECEPCIONS":                  "02 Recepcions",
    "03_FACTURES_COMPRA":             "03 Factures compra",
    "04_COMANDES_VENDES":             "04 Comandes vendes",
    "05_ENTREGUES":                   "05 Entregues",
    "06_FACTURES_VENDA":              "06 Factures venda",
    "07_STOCK":                       "07 Stock",
    "08_HISTORIAL_ENTRADES_SORTIDES": "08 Historial",
}


# ─────────────────────────────────────────────────────────────────────────────
# Vista principal
# ─────────────────────────────────────────────────────────────────────────────

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

    # Avisos
    if not referencia_completa(tasca_sel, grup, alumnes):
        st.warning(
            "⚠️ Les dades de referència no estan carregades per a tots els alumnes. "
            "La correcció pot ser incompleta."
        )
    if tasca_oberta:
        st.warning(
            "⚠️ La tasca encara és oberta. Els alumnes encara poden pujar o substituir llistats."
        )

    # Botó d'execució
    if st.button("▶️ Executar correcció", type="primary", key="btn_executar"):
        with st.spinner("Executant la correcció..."):
            resultats = executar_correccio(tasca_sel, grup)
        st.session_state[f"resultats_{tasca_sel}_{grup}"] = resultats
        st.success("Correcció executada correctament.")
        st.rerun()

    # Carregar resultats
    resultats = (
        st.session_state.get(f"resultats_{tasca_sel}_{grup}")
        or load_resultats(tasca_sel, grup)
    )

    if not resultats:
        st.info("Encara no s'ha executat cap correcció per a aquesta tasca.")
        return

    st.caption(f"Darrera correcció: {resultats.get('data_correccio', '—')}")

    if te_ambigus_pendents(resultats):
        st.warning("⚠️ Hi ha casos ambigus pendents de resolució. Resoleu-los per obtenir les notes finals.")

    st.divider()

    # ── Tres seccions ──────────────────────────────────────────────────────────
    tab_c, tab_v, tab_m = st.tabs([
        "🛒 Correcció de compres",
        "💼 Correcció de vendes",
        "📦 Correcció del magatzem",
    ])

    with tab_c:
        _seccio_bloc(resultats, alumnes, tasca_sel, grup, "compres")

    with tab_v:
        _seccio_bloc(resultats, alumnes, tasca_sel, grup, "vendes")

    with tab_m:
        _seccio_bloc(resultats, alumnes, tasca_sel, grup, "magatzem")


# ─────────────────────────────────────────────────────────────────────────────
# Secció d'un bloc (compres / vendes / magatzem)
# ─────────────────────────────────────────────────────────────────────────────

def _seccio_bloc(
    resultats: dict,
    alumnes: list[dict],
    num_tasca: str,
    grup: str,
    bloc: str,  # "compres" | "vendes" | "magatzem"
) -> None:
    llistats_bloc = {
        "compres":  LLISTATS_COMPRES,
        "vendes":   LLISTATS_VENDES,
        "magatzem": LLISTATS_MAGATZEM,
    }[bloc]

    alumnes_res = resultats.get("alumnes", {})

    # ── Taula resum del bloc ──────────────────────────────────────────────────
    st.subheader("Resum")
    files_resum = []
    for alumne in alumnes:
        exp = str(alumne["expedient"])
        res = alumnes_res.get(exp)
        if not res:
            files_resum.append({
                "Alumne": alumne["nom"],
                "Penalització": "—",
                "Errors": "—",
                "Casos ambigus": "—",
            })
            continue

        errors_bloc  = _errors_bloc(res, llistats_bloc)
        ambigus_bloc = _ambigus_bloc(res, llistats_bloc)
        pen = _penalitzacio_bloc(errors_bloc, ambigus_bloc)
        n_amb_pend = sum(1 for a in ambigus_bloc if a.get("resolucio") is None)

        files_resum.append({
            "Alumne":         res.get("nom", alumne["nom"]),
            "Penalització":   pen,
            "Errors":         len(errors_bloc),
            "Casos ambigus":  str(n_amb_pend) if n_amb_pend else "—",
        })

    st.dataframe(pd.DataFrame(files_resum), hide_index=True, use_container_width=True)

    st.divider()

    # ── Detall per alumne ──────────────────────────────────────────────────────
    st.subheader("Detall per alumne")

    for alumne in alumnes:
        exp = str(alumne["expedient"])
        res = alumnes_res.get(exp)
        if not res:
            continue

        errors_bloc  = _errors_bloc(res, llistats_bloc)
        ambigus_bloc = _ambigus_bloc(res, llistats_bloc)
        n_amb_pend   = sum(1 for a in ambigus_bloc if a.get("resolucio") is None)

        if n_amb_pend:
            icona = "❓"
        elif errors_bloc:
            icona = "❌"
        else:
            icona = "✅"

        pen = _penalitzacio_bloc(errors_bloc, ambigus_bloc)
        titol = f"{icona} {res.get('nom', exp)}  —  Penalització: **{pen}** pts"

        with st.expander(titol, expanded=(n_amb_pend > 0)):
            # Llistats faltants del bloc
            faltants = [
                c for c in res.get("llistats_faltants", [])
                if any(c in ll for ll in llistats_bloc)
            ]
            if faltants:
                st.caption(f"Llistats no entregats: {', '.join(faltants)}")

            # Casos ambigus del bloc
            if ambigus_bloc:
                st.markdown("##### Casos ambigus")
                for a in ambigus_bloc:
                    _mostrar_ambigu(a, exp, num_tasca, grup)

            # Errors del bloc
            if errors_bloc:
                st.markdown("##### Errors detectats")
                _taula_errors(errors_bloc)
            elif not ambigus_bloc:
                st.success("Cap error detectat en aquest bloc.")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de filtratge
# ─────────────────────────────────────────────────────────────────────────────

def _errors_bloc(res: dict, llistats_bloc: set) -> list[dict]:
    return [e for e in res.get("errors", []) if e.get("llistat", "") in llistats_bloc]


def _ambigus_bloc(res: dict, llistats_bloc: set) -> list[dict]:
    return [a for a in res.get("casos_ambigus", []) if a.get("llistat", "") in llistats_bloc]


def _penalitzacio_bloc(errors: list[dict], ambigus: list[dict]) -> float:
    """Suma de penalitzacions del bloc (errors + ambigus rebutjats)."""
    pen = sum(abs(e.get("penalitzacio", 0)) for e in errors)
    for a in ambigus:
        if a.get("resolucio") == "rebutjat":
            pen += abs(a.get("penalitzacio_si_rebutjat", 0.5))
    return round(pen, 2)


# ─────────────────────────────────────────────────────────────────────────────
# Taula d'errors
# ─────────────────────────────────────────────────────────────────────────────

def _taula_errors(errors: list[dict]) -> None:
    files = []
    for e in errors:
        files.append({
            "Gravetat":      GRAVETAT_ICONA.get(e.get("gravetat", ""), "⚪") + " " + e.get("gravetat", ""),
            "Llistat":       NOM_LLISTAT.get(e.get("llistat", ""), e.get("llistat", "")),
            "Descripció":    e.get("descripcio", ""),
            "Camp":          e.get("camp", "") or "",
            "Valor alumne":  fmt_data(str(e.get("valor_alumne", "") or "")),
            "Valor esperat": fmt_data(str(e.get("valor_esperat", "") or "")),
            "Penalització":  e.get("penalitzacio", 0),
        })
    if files:
        st.dataframe(pd.DataFrame(files), hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Casos ambigus
# ─────────────────────────────────────────────────────────────────────────────

def _mostrar_ambigu(a: dict, expedient: str, num_tasca: str, grup: str) -> None:
    resolucio = a.get("resolucio")
    aid = a["id"]

    if resolucio == "acceptat":
        estat_txt, estat_color = "✅ Acceptat", "green"
    elif resolucio == "rebutjat":
        estat_txt, estat_color = "❌ Rebutjat", "red"
    else:
        estat_txt, estat_color = "❓ Pendent", "orange"

    with st.container(border=True):
        col_desc, col_acc = st.columns([4, 2])
        with col_desc:
            st.markdown(
                f"**{NOM_LLISTAT.get(a.get('llistat',''), a.get('llistat',''))}** "
                f"— {a.get('descripcio', '')}"
            )
            st.caption(
                f"Valor alumne: `{fmt_data(str(a.get('valor_alumne', '') or '—'))}` "
                f"| Esperat: `{fmt_data(str(a.get('valor_esperat', '') or '—'))}` "
                f"| Penalització si rebutjat: **{a.get('penalitzacio_si_rebutjat', 0.5)} pts**"
            )
            st.markdown(f"Estat: :{estat_color}[{estat_txt}]")
        with col_acc:
            st.write("")
            if resolucio is None:
                if st.button("✅ Acceptar", key=f"acc_{aid}", use_container_width=True):
                    _resoldre(num_tasca, grup, expedient, aid, "acceptat")
                if st.button("❌ Rebutjar", key=f"reb_{aid}", use_container_width=True):
                    _resoldre(num_tasca, grup, expedient, aid, "rebutjat")
            else:
                if st.button("↩️ Desfer", key=f"desfer_{aid}", use_container_width=True):
                    _resoldre(num_tasca, grup, expedient, aid, None)


def _resoldre(num_tasca: str, grup: str, expedient: str, ambigu_id: str, resolucio) -> None:
    try:
        resultats = resoldre_ambigu(num_tasca, grup, expedient, ambigu_id, resolucio)
        st.session_state[f"resultats_{num_tasca}_{grup}"] = resultats
    except Exception as e:
        st.error(f"Error en resoldre el cas: {e}")
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

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
