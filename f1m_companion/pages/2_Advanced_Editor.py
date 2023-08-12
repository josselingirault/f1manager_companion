import typing as tp
from dataclasses import dataclass

import pandas as pd
import streamlit as st
from common.components import selectbox_with_default
from common.initialize import init_sidebar
from common.savefile import CompanionSaveFile
from common.translators import translators

st.set_page_config(layout="wide")

init_sidebar()


@dataclass
class TranslatedTable:
    dataframe: pd.DataFrame
    tmp_cols: tp.List[str]
    id_cols: tp.List[str]

    def disabled_cols(self) -> tp.List[str]:
        return self.tmp_cols + self.id_cols


def translate_db_ids(
    dataframes: tp.Dict[str, pd.DataFrame],
    selected_table: str,
) -> TranslatedTable:
    """Translate ID columns to explicit values to give context when editing.

    Args:
        dataframes: all dataframes
        selected_table: table to translate ids for

    Returns:
        dataframe with temporary columns.
    """
    dataframe = dataframes[selected_table].copy(deep=True)
    id_columns: tp.List[str] = [col for col in dataframe.columns if col in translators]
    id_cols: tp.List[str] = []
    tmp_cols: tp.List[str] = []
    for id_col in id_columns:
        translator = translators.get(id_col)
        if translator is None or selected_table == translator.foreign_table_name:
            continue

        foreign_df = dataframes[translator.foreign_table_name].copy(deep=True)
        foreign_df[translator.id_col] = foreign_df[translator.foreign_id_col]
        foreign_df[translator.tmp_col()] = (
            foreign_df[translator.foreign_value_col]
            if translator.func is None
            else foreign_df.apply(translator.func, axis=1)
        )
        tl_cols = [translator.id_col, translator.tmp_col()]
        foreign_df = foreign_df[tl_cols]
        dataframe = dataframe.merge(foreign_df, on=translator.id_col)
        tmp_cols.append(translator.tmp_col())
        id_cols.append(translator.id_col)

    return TranslatedTable(dataframe.sort_values(id_columns), tmp_cols, id_cols)


# Page script
with st.expander("How does it work?"):
    st.markdown("""placeholder""")

save_files = CompanionSaveFile.list_save_files()
st.info(f"Listed {len(save_files)} save files in companion folder.")
selected_save = selectbox_with_default("Select Save File to edit", save_files)
if selected_save is None:
    st.stop()


@st.cache_data()
def translate_dataframe_ids(
    dataframes: tp.Dict[str, pd.DataFrame]
) -> tp.Dict[str, TranslatedTable]:
    translated_dataframes: tp.Dict[str, TranslatedTable] = {}
    for table_name in dataframes:
        translated_dataframes[table_name] = translate_db_ids(dataframes, table_name)
    return translated_dataframes


# Only one unpacked save in the session_state at a time
# If you navigate out the page then come back, must keep the changes, so:
# We need to store the translated tables in the session_state
# and load them from session_state only when
# - there exist translated_dataframes in session_state
# - the selected_save.name is the same as the save name in session_state

translated_dataframes: tp.Dict[str, TranslatedTable]
key_save_name = "key_save_name"
key_translated_dataframes = "key_translated_dataframes"
if (
    key_translated_dataframes in st.session_state
    and st.session_state[key_save_name] == selected_save.name
):
    translated_dataframes = st.session_state[key_translated_dataframes]
else:
    st.session_state[key_save_name] = selected_save.name
    dataframes = selected_save.extract_dataframes()
    translated_dataframes = translate_dataframe_ids(dataframes)

selected_table_name = selectbox_with_default(
    "Select Table to edit", translated_dataframes
)
if selected_table_name is None:
    st.stop()

selected_table = translated_dataframes[selected_table_name]
selected_table.dataframe = st.data_editor(
    selected_table.dataframe,
    disabled=selected_table.disabled_cols(),
    hide_index=True,
)
st.session_state[key_translated_dataframes] = translated_dataframes

new_save_name = st.text_input(
    "File name for the repacked save", selected_save.name + "_edited"
)
if st.button("Apply changes and repack file"):
    cleaned_dataframes = {}
    for table_name, tf_dataframe in translated_dataframes.items():
        df = tf_dataframe.dataframe
        cleaned_dataframes[table_name] = df.drop(
            columns=[col for col in df.columns if col.startswith("TMP_")]
        )
    new_path = selected_save.repack(new_save_name, cleaned_dataframes)
    st.success(f"Saved edited file to {new_path}")
