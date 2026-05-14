import streamlit as st
from datetime import date, timedelta
from modules.tasques_data import (
    save_tasca,
    get_totes_tasques,
    get_nums_tasques_disponibles,
    load_tasca,
)


def show():
    grup = st.session_state.grup
    _sidebar(grup)

    st.title("⚙️ Gestió de tasques")

    tasques = get_totes_tasques(grup)

    # ── Llistat de tasques existents ─────────────────────────────────────────
    if tasques:
        st.markdown("#### Tasques configurades")
        for t in tasques:
            estat = "🟢 Activa" if t.get("activa") else "⚫ Inactiva"
            mode = "Individual" if t.get("mode_facturacio") == "individual" else "Recapitulativa"
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                c1.markdown(f"**Tasca {t['num_tasca']}**")
                c2.caption(f"Obertura: {t.get('data_obertura', '—')}")
                c3.caption(f"Tancament: {t.get('data_tancament', '—')}")
                c4.caption(f"Facturació: {mode}")
                with c5:
                    # Botó per canviar l'estat activa/inactiva
                    label_boto = "Desactivar" if t.get("activa") else "Activar"
                    if st.button(label_boto, key=f"toggle_{t['num_tasca']}"):
                        t_actual = load_tasca(t["num_tasca"], grup)
                        if t_actual:
                            t_actual["activa"] = not t_actual.get("activa", False)
                            save_tasca(t_actual)
                            st.rerun()

    # ── Nova tasca ───────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Crear nova tasca")

    nums_lliures = get_nums_tasques_disponibles(grup)
    if not nums_lliures:
        st.warning("Ja s'han creat totes les tasques possibles (02.01 – 02.99).")
        return

    with st.form("nova_tasca", clear_on_submit=False):
        num_sel = st.selectbox("Número de tasca", nums_lliures)

        c1, c2 = st.columns(2)
        with c1:
            data_obertura = st.date_input("Data d'obertura", value=date.today())
        with c2:
            # Proposa el proper divendres com a termini
            dies = (4 - date.today().weekday()) % 7
            proper_div = date.today() + timedelta(days=dies if dies > 0 else 7)
            data_tancament = st.date_input("Termini de lliurament", value=proper_div)

        mode = st.radio(
            "Mode de facturació de vendes",
            ["individual", "recapitulativa"],
            format_func=lambda x: (
                "Individual — 1 comanda → 1 albarà → 1 factura"
                if x == "individual"
                else "Recapitulativa — factura agrupa diverses comandes del mateix client"
            ),
        )
        activa = st.checkbox("Activar tasca immediatament", value=True)
        enviar = st.form_submit_button("✅ Crear tasca", type="primary", use_container_width=True)

    if enviar:
        if data_tancament < data_obertura:
            st.error("La data de tancament no pot ser anterior a la d'obertura.")
        else:
            save_tasca({
                "num_tasca": num_sel,
                "grup": grup,
                "data_obertura": data_obertura.isoformat(),
                "data_tancament": data_tancament.isoformat(),
                "mode_facturacio": mode,
                "activa": activa,
            })
            st.success(f"✅ Tasca **{num_sel}** creada correctament.")
            st.rerun()


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
