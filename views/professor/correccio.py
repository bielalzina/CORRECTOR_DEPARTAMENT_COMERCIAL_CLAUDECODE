"""Vista de correcció automàtica per al professor."""

import io
import streamlit as st
import pandas as pd

from modules.tasques_data import get_totes_tasques
from modules.alumnes_data import get_alumnes_per_grup
from modules.correccio import (
    executar_correccio, load_resultats, resoldre_ambigu, te_ambigus_pendents,
)
from modules.referencia_data import referencia_completa
from modules.utils import fmt_data, alias_camp


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

    # ── Quatre pestanyes ───────────────────────────────────────────────────────
    tab_c, tab_v, tab_m, tab_g = st.tabs([
        "🛒 Correcció de compres",
        "💼 Correcció de vendes",
        "📦 Correcció del magatzem",
        "📋 Errors globals",
    ])

    with tab_c:
        _seccio_bloc(resultats, alumnes, tasca_sel, grup, "compres")

    with tab_v:
        _seccio_bloc(resultats, alumnes, tasca_sel, grup, "vendes")

    with tab_m:
        _seccio_bloc(resultats, alumnes, tasca_sel, grup, "magatzem")

    with tab_g:
        _seccio_errors_globals(resultats, alumnes)


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
            fila: dict = {"Alumne": alumne["nom"]}
            if bloc == "compres":
                fila["Comandes compra"] = "—"
                fila["Recepcions"] = "—"
                fila["Factures compra"] = "—"
            elif bloc == "vendes":
                fila["Comandes venda"] = "—"
                fila["Entregues"] = "—"
                fila["Factures venda"] = "—"
            fila["Penalització"] = "—"
            fila["Errors"] = "—"
            fila["Casos ambigus"] = "—"
            files_resum.append(fila)
            continue

        errors_bloc  = _errors_bloc(res, llistats_bloc)
        ambigus_bloc = _ambigus_bloc(res, llistats_bloc)
        pen = _penalitzacio_bloc(errors_bloc, ambigus_bloc)
        n_amb_pend = sum(1 for a in ambigus_bloc if a.get("resolucio") is None)
        counts = res.get("counts", {})

        fila = {"Alumne": res.get("nom", alumne["nom"])}
        if bloc == "compres":
            rc = counts.get("ref_compres")
            fila["Comandes compra"] = _fmt_count(counts.get("n01"), rc)
            fila["Recepcions"]      = _fmt_count(counts.get("n02"), rc)
            fila["Factures compra"] = _fmt_count(counts.get("n03"), rc)
        elif bloc == "vendes":
            rv = counts.get("ref_vendes")
            fila["Comandes venda"] = _fmt_count(counts.get("n04"), rv)
            fila["Entregues"]      = _fmt_count(counts.get("n05"), rv)
            fila["Factures venda"] = _fmt_count(counts.get("n06"), None)
        fila["Penalització"]  = pen
        fila["Errors"]        = len(errors_bloc)
        fila["Casos ambigus"] = str(n_amb_pend) if n_amb_pend else "—"
        files_resum.append(fila)

    df_resum = pd.DataFrame(files_resum)
    cols_count = {
        "compres": ["Comandes compra", "Recepcions", "Factures compra"],
        "vendes":  ["Comandes venda", "Entregues", "Factures venda"],
    }.get(bloc, [])
    st.html(_taula_resum_html(df_resum, cols_count))

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

def _taula_resum_html(df: pd.DataFrame, cols_count: list[str]) -> str:
    """Genera una taula HTML amb centrat de columnes i color per discrepàncies."""
    COLOR_DISC   = "#ffe0b2"
    COLOR_DISC_T = "#6d3b00"

    def _es_discrepancia(val: str, col: str) -> bool:
        if col not in cols_count or not isinstance(val, str) or "/" not in val:
            return False
        parts = val.split("/")
        try:
            return int(parts[0]) != int(parts[1])
        except ValueError:
            return False

    def _fmt_val(val, col: str) -> str:
        if col == "Penalització" and isinstance(val, (int, float)):
            return f"{val:.2f}"
        return str(val) if val is not None else "—"

    css = """
    <style>
    .resum-taula { width:100%; border-collapse:collapse; font-size:14px; }
    .resum-taula th {
        background:#f0f2f6; color:#31333f;
        padding:8px 10px; border-bottom:2px solid #d0d0d0;
        text-align:center; font-weight:600;
    }
    .resum-taula th:first-child { text-align:left; }
    .resum-taula td {
        padding:6px 10px; border-bottom:1px solid #e8e8e8;
        text-align:center; vertical-align:middle;
    }
    .resum-taula td:first-child { text-align:left; }
    .resum-taula tr:hover td { background:#f7f7f7; }
    .disc { background-color:""" + COLOR_DISC + """; color:""" + COLOR_DISC_T + """; font-weight:600; border-radius:4px; }
    </style>
    """

    cols = list(df.columns)
    header = "".join(f"<th>{c}</th>" for c in cols)
    rows = []
    for _, row in df.iterrows():
        cells = []
        for col in cols:
            val = row[col]
            txt = _fmt_val(val, col)
            disc = _es_discrepancia(txt, col)
            cls = ' class="disc"' if disc else ""
            cells.append(f"<td{cls}>{txt}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")

    return css + f'<table class="resum-taula"><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def _fmt_count(registrades, esperades) -> str:
    if registrades is None:
        return "—"
    if esperades is None:
        return str(registrades)
    return f"{registrades}/{esperades}"


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
            "Document":      e.get("document", "") or "",
            "Descripció":    e.get("descripcio", ""),
            "Camp":          alias_camp(e.get("camp", "") or "", e.get("llistat", "")),
            "Valor alumne":  fmt_data(str(e.get("valor_alumne", "") or "")),
            "Valor esperat": fmt_data(str(e.get("valor_esperat", "") or "")),
            "Penalització":  e.get("penalitzacio", 0),
        })
    if files:
        st.dataframe(pd.DataFrame(files), hide_index=True, width='stretch')


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
                if st.button("✅ Acceptar", key=f"acc_{aid}", width='stretch'):
                    _resoldre(num_tasca, grup, expedient, aid, "acceptat")
                if st.button("❌ Rebutjar", key=f"reb_{aid}", width='stretch'):
                    _resoldre(num_tasca, grup, expedient, aid, "rebutjat")
            else:
                if st.button("↩️ Desfer", key=f"desfer_{aid}", width='stretch'):
                    _resoldre(num_tasca, grup, expedient, aid, None)


