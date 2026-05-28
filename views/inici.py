import streamlit as st


def show():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🏫 Empresa a l'Aula")
        st.markdown("### Correcció de tasques setmanals · CIFP Joan Taix")
        st.divider()
        st.markdown("#### Com vols accedir?")
        st.write("")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("👩‍🎓 Sóc alumne", width='stretch', type="primary"):
                st.session_state.role = "alumne"
                st.rerun()
        with c2:
            if st.button("👨‍🏫 Sóc professor", width='stretch'):
                st.session_state.role = "professor"
                st.rerun()
