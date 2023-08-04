"""_summary_"""

from src.constants import PATH_BUDDY_DATA, PATH_BUDDY_SAVES, PATH_SAVES
import typing as tp
import streamlit as st
from src.buddy import init_buddy, TestData, init_sidebar
from src.unpacking import process_unpack
import pendulum
import tempfile
import sqlite3
import pandas as pd
from shutil import copyfile
from pathlib import Path

date_origin = pendulum.date(1900, 1, 1)


def check_test_data(folder: Path) -> bool:
    """_summary_

    Args:
        folder: _description_

    Returns:
        _description_
    """
    return True


def load_test_data(folder: Path) -> TestData:
    """_summary_

    Args:
        folder: _description_

    Returns:
        _description_
    """
    return TestData("bob")


@st.cache_data()
def load_all_test_data() -> tp.Dict[str, TestData]:
    """Load data of tests you've done previously, if any."""
    data = {
        str(folder): load_test_data(folder)
        for folder in PATH_BUDDY_DATA.iterdir()
        if check_test_data(folder)
    }

    if data:
        st.info(f"Loaded previous test data from {len(data)} tests.")

    return data


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


# Page
init_sidebar()
buddy = init_buddy()
buddy.testing = load_all_test_data()

st.title("Testing")
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


def format_data_name(sql_conn: sqlite3.Connection) -> str:
    """_summary_

    Args:
        sql_conn: _description_

    Returns:
        _description_
    """
    rows = pd.read_sql_query(
        "SELECT * FROM Player AS p JOIN Teams AS t ON p.TeamID = t.TeamID", sql_conn
    )
    row = rows.iloc[0]
    character_name = (
        "test"
        if row["FirstName"] == "[TEAMPRINCIPAL_TEAM]"
        else str("career_" + row["FirstName"] + "_" + row["LastName"])
    )
    team = row["TeamName"]
    seed = str(row["UniqueSeed"])
    row = pd.read_sql_query("SELECT * FROM Player_State", sql_conn).iloc[0]
    day = str(row["Day"])
    season = str(row["CurrentSeason"])
    try:
        row = pd.read_sql_query(
            "SELECT * FROM Save_Weekend AS w JOIN Races AS r ON w.RaceID = r.RaceID "
            "JOIN Races_Tracks AS t ON r.TrackID = t.TrackID",
            sql_conn,
        ).iloc[0]
        track = row["Name"]

        session = str(row["WeekendStage"])
        return "__".join([character_name, team, day, season, track, session, seed])
    except IndexError:
        return "__".join([character_name, team, day, season, seed])


if st.button("Import File"):
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        process_unpack(selected_save["filepath"], tmp_dir)
        db_unpacked = tmp_dir / "main.db"
        sql_conn = sqlite3.connect(db_unpacked)
        data_name = format_data_name(sql_conn)

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
