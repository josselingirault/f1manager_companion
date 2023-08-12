"""Home Page."""

import streamlit as st
from common.initialize import init_paths, init_sidebar

st.set_page_config(layout="wide")

init_sidebar()
init_paths()

st.title("Welcome to JoyA's F1Manager Companion")

st.markdown(
    """
    JoyA's F1Manager Companion is a small app designed to enhance the experience playing F1Manager.

    - File Manager: import your save files into Companion
    - Advanced Editor: edit your save

    :warning: This is an early version, expect bugs and a lot of memory usage.

    Want to help ? Found a bug ? Feel free to report issues on the [github page](https://github.com/josselingirault/f1manager_companion)
    """
)
