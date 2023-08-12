"""_summary_"""

import tempfile
import typing as tp

import pandas as pd
import streamlit as st
from common.constants import PATH_COMPANION_SAVES
from common.initialize import init_paths, init_sidebar
from common.types import Generic, SaveName
from common.utils import load_db_tables, load_save_file


def selectbox_with_default(
    label: str, values: tp.Iterable[Generic], default=None, default_display="<select>"
) -> Generic | None:
    return st.selectbox(
        label,
        (default, *values),
        format_func=lambda x: default_display if x is None else x,
    )


def pick_save_type() -> tp.Literal["test", "career_"] | None:
    set_save_types: tp.Set[str] = set()
    for save_path in PATH_COMPANION_SAVES.glob("*.sav"):
        set_save_types.add(save_path.stem.split("__")[0])
    save_type = selectbox_with_default(
        "You can only pick one save type at a time", set_save_types
    )
    return save_type  # type: ignore


def filter_saves(save_type: tp.Literal["test", "career_"]) -> tp.Set[SaveName]:
    selected_saves = {x.stem for x in PATH_COMPANION_SAVES.glob(f"{save_type}*.sav")}
    st.info(f"Selected saves: {selected_saves}")
    return selected_saves  # type: ignore


def load_tables_from_saves(
    selected_saves: tp.Iterable[SaveName],
) -> tp.Dict[str, pd.DataFrame]:
    """Load a defined set of tables from all selected saves."""
    fixed_tables = (
        "Races",
        "Races_Tracks",
        "Staff_BasicData",
        "Staff_DriverData",
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


def save_type_loader() -> tp.Dict[str, pd.DataFrame]:
    """Create the layout for save selection.

    Returns:
        selected data tables
    """
    with st.expander("Select the saves to load"):
        save_type = pick_save_type()
        if save_type is None:
            st.stop()
        selected_saves = filter_saves(save_type)
        dataframes = load_tables_from_saves(selected_saves)
        st.success("Loaded data!")
        return dataframes


init_sidebar()
init_paths()


st.title("Analyze testing results")
if st.session_state.display_help:
    with st.expander("How does it work?"):
        st.markdown(
            """
            1. Select whether you want to look at test or career saves
            2. Pick filters to use
            """
        )

dataframes = save_type_loader()

st.header("Analysis")


# st.subheader("Select the saves to analyze")
# save_names: tp.Iterable[SaveName] = dataframes["Player"]["DBFile"]  # type: ignore
# checkboxes = {save_name: st.checkbox(save_name) for save_name in sorted(save_names)}
# for save_name, check in checkboxes.items():


player = dataframes["Player"][["TeamID", "UniqueSeed"]]
teams = dataframes["Teams"][["TeamID", "TeamName"]]
drivers = dataframes["Staff_DriverData"][["StaffID"]]
contracts = dataframes["Staff_Contracts"][["TeamID", "StaffID", "PosInTeam"]]
humans = dataframes["Staff_BasicData"][["StaffID", "FirstName", "LastName"]]

your_drivers = (
    player.merge(teams, on="TeamID")
    .merge(contracts, on="TeamID")
    .merge(humans, on="StaffID")
    .merge(drivers, on="StaffID")
)
your_drivers["CarIndex"] = (
    (your_drivers["TeamID"] - 1) * 2 + your_drivers["PosInTeam"] - 1
)
your_drivers = your_drivers[your_drivers["PosInTeam"] < 3]

weekend = dataframes["Save_Weekend"][["RaceID"]]
races = dataframes["Races"][["RaceID", "TrackID"]]
tracks = dataframes["Races_Tracks"][["TrackID", "Name"]]


def extract_name(series: pd.Series) -> pd.Series:
    """Extract 'Charles' from '[StaffName_Forename_Male_Charles]'."""
    return series.str.strip("[|]").str.split("_").str[-1]


your_drivers["FullName"] = (
    extract_name(your_drivers["FirstName"])
    + " "
    + extract_name(your_drivers["LastName"])
)

st.dataframe(your_drivers, hide_index=True)
your_drivers = your_drivers[["CarIndex", "FullName", "TeamName"]]

race_info = weekend.merge(races, on="RaceID").merge(tracks, on="TrackID")


st.dataframe(your_drivers, hide_index=True)
st.dataframe(race_info, hide_index=True)
with st.expander("dev"):
    st.info(sorted(dataframes.keys()))

st.dataframe(dataframes["Player"], hide_index=True)
