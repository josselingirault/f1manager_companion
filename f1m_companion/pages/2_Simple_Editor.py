"""Page for the Advanced Editor."""
import typing as tp

import pandas as pd
import streamlit as st
from common.components import selectbox_with_default
from common.constants import PATH_COMPANION_TABLES
from common.initialize import init_page
from common.savefile import CompanionSaveFile

init_page()

# Page script
if st.session_state.display_help:
    with st.expander("How does it work?"):
        st.markdown(
            """
                1. Select the save file your want to edit
                2. Select the table your want to edit
                3. Edit the values you want (some columns are uneditable)
                4. Chose name for edited save file
                5. Click apply
                6. Load your save in F1Manager !
            """
        )

save_files = CompanionSaveFile.dict_save_files()
st.info(f"Listed {len(save_files)} save files in companion folder.")
selected_save_name = selectbox_with_default("Select Save File to edit", save_files)
selected_save = save_files[selected_save_name]

table_sets = [x.stem for x in PATH_COMPANION_TABLES.glob("*")]
selected_table_set = selectbox_with_default("Select set of tables to apply", table_sets)

path_table_set = PATH_COMPANION_TABLES / selected_table_set
table_names = [x.stem for x in path_table_set.glob("*")]

checkboxes: tp.Dict[str, bool] = {}
for table_name in table_names:
    checkboxes[table_name] = st.checkbox(table_name)

selected_tables = [k for k, v in checkboxes.items() if v]
tables = {t: pd.read_csv(path_table_set / f"{t}.csv") for t in selected_tables}

new_save_name = st.text_input(
    "File name for the repacked save", selected_save.name + "_edited"
)
if st.button("Apply changes and repack file"):
    new_path = selected_save.repack(new_save_name, tables)
    st.success(f"Saved edited save file to {new_path}")
