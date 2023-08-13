"""Page for the File Manager."""

from shutil import copyfile

import streamlit as st
from common.components import selectbox_with_default
from common.constants import FAKE_PATH_F1M, PATH_COMPANION_SAVES, PATH_SAVES
from common.initialize import init_page
from common.savefile import OriginalSaveFile

init_page()

st.title("Import Save Files")
st.write(
    "Import your save files from the F1Manager folder so the Companion can recognize them."
)

if st.session_state.display_help:
    with st.expander("How does it work?"):
        st.markdown(
            """
            1. Select the save file your want to import
            2. Click on the import save file button
            3. Save file imported ! Companion also renamed the file with a more explicit name
            """
        )

save_files = OriginalSaveFile.dict_save_files()
st.info(f"Listed {len(save_files)} save files in SaveGames folder.")
selected_save_name = selectbox_with_default("Pick save file to import", save_files)
selected_save = save_files[selected_save_name]

new_save_path = PATH_COMPANION_SAVES / f"{selected_save.rich_name}.sav"
if new_save_path.exists():
    st.warning(f"Save file {new_save_path.stem} already exists, want to overwrite ?")
if st.button("Import Save File"):
    new_save_path = PATH_COMPANION_SAVES / f"{selected_save.rich_name}.sav"
    copyfile(selected_save.path, new_save_path)
    st.success(
        f"Copied save file to {FAKE_PATH_F1M / new_save_path.relative_to(PATH_SAVES)}"
    )
