import streamlit as st
import pandas as pd
import sqlite3
import pathlib as pl
from src.unpacking import process_unpack

st.title("F1Manager 2023 Database Editor")

import os
import getpass

st.text(os.getcwd())
st.text(getpass.getuser())


@st.cache_resource
def get_sql_conn(path: pl.Path):
    return sqlite3.connect(path, check_same_thread=False)


def get_tables(conn: sqlite3.Connection):
    return sorted(
        pd.read_sql_query('SELECT name from sqlite_master where type= "table";', conn)[
            "name"
        ]
    )


tab_file, tab_advanced = st.tabs(["File", "Advanced Editor"])

with tab_file:
    # Select file
    save_file: None | pl.Path = None
    path_str = st.text_input(
        "F1Manager Save Files Location",
        value="C:\\Users\\<yourname>\\AppData\\Local\\F1Manager23\\Saved\\SaveGames",
    )
    path: pl.Path = pl.Path(path_str)
    if not path.exists():
        st.warning(f"Folder does not exist: {path}")
        st.stop()
    save_file = st.selectbox("Select Save File", sorted(path.glob("*")))
    if not save_file:
        st.stop()
    path_unpacked = path / f"{save_file.stem}_unpacked"
    path_unpacked.mkdir(exist_ok=True)
    save_unpacked = path_unpacked / "main.db"
    if st.button("Load File"):
        if not save_unpacked.exists():
            process_unpack(save_file, path_unpacked)


with tab_advanced:
    if not save_unpacked.exists():
        st.warning("You need to load a save in the File tab")
        st.stop()

    sql_conn = get_sql_conn(save_unpacked)
    tables = get_tables(sql_conn)
    selected_tables = st.multiselect("Select Tables", tables)
    if not selected_tables:
        st.stop()

    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {}
    dataframes: dict[str, pd.DataFrame] = st.session_state.dataframes
    if st.button("Save changes"):
        cursor = sql_conn.cursor()
        for table_name in selected_tables:
            cursor.execute(f"DROP TABLE {table_name}")
            dataframes[table_name].to_sql(table_name, sql_conn)
        sql_conn.commit()

    for table_name in selected_tables:
        st.subheader(table_name)
        dataframes[table_name] = pd.read_sql_query(
            f"SELECT * FROM {table_name}", sql_conn
        )
        st.data_editor(dataframes[table_name])
