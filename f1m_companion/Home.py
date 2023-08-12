"""Home Page."""

import streamlit as st
from common.initialize import init_paths, init_sidebar

init_sidebar()
init_paths()

st.title("Welcome to JoyA's F1Manager Companion")

st.markdown(
    """1. Go to File Import, and import your save
2. Go to Database Editor
3. Save the changes
4. Repack your save"""
)
