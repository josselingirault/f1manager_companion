import streamlit as st
import pandas as pd
import sqlite3
import pathlib as pl
from src.unpacking import process_unpack, process_repack

# from src.tester import do_testing
from src.buddy import init_buddy, init_sidebar


init_sidebar()
init_buddy()


with st.expander("How does it work?"):
    st.markdown(
        """1. Find your save file and unpack it
    2. Edit the tables
    3. Save the changes
    4. Repack your save"""
    )


def get_tables(conn: sqlite3.Connection):
    df = pd.read_sql_query('SELECT name from sqlite_master where type= "table";', conn)
    return sorted(df["name"])


tab_file, tab_advanced = st.tabs(["File", "Advanced Editor"])

if "is_changed" not in st.session_state:
    st.session_state.is_changed = False

with tab_file:
    # Select file
    path_str = st.text_input(
        "F1Manager Save Files Location",
        value="/usr/home/project/saves",
    )
    path: pl.Path = pl.Path(path_str)
    if not path.exists():
        st.warning(f"Folder does not exist: {path}")
        st.stop()
    save_file = st.selectbox("Select Save File", sorted(path.glob("*.sav")))
    if not save_file:
        st.stop()
    path_unpacked = path / f"{save_file.stem}_unpacked"
    path_unpacked.mkdir(exist_ok=True)
    save_unpacked = path_unpacked / "main.db"
    if save_unpacked.exists():
        st.warning(
            "You are about to override a previously unpacked save file, consider "
            "renaming the new file to avoid losing data"
        )
    if st.button("Load File"):
        process_unpack(save_file, path_unpacked)
        st.success(f"Unpacked save to {save_unpacked}")

    if st.session_state.is_changed:
        new_save_file = st.text_input("New file", value=save_file)
        if new_save_file == str(save_file):
            st.warning(
                "You are about to override the original save file, consider "
                "renaming the file to avoid losing data"
            )
        if st.button("Save File"):
            process_repack(path_unpacked, new_save_file)
            st.success(f"Repacked save to {new_save_file}")

with tab_advanced:
    if not save_unpacked.exists():
        st.warning("You need to load a save in the File tab")
        st.stop()
    sql_conn = sqlite3.connect(save_unpacked)
    tables = get_tables(sql_conn)
    selected_tables = st.multiselect("Select Tables", tables)
    if not selected_tables:
        st.stop()

    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {}
    dataframes: dict[str, pd.DataFrame] = st.session_state.dataframes
    if st.button("Save changes"):
        for table_name in selected_tables:
            res = dataframes[table_name].to_sql(
                table_name, sql_conn, index=False, if_exists="replace"
            )
        st.success(f"Saved changes to tables {selected_tables}")
        st.info("You can continue or repack your save in the File tab")
        st.session_state.is_changed = True

    for table_name in selected_tables:
        st.subheader(table_name)
        dataframes[table_name] = pd.read_sql_query(
            f"SELECT * FROM {table_name}", sql_conn
        )
        dataframes[table_name] = st.data_editor(dataframes[table_name])
