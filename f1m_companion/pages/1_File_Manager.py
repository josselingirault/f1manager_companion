"""Page for the File Manager."""

from shutil import copyfile

import streamlit as st
from common.components import selectbox_with_default
from common.constants import PATH_COMPANION_SAVES, PATH_SAVES
from common.initialize import init_sidebar
from common.savefile import OriginalSaveFile

init_sidebar()

st.title("Import/Export Save Files")
if st.session_state.display_help:
    with st.expander("How does it work?"):
        st.markdown(
            """
            1. Do whatever you want in an F1Manager race
            2. Before the end of the race, save your game
            3. Click on the import save button
            """
        )

save_files = OriginalSaveFile.list_save_files()
st.info(f"Listed {len(save_files)} save files in SaveGames folder.")
selected_save = selectbox_with_default("Pick save file to import", save_files)
if selected_save is None:
    st.stop()

new_save_path = PATH_COMPANION_SAVES / f"{selected_save.rich_name}.sav"
if new_save_path.exists():
    st.warning(f"Save file {new_save_path.stem} already exists, want to overwrite ?")
if st.button("Import Save File"):
    new_save_path = PATH_COMPANION_SAVES / f"{selected_save.rich_name}.sav"
    copyfile(selected_save.path, new_save_path)
    st.success(
        "Copied save file to your F1Manager save folder at \n"
        f"{new_save_path.relative_to(PATH_SAVES)}"
    )