def _resoldre(num_tasca: str, grup: str, expedient: str, ambigu_id: str, resolucio) -> None:
    try:
        resultats = resoldre_ambigu(num_tasca, grup, expedient, ambigu_id, resolucio)
        st.session_state[f"resultats_{num_tasca}_{grup}"] = resultats
    except Exception as e:
        st.error(f"Error en resoldre el cas: {e}")
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Vista global d'errors (totes les empreses)
# ─────────────────────────────────────────────────────────────────────────────

def _seccio_errors_globals(resultats: dict, alumnes: list[dict]) -> None:
    """Taula unificada amb tots els errors de totes les empreses."""

    # Mapa expedient → alumne per a la columna Empresa
    info_alumne = {str(a["expedient"]): a for a in alumnes}

    alumnes_res = resultats.get("alumnes", {})
    files = []

    for exp, res in alumnes_res.items():
        alumne = info_alumne.get(exp, {})
        empresa = alumne.get("rao_social", exp)

        for e in res.get("errors", []):
            llistat_codi = e.get("llistat", "")
            if llistat_codi in LLISTATS_COMPRES:
                apartat = "COMPRES"
            elif llistat_codi in LLISTATS_VENDES:
                apartat = "VENDES"
            else:
                apartat = "MAGATZEM"
            files.append({
                "Empresa":       empresa,
                "Apartat":       apartat,
                "Gravetat":      GRAVETAT_ICONA.get(e.get("gravetat", ""), "⚪") + " " + e.get("gravetat", ""),
                "Llistat":       NOM_LLISTAT.get(llistat_codi, llistat_codi),
                "Document":      e.get("document", "") or "",
                "Descripció":    e.get("descripcio", ""),
                "Camp":          alias_camp(e.get("camp", "") or "", llistat_codi),
                "Valor alumne":  fmt_data(str(e.get("valor_alumne", "") or "")),
                "Valor esperat": fmt_data(str(e.get("valor_esperat", "") or "")),
                "Penalització":  e.get("penalitzacio", 0),
            })

    if not files:
        st.success("Cap error detectat.")
        return

    df = pd.DataFrame(files)

    # Resum ràpid
    c1, c2, c3 = st.columns(3)
    c1.metric("Total errors", len(df))
    c2.metric("Empreses afectades", df["Empresa"].nunique())
    pen_total = df["Penalització"].abs().sum()
    c3.metric("Penalització total acumulada", f"{round(pen_total, 2)} pts")

    st.divider()

    # Filtre per empresa
    empreses = ["— Totes —"] + sorted(df["Empresa"].unique().tolist())
    empresa_sel = st.selectbox("Filtrar per empresa:", empreses, key="global_empresa_sel")
    if empresa_sel != "— Totes —":
        df = df[df["Empresa"] == empresa_sel]

    st.dataframe(df, hide_index=True, width='stretch')

    # Descàrrega
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Errors")
    st.download_button(
        label="⬇️ Descarregar errors (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"errors_globals_{resultats.get('num_tasca', '')}_{resultats.get('grup', '')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_errors_globals",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

def _sidebar(grup: str):
    prof = st.session_state.user
    with st.sidebar:
        st.markdown(f"**{prof.get('nom', grup)}**")
        st.caption(f"Grup: {grup}")
        st.divider()
        if st.button("📊 Tauler", width='stretch'):
            st.session_state.page = "tauler"
            st.rerun()
        if st.button("📋 Dades de referència", width='stretch'):
            st.session_state.page = "referencia"
            st.rerun()
        if st.button("🔍 Correcció", width='stretch'):
            st.session_state.page = "correccio"
            st.rerun()
        if st.button("⚙️ Gestió de tasques", width='stretch'):
            st.session_state.page = "tasques"
            st.rerun()
        st.divider()
        if st.button("Tancar sessió", width='stretch'):
            for k in ["role", "user", "grup", "page", "tasca_sel"]:
                st.session_state[k] = None
            st.rerun()
