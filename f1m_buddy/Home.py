import streamlit as st
from src.buddy import init_buddy, init_sidebar

init_sidebar()
init_buddy()

st.title("Home")

st.markdown(
    """1. Go to File Import, and import your save
2. Go to Database Editor
3. Save the changes
4. Repack your save"""
)
