"""Page for the Advanced Editor."""
import streamlit as st
from common.components import selectbox_with_default
from common.database_translator import TranslatedDatabase
from common.initialize import init_sidebar
from common.savefile import CompanionSaveFile

st.set_page_config(layout="wide")

init_sidebar()

# Page script
with st.expander("How does it work?"):
    st.markdown("""placeholder""")

save_files = CompanionSaveFile.list_save_files()
st.info(f"Listed {len(save_files)} save files in companion folder.")
selected_save = selectbox_with_default("Select Save File to edit", save_files)
if selected_save is None:
    st.stop()


# Only one unpacked save in the session_state at a time
# If you navigate out the page then come back, must keep the changes, so:
# We need to store the translated tables in the session_state
# and load them from session_state only when
# - there exist translated_dataframes in session_state
# - the selected_save.name is the same as the save name in session_state

translated_database: TranslatedDatabase
key_save_name = "key_save_name"
key_translated_database = "key_translated_database"
if (
    key_translated_database in st.session_state
    and st.session_state[key_save_name] == selected_save.name
):
    translated_database = st.session_state[key_translated_database]
else:
    st.session_state[key_save_name] = selected_save.name
    tables = selected_save.extract_tables()
    translated_database = TranslatedDatabase(tables)

selected_table_name = selectbox_with_default(
    "Select Table to edit", translated_database.tables
)
if selected_table_name is None:
    st.stop()

selected_table = translated_database.tables[selected_table_name]
selected_table.dataframe = st.data_editor(
    selected_table.dataframe,
    disabled=selected_table.disabled_cols,
    hide_index=True,
)
st.session_state[key_translated_database] = translated_database

new_save_name = st.text_input(
    "File name for the repacked save", selected_save.name + "_edited"
)
if st.button("Apply changes and repack file"):
    new_path = selected_save.repack(new_save_name, translated_database.clean_tables())
    st.success(f"Saved edited file to {new_path}")
