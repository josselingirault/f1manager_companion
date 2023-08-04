"""_summary_"""

import sqlite3
import tempfile
import typing as tp
from pathlib import Path
from shutil import copyfile

import pandas as pd
import pendulum
import streamlit as st
from src.buddy import init_buddy, init_sidebar
from src.constants import PATH_BUDDY_DATA, PATH_BUDDY_SAVES, PATH_SAVES
from src.unpacking import process_unpack

date_origin = pendulum.date(1900, 1, 1)


class SaveFile(tp.TypedDict):
    filepath: Path
    modified: float


def list_save_files() -> tp.List[SaveFile]:
    """_summary_"""
    save_files: tp.List[SaveFile] = sorted(
        [
            {"filepath": x, "modified": x.stat().st_mtime}
            for x in PATH_SAVES.glob("*.sav")
        ],
        key=lambda x: x["modified"],
        reverse=True,
    )
    st.info(f"Listed {len(save_files)} save files.")
    return save_files


def format_savefile_name(savefile: SaveFile) -> str:
    """"""
    return str(
        pendulum.from_timestamp(savefile["modified"]).to_datetime_string()
        + ", "
        + savefile["filepath"].stem
    )


def format_save_name(sql_conn: sqlite3.Connection) -> str:
    """_summary_

    Args:
        sql_conn: _description_

    Returns:
        _description_
    """
    query = "SELECT * FROM Player AS p JOIN Teams AS t ON p.TeamID = t.TeamID"
    row = pd.read_sql_query(query, sql_conn).iloc[0]
    save_type = (
        "test"
        if row["FirstName"] == "[TEAMPRINCIPAL_TEAM]"
        else str("career_" + row["FirstName"] + "_" + row["LastName"])
    )
    team = row["TeamName"]
    seed = str(row["UniqueSeed"])
    row = pd.read_sql_query("SELECT * FROM Player_State", sql_conn).iloc[0]
    day = pendulum.date(1900, 1, 1).add(days=int(row["Day"])).to_date_string()
    try:
        query = (
            "SELECT * FROM Save_Weekend AS w JOIN Races AS r ON w.RaceID = r.RaceID "
            "JOIN Races_Tracks AS t ON r.TrackID = t.TrackID"
        )
        row = pd.read_sql_query(query, sql_conn).iloc[0]
        track = row["Name"]
        session = str(row["WeekendStage"])
        elements = [save_type, team, day, track, session, seed]
    except IndexError:
        elements = [save_type, team, day, "track", "session", seed]
    return "__".join(elements)


init_sidebar()
init_buddy()

st.title("Import Save Files")
if st.session_state.display_help:
    with st.expander("How does it work?"):
        st.markdown(
            """
            1. Do whatever you want in an F1Manager race
            2. Before the end of the race, save your game
            3. Click on the import save button
            """
        )

selected_save = st.selectbox(
    "Pick save file to import",
    list_save_files(),
    format_func=lambda x: format_savefile_name(x),
)
if not selected_save:
    st.stop()


if st.button("Import File"):
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        process_unpack(selected_save["filepath"], tmp_dir)
        db_unpacked = tmp_dir / "main.db"
        sql_conn = sqlite3.connect(db_unpacked)
        data_name = format_save_name(sql_conn)
        sql_conn.close()

    new_save_path = PATH_BUDDY_SAVES / f"{data_name}.sav"
    if new_save_path.exists():
        st.warning(
            f"Save file {new_save_path.stem} already exists, delete it manually if you "
            "want to replace it."
        )
        st.stop()
    copyfile(selected_save["filepath"], new_save_path)
    st.success(f"Copied save file to {new_save_path}")
    new_data_path = PATH_BUDDY_DATA / data_name
    new_data_path.mkdir()
