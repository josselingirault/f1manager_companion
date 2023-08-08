"""_summary_"""

import tempfile
import typing as tp

import pandas as pd
import streamlit as st
from src.buddy import init_buddy, init_sidebar
from src.constants import PATH_BUDDY_TEST
from src.types import SaveName
from src.utils import load_db_tables, load_save_file

init_sidebar()
init_buddy()


st.title("Analyze testing results")
if st.session_state.display_help:
    with st.expander("How does it work?"):
        st.markdown(
            """
            1. Select whether you want to look at test or career saves
            2. Pick filters to use
            """
        )


def load_tables_from_saves(
    save_names: tp.Iterable[SaveName],
) -> tp.Dict[str, pd.DataFrame]:
    """Load a defined set of tables from all selected saves."""
    fixed_tables = (
        "Races",
        "Races_Tracks",
        "Save_WeatherHistory",
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
        "Save_Weekend",
    )

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        db_files = [load_save_file(save_name, tmp_dir_str) for save_name in save_names]
        return load_db_tables(db_files, tables, fixed_tables)


save_names: tp.List[SaveName] = [
    save.stem for save in PATH_BUDDY_TEST.glob("*.sav")  # type: ignore
]

dataframes = load_tables_from_saves(save_names)
st.success("Loaded data!")

laps_times = dataframes["Save_TimingManager_Laps"]
laps_history = dataframes["Save_Strategist_LapHistory"].drop(columns=["RaceTime"])
laps_weather = dataframes["Save_WeatherHistory"]
laps_weather["Time"] = laps_weather["Time"].astype(float)

st.dataframe(laps_weather, hide_index=True)

laps = pd.merge_asof(
    laps_times.merge(
        laps_history,
        on=["CarIndex", "Lap", "DBFile"],
    ).sort_values("RaceTime"),
    laps_weather.sort_values("Time"),
    left_on="RaceTime",
    right_on="Time",
).sort_values(["CarIndex", "Lap"])

# laps = laps[laps["Lap"] > 3]
laps["LapTime"] = laps["LapTimeMS"] / 1000
laps = laps[laps["CarIndex"].isin([0, 1])]
# laps["LapTimeFit"] = PolynomialFeatures(2).fit_transform(laps[["Lap", "LapTime"]])

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


def extract_name(series: pd.Series) -> pd.Series:
    """Extract 'Charles' from '[StaffName_Forename_Male_Charles]'."""
    return series.str.strip("[|]").str.split("_").str[-1]


your_drivers["LastName"] = extract_name(your_drivers["LastName"])
your_drivers["FirstName"] = extract_name(your_drivers["FirstName"])
your_drivers["FullName"] = your_drivers["FirstName"] + " " + your_drivers["LastName"]

data = laps.merge(your_drivers, on="CarIndex")

for save in data["DBFile"].unique():
    subdata: pd.DataFrame = data[data["DBFile"] == save]
    subpath = PATH_BUDDY_TEST / f"{save}.csv"
    subdata.to_csv(subpath, index=False)


st.dataframe(data)
