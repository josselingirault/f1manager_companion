from pathlib import Path

import streamlit as st

import common.constants as cst


def init_paths():
    """Check that the paths defined in constants exist, or create them."""
    for var_name in [x for x in vars(cst) if x.startswith("PATH_")]:
        path: Path = getattr(cst, var_name)
        path.mkdir(exist_ok=True)


def init_page():
    """Initialize the pages with the sidebar."""
    st.set_page_config(layout="wide")

    with st.sidebar:
        st.title("Settings")
        st.session_state.display_help = st.checkbox("Display help", value=True)
