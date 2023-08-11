"""Folders for functions with no streamlit logic."""

import sqlite3
import typing as tp
from pathlib import Path

import pandas as pd

from src.constants import PATH_BUDDY_TEST
from src.unpacking import process_unpack


def load_save_file(save_name: str, tmp_dir_str: str) -> Path:
    save_path = (PATH_BUDDY_TEST / save_name).with_suffix(".sav")
    tmp_dir = Path(tmp_dir_str)
    process_unpack(save_path, tmp_dir)
    return (tmp_dir / "main.db").rename((tmp_dir / save_name).with_suffix(".db"))


def load_db_tables(
    db_files: tp.Iterable[Path],
    tables: tp.Iterable[str],
    fixed_tables: None | tp.Iterable[str] = None,
) -> tp.Dict[str, pd.DataFrame]:
    all_tables = list(tables)
    if fixed_tables:
        all_tables.extend(fixed_tables)
    dataframe_lists: tp.Dict[str, tp.List[pd.DataFrame]] = {x: [] for x in all_tables}
    for index, db_file in enumerate(db_files):
        sql_conn = sqlite3.connect(db_file)
        if fixed_tables and index == 0:
            for table_name in fixed_tables:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", sql_conn)
                dataframe_lists[table_name].append(df)
        for table_name in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", sql_conn)
            df["DBFile"] = db_file.stem
            dataframe_lists[table_name].append(df)
    return {
        table_name: pd.concat(dataframes)
        for table_name, dataframes in dataframe_lists.items()
    }
