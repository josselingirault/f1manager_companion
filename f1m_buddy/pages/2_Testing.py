"""_summary_"""

import tempfile
import typing as tp

import streamlit as st
from src.buddy import init_buddy, init_sidebar
from src.constants import PATH_BUDDY_SAVES
from src.types import Generic, SaveName
from src.utils import load_db_tables, load_save_file


def selectbox_with_default(label: str, values: tp.Iterable[Generic]) -> Generic | None:
    return st.selectbox(
        label,
        (None, *values),
        format_func=lambda x: "<select>" if x is None else x,
    )


def pick_save_type() -> tp.Literal["test", "career_"] | None:
    set_save_types: tp.Set[str] = set()
    for save_path in PATH_BUDDY_SAVES.glob("*.sav"):
        set_save_types.add(save_path.stem.split("__")[0])
    save_type = selectbox_with_default(
        "You can only pick one save type at a time", set_save_types
    )
    return save_type  # type: ignore


def filter_saves(save_type: tp.Literal["test", "career_"]) -> tp.Set[SaveName]:
    selected_saves = {x.stem for x in PATH_BUDDY_SAVES.glob(f"{save_type}*.sav")}
    st.info(f"Selected saves: {selected_saves}")
    return selected_saves  # type: ignore


def load_tables_from_saves(selected_saves: tp.Iterable[SaveName]):
    """Load a defined set of tables from all selected saves."""
    fixed_tables = (
        "Races",
        "Races_Tracks",
        "Staff_BasicData",
        "Staff_Contracts",
        "Teams",
    )
    tables = (
        "Player",
        "Save_Strategist_LapHistory",
        "Save_TimingManager_Laps",
        "Save_TimingManager_Sectors",
        "Save_WeatherHistory",
        "Save_Weekend",
    )

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        db_files = [
            load_save_file(save_name, tmp_dir_str) for save_name in selected_saves
        ]
        return load_db_tables(db_files, tables, fixed_tables)


def save_type_loader():
    with st.expander("Select the saves to analyze"):
        save_type = pick_save_type()
        if save_type is None:
            st.stop()
        selected_saves = filter_saves(save_type)
        dataframes = load_tables_from_saves(selected_saves)
        st.success("Loaded data!")
        return dataframes


init_sidebar()
init_buddy()


st.title("Analyze testing results")

dataframes = save_type_loader()

with st.expander("dev"):
    st.info(sorted(dataframes.keys()))


# class SaveFile(tp.TypedDict):
#     filepath: Path
#     modified: float


# def list_save_files() -> tp.List[SaveFile]:
#     """_summary_"""
#     save_files: tp.List[SaveFile] = sorted(
#         [
#             {"filepath": x, "modified": x.stat().st_mtime}
#             for x in PATH_SAVES.glob("*.sav")
#         ],
#         key=lambda x: x["modified"],
#         reverse=True,
#     )
#     st.info(f"Listed {len(save_files)} save files.")
#     return save_files


# def format_savefile_name(savefile: SaveFile) -> str:
#     """"""
#     return str(
#         pendulum.from_timestamp(savefile["modified"]).to_datetime_string()
#         + ", "
#         + savefile["filepath"].stem
#     )


# init_sidebar()
# init_buddy()

# st.title("Import Save Files")
# if st.session_state.display_help:
#     with st.expander("How does it work?"):
#         st.markdown(
#             """
#             1. Do whatever you want in an F1Manager race
#             2. Before the end of the race, save your game
#             3. Click on the import save button
#             """
#         )

# selected_save = st.selectbox(
#     "Pick save file to import",
#     list_save_files(),
#     format_func=lambda x: format_savefile_name(x),
# )
# if not selected_save:
#     st.stop()


# def format_data_name(sql_conn: sqlite3.Connection) -> str:
#     """_summary_

#     Args:
#         sql_conn: _description_

#     Returns:
#         _description_
#     """
#     rows = pd.read_sql_query(
#         "SELECT * FROM Player AS p JOIN Teams AS t ON p.TeamID = t.TeamID", sql_conn
#     )
#     row = rows.iloc[0]
#     character_name = (
#         "test"
#         if row["FirstName"] == "[TEAMPRINCIPAL_TEAM]"
#         else str("career_" + row["FirstName"] + "_" + row["LastName"])
#     )
#     team = row["TeamName"]
#     seed = str(row["UniqueSeed"])
#     row = pd.read_sql_query("SELECT * FROM Player_State", sql_conn).iloc[0]
#     day = str(row["Day"])
#     season = str(row["CurrentSeason"])
#     try:
#         row = pd.read_sql_query(
#             "SELECT * FROM Save_Weekend AS w JOIN Races AS r ON w.RaceID = r.RaceID "
#             "JOIN Races_Tracks AS t ON r.TrackID = t.TrackID",
#             sql_conn,
#         ).iloc[0]
#         track = row["Name"]

#         session = str(row["WeekendStage"])
#         return "__".join([character_name, team, day, season, track, session, seed])
#     except IndexError:
#         return "__".join([character_name, team, day, season, seed])


# if st.button("Import File"):
#     with tempfile.TemporaryDirectory() as tmp_dir_str:
#         tmp_dir = Path(tmp_dir_str)
#         process_unpack(selected_save["filepath"], tmp_dir)
#         db_unpacked = tmp_dir / "main.db"
#         sql_conn = sqlite3.connect(db_unpacked)
#         data_name = format_data_name(sql_conn)

#     new_save_path = PATH_BUDDY_SAVES / f"{data_name}.sav"
#     if new_save_path.exists():
#         st.warning(
#             f"Save file {new_save_path.stem} already exists, delete it manually if
# you"
#             "want to replace it."
#         )
#         st.stop()
#     copyfile(selected_save["filepath"], new_save_path)
#     st.success(f"Copied save file to {new_save_path}")
#     new_data_path = PATH_BUDDY_DATA / data_name
#     new_data_path.mkdir()
