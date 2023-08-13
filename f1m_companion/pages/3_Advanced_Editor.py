"""Page for the Advanced Editor."""
import typing as tp

import pandas as pd
import streamlit as st
from common.components import selectbox_with_default
from common.database_translator import TranslatedDatabase
from common.initialize import init_page
from common.savefile import CompanionSaveFile

init_page()

st.title("Advanced Editor")

st.write("Edit the tables in your save.")

# Page script
if st.session_state.display_help:
    with st.expander("How does it work?"):
        st.markdown(
            """
                1. Select the save file your want to edit
                2. Select the table your want to edit
                3. Edit the values you want (some columns are uneditable)
                4. Click Apply changes (:warning: If you leave this page without applying, changes will be lost)
                5. Repack to a save file
                    1. Chose name for edited save file
                    2. Click repack
                6. Save a single table
                    1. Chose table to save as csv
                    2. Chose name of folder where to save sav
                    3. Click save
                    4. You can now use those csv files to edit tables in the simple editor
                7. Load your save in F1Manager !
            """
        )

save_files = CompanionSaveFile.dict_save_files()
st.info(f"Listed {len(save_files)} save files in companion folder.")
selected_save_name = selectbox_with_default("Select Save File to edit", save_files)
selected_save = save_files[selected_save_name]

# Only one unpacked save in the session_state at a time
# If you navigate out the page then come back, must keep the changes, so
# We need to store the translated tables in the session_state

translated_database: TranslatedDatabase
edited_tables: tp.Dict[str, pd.DataFrame]
key_save_name = "key_save_name"
key_translated_database = "key_translated_database"
key_edited_tables = "key_edited_tables"

if (
    key_translated_database not in st.session_state
    or selected_save.name != st.session_state[key_save_name]
):
    # When first render or selected save changes
    # - Extract table from the save
    # - Reset the edited_tables session_state
    st.session_state[key_save_name] = selected_save.name
    tables = selected_save.extract_tables()
    st.session_state[key_translated_database] = TranslatedDatabase(tables)
    st.session_state[key_edited_tables] = {}

translated_database = st.session_state[key_translated_database]
edited_tables = st.session_state[key_edited_tables]

selected_table_name = selectbox_with_default(
    "Select Table to edit", translated_database.tables
)

selected_table = translated_database.tables[selected_table_name]
df = st.data_editor(
    selected_table.dataframe,
    disabled=selected_table.disabled_cols,
    hide_index=True,
)

if not df.equals(selected_table.dataframe):
    edited_tables[selected_table_name] = df

if edited_tables:
    st.info(f"You've edited the tables {sorted(edited_tables)}")
else:
    st.info("No changes made.")
    st.stop()

if st.button("Apply changes"):
    for table_name, table in edited_tables.items():
        translated_database.tables[table_name].dataframe = table
    st.success("Applied changes ! ")

col1, col2 = st.columns(2)

with col2:
    st.subheader("Repack to a save file")
    new_save_name = st.text_input(
        "Choose name for the repacked save", selected_save.name + "_edited"
    )
    if st.button("Repack save"):
        new_path = selected_save.repack(
            new_save_name, translated_database.clean_tables()
        )
        st.success(f"Saved save file to {new_path}")

with col1:
    st.subheader("Save a single table as a csv file")
    selected_edited_table = selectbox_with_default(
        "Select table to save", st.session_state[key_edited_tables]
    )
    tables_folder = st.text_input("Choose folder name", "my_custom_tables")
    if st.button("Save table as csv"):
        export_path = translated_database.table_to_csv(
            selected_edited_table, tables_folder
        )
        st.success(f"Saved table to {export_path}")
