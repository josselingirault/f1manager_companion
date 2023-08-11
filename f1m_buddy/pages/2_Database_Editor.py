import sqlite3
import tempfile
import typing as tp
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

# from src.tester import do_testing
from src.buddy import init_buddy, init_sidebar
from src.constants import PATH_BUDDY_SAVES
from src.unpacking import process_unpack

Generic = tp.TypeVar("Generic")

st.set_page_config(layout="wide")

init_sidebar()
init_buddy()


def load_save_file(save_name: str, tmp_dir_str: str) -> Path:
    """Get a .sav file and unpack it to a .db file."""
    save_path = (PATH_BUDDY_SAVES / save_name).with_suffix(".sav")
    tmp_dir = Path(tmp_dir_str)
    process_unpack(save_path, tmp_dir)
    return (tmp_dir / "main.db").rename((tmp_dir / save_name).with_suffix(".db"))


def list_tables(conn: sqlite3.Connection) -> tp.List[str]:
    df = pd.read_sql_query('SELECT name from sqlite_master where type= "table";', conn)
    return sorted(df["name"])


def extract_name(series: pd.Series) -> pd.Series:
    """Extract 'Charles' from '[StaffName_Forename_Male_Charles]'."""
    return series.str.strip("[|]").str.split("_").str[-1]


def extract_full_name(row: pd.Series) -> pd.Series:
    """Extract 'Charles' and 'Leclerc' from '[StaffName_Forename_Male_Charles]'."""
    first_name: str = row["FirstName"]
    first_name = first_name.strip("[|]").split("_")[-1]
    last_name: str = row["LastName"]
    last_name = last_name.strip("[|]").split("_")[-1]
    row["FullName"] = first_name + " " + last_name
    return row["FullName"]


@dataclass
class ColumnTranslation:
    id_col: str
    foreign_table_name: str
    foreign_id_col: str
    foreign_value_col: str
    func: tp.Callable | None

    def tmp_col(self) -> str:
        return f"TMP_{self.id_col}_{self.foreign_value_col}"


CONFIG_COLUMN_TRANSLATION = [
    ColumnTranslation(
        "StaffID", "Staff_BasicData", "StaffID", "FullName", extract_full_name
    ),
    ColumnTranslation(
        "StatID", "Staff_Enum_PerformanceStatTypes", "Value", "Name", None
    ),
]
translators = {x.id_col: x for x in CONFIG_COLUMN_TRANSLATION}


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


def selectbox_with_default(
    label: str,
    values: tp.Iterable[Generic],
    default=None,
    default_display="<select>",
) -> Generic:
    """_summary_

    Args:
        label: _description_
        values: _description_
        default: _description_. Defaults to None.
        default_display: _description_. Defaults to "<select>".

    Returns:
        _description_
    """
    key = hash(label)
    if key not in st.session_state:
        st.session_state[key] = None
    default = st.session_state[key]
    st.session_state[key] = st.selectbox(
        label,
        (default, *sorted(list(values))),
        format_func=lambda x: default_display if x is None else x,
    )
    if st.session_state[key] is None:
        st.stop()
    return st.session_state[key]


# Page script
with st.expander("How does it work?"):
    st.markdown("""placeholder""")

save_files = sorted(PATH_BUDDY_SAVES.glob("*.sav"))

selected_save_name = selectbox_with_default(
    "Select Save File",
    [x.stem for x in save_files],
)

key = hash(selected_save_name)
if key not in st.session_state:
    tmp_path = PATH_BUDDY_SAVES / "tmp"
    for file in tmp_path.glob("*"):
        file.unlink()

    st.session_state[key] = True

# Once save has been selected
with tempfile.TemporaryDirectory() as tmp_dir_str:
    db_file = load_save_file(selected_save_name, tmp_dir_str)
    sql_conn = sqlite3.connect(db_file)
    table_names = list_tables(sql_conn)
    dataframes: tp.Dict[str, pd.DataFrame] = {}
    for table_name in table_names:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", sql_conn)
        dataframes[table_name] = df

selected_table = selectbox_with_default("Select Table", [x for x in table_names])

ssk_table = hash(selected_table)
if ssk_table not in st.session_state:
    st.session_state[ssk_table] = translate_db_ids(dataframes, selected_table)

st.session_state[ssk_table].dataframe = st.data_editor(
    st.session_state[ssk_table].dataframe,
    disabled=st.session_state[ssk_table].disabled_cols(),
    hide_index=True,
)

if st.button("Apply changes"):
    dataframes[selected_table] = st.session_state[ssk_table].dataframe.drop(
        columns=st.session_state[ssk_table].tmp_cols
    )
