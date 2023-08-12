import sqlite3
import tempfile
import typing as tp
from abc import ABC
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import pendulum

from common.constants import PATH_COMPANION_SAVES, PATH_SAVES
from common.xaranaktu.unpacking import process_repack, process_unpack


class SaveFile(ABC):
    name: str

    def __init__(self, path: Path) -> None:
        self.path = path

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other: tp.Self):
        return self.name < other.name

    @contextmanager
    def unpack(self, target_dir: Path) -> tp.Generator[sqlite3.Connection, None, None]:
        process_unpack(self.path, target_dir)
        save_unpacked = target_dir / "main.db"
        sql_conn = sqlite3.connect(save_unpacked)
        try:
            yield sql_conn
        finally:
            sql_conn.close()

    def repack(self, target_stem: str, dataframes: tp.Dict[str, pd.DataFrame]) -> Path:
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            with self.unpack(tmp_dir) as sql_conn:
                for table_name, df in dataframes.items():
                    df.to_sql(table_name, sql_conn, if_exists="replace", index=False)
                sql_conn.commit()
                new_path = (PATH_SAVES / target_stem).with_suffix(".sav")
                process_repack(tmp_dir, new_path)
        return new_path.relative_to(PATH_SAVES)

    @property
    def rich_name(self) -> str:
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            with self.unpack(Path(tmp_dir_str)) as sql_conn:
                query = (
                    "SELECT * FROM Player AS p JOIN Teams AS t ON p.TeamID = t.TeamID"
                )
                row = pd.read_sql_query(query, sql_conn).iloc[0]
                save_type = (
                    "test"
                    if row["FirstName"] == "[TEAMPRINCIPAL_TEAM]"
                    else str("career_" + row["FirstName"] + "_" + row["LastName"])
                )
                team = row["TeamName"]
                seed = str(row["UniqueSeed"])
                row = pd.read_sql_query("SELECT * FROM Player_State", sql_conn).iloc[0]
                day = (
                    pendulum.date(1900, 1, 1).add(days=int(row["Day"])).to_date_string()
                )
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

    def extract_dataframes(self) -> tp.Dict[str, pd.DataFrame]:
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            with self.unpack(Path(tmp_dir_str)) as sql_conn:
                df_tables = pd.read_sql_query(
                    'SELECT name from sqlite_master where type= "table";', sql_conn
                )
                table_names: tp.List[str] = sorted(df_tables["name"])
                table_names.remove("sqlite_sequence")
                dataframes: tp.Dict[str, pd.DataFrame] = {}
                for table_name in table_names:
                    df = pd.read_sql_query(f"SELECT * FROM {table_name}", sql_conn)
                    dataframes[table_name] = df
        return dataframes


class OriginalSaveFile(SaveFile):
    """Save files found in the F1Manager SaveGames folder.

    Args:
        SaveFile: _description_
    """

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.modified = path.stat().st_mtime
        self.name = str(
            pendulum.from_timestamp(self.modified).to_datetime_string()
            + ", "
            + self.path.stem
        )

    @classmethod
    def list_save_files(cls) -> tp.List[tp.Self]:
        """Instanciate a SaveFile for each save file found."""
        return [cls(x) for x in PATH_SAVES.glob("*.sav")]


class CompanionSaveFile(SaveFile):
    """Save files found in the Companion folder

    Args:
        SaveFile: _description_
    """

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.name = self.path.stem

    @classmethod
    def list_save_files(cls) -> tp.List[tp.Self]:
        """Instanciate a SaveFile for each save file found."""
        return [cls(x) for x in PATH_COMPANION_SAVES.glob("*.sav")]
