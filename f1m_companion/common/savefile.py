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
    saves_path: Path

    def __init__(self, path: Path) -> None:
        self.path = path

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other: tp.Self):
        return self.name < other.name

    @contextmanager
    def unpack(self, target_dir: Path) -> tp.Generator[sqlite3.Connection, None, None]:
        """Unpack save file and yield sqlite connection.

        Args:
            target_dir: unpack save file to dir

        Yields:
            sqlite connection to unpacked database.
        """
        process_unpack(self.path, target_dir)
        save_unpacked = target_dir / "main.db"
        sql_conn = sqlite3.connect(save_unpacked)
        try:
            yield sql_conn
        finally:
            sql_conn.close()

    def repack(self, target_stem: str, tables: tp.Dict[str, pd.DataFrame]) -> Path:
        """Repack tables to target location.

        Works by unpacking the original save file again, do not delete it !

        Args:
            target_stem: new save file name
            tables: tables to repack

        Returns:
            relative path where save file was repacked.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            with self.unpack(tmp_dir) as sql_conn:
                for table_name, table in tables.items():
                    table.to_sql(table_name, sql_conn, if_exists="replace", index=False)
                sql_conn.commit()
                new_path = (PATH_SAVES / target_stem).with_suffix(".sav")
                process_repack(tmp_dir, new_path)
        return new_path.relative_to(PATH_SAVES)

    @property
    def rich_name(self) -> str:
        """Parse save file to generate a descriptive name for save.

        format: <career_name>__<team>__<date>__<track>__<session>__<seed>
        ex:     career_Bob_Morane__Alpine__2023-06-18__Barhein__9__14815

        Returns:
            rich name.
        """
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
                        "SELECT * FROM "
                        "Save_Weekend AS w JOIN Races AS r ON w.RaceID = r.RaceID "
                        "JOIN Races_Tracks AS t ON r.TrackID = t.TrackID"
                    )
                    row = pd.read_sql_query(query, sql_conn).iloc[0]
                    track = row["Name"]
                    session = str(row["WeekendStage"])
                    elements = [save_type, team, day, track, session, seed]
                except IndexError:
                    elements = [save_type, team, day, "track", "session", seed]
        return "__".join(elements)

    def extract_tables(self) -> tp.Dict[str, pd.DataFrame]:
        """Extract list of table names from save file.

        Returns:
            list of tables.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            with self.unpack(Path(tmp_dir_str)) as sql_conn:
                df_tables = pd.read_sql_query(
                    'SELECT name from sqlite_master where type= "table";', sql_conn
                )
                table_names: tp.List[str] = sorted(df_tables["name"])
                table_names.remove("sqlite_sequence")
                tables: tp.Dict[str, pd.DataFrame] = {}
                for table_name in table_names:
                    df = pd.read_sql_query(f"SELECT * FROM {table_name}", sql_conn)
                    tables[table_name] = df
        return tables

    @classmethod
    def list_save_files(cls) -> tp.List[tp.Self]:
        """Instanciate a SaveFile for each save file found."""
        return [cls(x) for x in cls.saves_path.glob("*.sav")]


class OriginalSaveFile(SaveFile):
    """Save files found in the F1Manager SaveGames folder."""

    saves_path = PATH_SAVES

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.modified = path.stat().st_mtime
        self.name = str(
            pendulum.from_timestamp(self.modified).to_datetime_string()
            + ", "
            + self.path.stem
        )


class CompanionSaveFile(SaveFile):
    """Save files found in the Companion folder."""

    saves_path = PATH_COMPANION_SAVES

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.name = self.path.stem
