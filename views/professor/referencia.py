import streamlit as st
from modules.tasques_data import get_totes_tasques
from modules.alumnes_data import get_alumnes_per_grup
from modules.referencia_data import (
    generar_plantilla,
    processar_plantilla,
    save_referencia,
    load_referencia,
    referencia_completa,
)
from modules.utils import fmt_data


def show():
    grup = st.session_state.grup
    _sidebar(grup)

    st.title("📋 Dades de referència")
    st.caption("El professor descarrega la plantilla, l'omple amb les dades reals i la puja.")

    tasques = get_totes_tasques(grup)
    if not tasques:
        st.info("No hi ha cap tasca creada. Crea'n una des de ⚙️ Gestió de tasques.")
        return

    alumnes = get_alumnes_per_grup(grup)

    opcions = {
        f"Tasca {t['num_tasca']}  ({fmt_data(t.get('data_tancament', ''))})": t
        for t in tasques
    }
    sel = st.selectbox("Selecciona la tasca", list(opcions.keys()))
    tasca = opcions[sel]
    num_tasca = tasca["num_tasca"]

    ref_existent = load_referencia(num_tasca, grup)
    n_alumnes = len(alumnes)
    n_amb_ref = sum(1 for a in alumnes if str(a["expedient"]) in ref_existent)

    # ── Estat actual ──────────────────────────────────────────────────────────
    st.divider()
    col1, col2 = st.columns(2)
    col1.metric("Alumnes amb dades carregades", f"{n_amb_ref} / {n_alumnes}")

    if n_amb_ref == n_alumnes:
        col2.success("✅ Dades completes per a tots els alumnes")
    elif n_amb_ref > 0:
        col2.warning(f"⚠️ Falten dades per a {n_alumnes - n_amb_ref} alumne(s)")
    else:
        col2.info("ℹ️ Encara no s'han carregat dades de referència per a aquesta tasca")

    # ── Descàrrega de la plantilla ────────────────────────────────────────────
    st.divider()
    st.markdown("#### 1. Descarrega la plantilla")
    st.caption(
        "La plantilla inclou tots els alumnes del grup amb les columnes pre-emplenades "
        "(fons blau). Omple les cel·les grogues i puja el fitxer."
    )

    plantilla = generar_plantilla(num_tasca, grup, alumnes)
    st.download_button(
        label="⬇️ Descarregar plantilla xlsx",
        data=plantilla,
        file_name=f"referencia_{num_tasca}_{grup}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # ── Pujada de la plantilla emplenada ──────────────────────────────────────
    st.divider()
    st.markdown("#### 2. Puja la plantilla emplenada")

    fitxer = st.file_uploader(
        "Plantilla emplenada",
        type=["xlsx"],
        label_visibility="collapsed",
    )

    if fitxer:
        contingut = fitxer.read()
        dades, errors = processar_plantilla(contingut, num_tasca, grup)

        if errors:
            st.error(f"S'han trobat {len(errors)} error(s). Corregeix-los i torna a pujar el fitxer.")
            for e in errors:
                st.markdown(f"- {e}")
        else:
            n_exp = len(dades)
            n_compres = sum(len(v["compres"]) for v in dades.values())
            n_vendes  = sum(len(v["vendes"])  for v in dades.values())

            st.success(
                f"Fitxer vàlid: **{n_exp}** alumnes, "
                f"**{n_compres}** operacions de compra, "
                f"**{n_vendes}** operacions de venda."
            )

            if st.button("💾 Guardar dades de referència", type="primary", use_container_width=True):
                # Fusionar amb les dades existents (no esborrar R_DATA_ENTREGA_TASCA ja guardades)
                ref_actual = load_referencia(num_tasca, grup)
                for exp, nou in dades.items():
                    if exp in ref_actual:
                        # Conservar R_DATA_ENTREGA_TASCA si ja existia
                        for i, compra in enumerate(nou["compres"]):
                            if i < len(ref_actual[exp].get("compres", [])):
                                compra["R_DATA_ENTREGA_TASCA"] = ref_actual[exp]["compres"][i].get(
                                    "R_DATA_ENTREGA_TASCA", ""
                                )
                    ref_actual[exp] = nou
                save_referencia(num_tasca, grup, ref_actual)
                st.success("✅ Dades de referència guardades correctament.")
                st.rerun()

    # ── Resum de les dades carregades ─────────────────────────────────────────
    if ref_existent:
        st.divider()
        st.markdown("#### Dades carregades")
        _mostrar_resum(ref_existent, alumnes)


def _mostrar_resum(ref: dict, alumnes: list[dict]) -> None:
    files = []
    for alumne in alumnes:
        exp = str(alumne["expedient"])
        if exp not in ref:
            files.append({
                "Alumne": alumne["nom"],
                "Compres": "—",
                "Vendes": "—",
                "Estat": "❌ Sense dades",
            })
        else:
            d = ref[exp]
            files.append({
                "Alumne": alumne["nom"],
                "Compres": len(d.get("compres", [])),
                "Vendes": len(d.get("vendes", [])),
                "Estat": "✅ Complet",
            })

    import pandas as pd
    st.dataframe(pd.DataFrame(files), hide_index=True, use_container_width=True)


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
