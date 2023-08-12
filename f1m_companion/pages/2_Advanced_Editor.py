"""Page for the Advanced Editor."""
import streamlit as st
from common.components import selectbox_with_default
from common.database_translator import TranslatedDatabase
from common.initialize import init_sidebar
from common.savefile import CompanionSaveFile

st.set_page_config(layout="wide")

init_sidebar()

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

save_files = CompanionSaveFile.list_save_files()
st.info(f"Listed {len(save_files)} save files in companion folder.")
selected_save = selectbox_with_default("Select Save File to edit", save_files)
# if selected_save is None:
#     st.stop()

# Only one unpacked save in the session_state at a time
# If you navigate out the page then come back, must keep the changes, so:
# We need to store the translated tables in the session_state
# and load them from session_state only when
# - there exist translated_dataframes in session_state
# - the selected_save.name is the same as the save name in session_state

translated_database: TranslatedDatabase
key_save_name = "key_save_name"
key_translated_database = "key_translated_database"
key_edited_tables = "key_edited_tables"
if (
    key_translated_database in st.session_state
    and st.session_state[key_save_name] == selected_save.name
):
    translated_database = st.session_state[key_translated_database]
else:
    st.session_state[key_save_name] = selected_save.name
    st.session_state[key_edited_tables] = set()
    tables = selected_save.extract_tables()
    translated_database = TranslatedDatabase(tables)

selected_table_name = selectbox_with_default(
    "Select Table to edit", translated_database.tables
)
# if selected_table_name is None:
#     st.stop()

selected_table = translated_database.tables[selected_table_name]
edited_dataframe = st.data_editor(
    selected_table.dataframe,
    disabled=selected_table.disabled_cols,
    hide_index=True,
)
if not edited_dataframe.equals(selected_table.dataframe):
    st.session_state[key_edited_tables].add(selected_table_name)
    selected_table.dataframe = edited_dataframe

st.session_state[key_translated_database] = translated_database

if st.session_state[key_edited_tables]:
    st.info(f"You've edited the tables {st.session_state[key_edited_tables]}")
else:
    st.info("No changes made.")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Save all changes and repack to a save file")
    new_save_name = st.text_input(
        "File name for the repacked save", selected_save.name + "_edited"
    )
    if st.button("Apply changes and repack file"):
        new_path = selected_save.repack(
            new_save_name, translated_database.clean_tables()
        )
        st.success(f"Saved edited save file to {new_path}")

with col2:
    st.subheader("Save a single edited table")
    selected_edited_table = selectbox_with_default(
        "Select table to save", st.session_state[key_edited_tables]
    )
    # if selected_edited_table is None:
    #     st.stop()
    tables_folder = st.text_input("Folder", "my_custom_tables")
    if st.button("Save edited table as csv"):
        export_path = translated_database.table_to_csv(
            selected_edited_table, tables_folder
        )
        st.success(f"Saved edited table to {export_path}")
