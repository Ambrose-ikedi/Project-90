from pathlib import Path
from dotenv import load_dotenv

# Load local credentials before importing modules that read configuration.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"), override=False)

import streamlit as st
from database.db_connection import init_db
from utils.authentication import login_form, logout, current_user
from modules.ui import render_app

st.set_page_config(
    page_title="Project 90 | Recover. Learn. Grow.",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    login_form()
else:
    user = current_user()
    with st.sidebar:
        st.markdown("# 🌱 PROJECT 90")
        st.caption("Recover. Learn. Grow.")
        st.markdown("---")
        st.write(f"**{user['full_name']}**")
        st.caption(user["role"].replace("_", " ").title())
        if st.button("Sign out", use_container_width=True):
            logout()
            st.rerun()
    render_app(user)
