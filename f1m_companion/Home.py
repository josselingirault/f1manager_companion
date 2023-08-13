"""Home Page."""

import streamlit as st
from common.initialize import init_page, init_paths

init_page()
init_paths()

st.title("Welcome to JoyA's F1Manager Companion")

st.markdown(
    """
    The F1Manager Companion is a small app designed to enhance the experience playing F1Manager.

    - File Manager: import your save files into Companion
    - Simple Editor: edit your save by simply replacing database tables !
    - Advanced Editor: edit your save in a more a more complex editor

    :warning: This is an early version, expect bugs and a lot of memory usage.

    Want to help ? Found a bug ? Feel free to report issues on the [github page](https://github.com/josselingirault/f1manager_companion)
    """
)
