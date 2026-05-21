import streamlit as st

st.set_page_config(
    page_title="Empresa a l'Aula",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inicialització de l'estat de sessió ──────────────────────────────────────
_defaults = {
    "role": None,       # None | "alumne" | "professor"
    "user": None,       # dict amb les dades de l'usuari autenticat
    "grup": None,       # "ADG21" | "ADG32"
    "page": None,       # pàgina activa dins la zona (portal, lliurament, tauler, tasques)
    "tasca_sel": None,  # num_tasca seleccionada per a lliurament
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Router principal ─────────────────────────────────────────────────────────
role = st.session_state.role
user = st.session_state.user
page = st.session_state.page

if role is None:
    from views.inici import show
    show()

elif role == "alumne":
    if user is None:
        from views.alumne.identificacio import show
        show()
    elif page == "lliurament":
        from views.alumne.lliurament import show
        show()
    else:
        from views.alumne.portal import show
        show()

elif role == "professor":
    if user is None:
        from views.professor.login import show
        show()
    elif page == "tasques":
        from views.professor.tasques import show
        show()
    elif page == "referencia":
        from views.professor.referencia import show
        show()
    elif page == "correccio":
        from views.professor.correccio import show
        show()
    else:
        from views.professor.tauler import show
        show()
