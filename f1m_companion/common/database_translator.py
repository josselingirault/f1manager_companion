"""Helper class for handling translated tables in the editor."""
import typing as tp
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from common.column_translators import column_translators
from common.constants import PATH_COMPANION, PATH_COMPANION_TABLES


@dataclass
class TranslatedTable:
    dataframe: pd.DataFrame
    tmp_cols: tp.List[str]
    id_cols: tp.List[str]

    @property
    def disabled_cols(self) -> tp.List[str]:
        return self.tmp_cols + self.id_cols


def translate_db_ids(
    tables: tp.Dict[str, pd.DataFrame],
    selected_table: str,
) -> TranslatedTable:
    """Translate ID columns to explicit values to give context when editing.

    Translated columns start with TMP_

    Args:
        tables: all tables
        selected_table: table to translate columns for

    Returns:
        dataframe with temporary translated columns.
    """
    dataframe = tables[selected_table].copy(deep=True)
    id_columns: tp.List[str] = [
        col for col in dataframe.columns if col in column_translators
    ]
    id_cols: tp.List[str] = []
    tmp_cols: tp.List[str] = []
    for id_col in id_columns:
        translator = column_translators.get(id_col)
        if translator is None or selected_table == translator.foreign_table_name:
            continue

        foreign_df = tables[translator.foreign_table_name].copy(deep=True)
        foreign_df[translator.id_col] = foreign_df[translator.foreign_id_col]
        foreign_df[translator.tmp_col] = (
            foreign_df[translator.foreign_value_col]
            if translator.func is None
            else foreign_df.apply(translator.func, axis=1)
        )
        tl_cols = [translator.id_col, translator.tmp_col]
        foreign_df = foreign_df[tl_cols]
        dataframe = dataframe.merge(foreign_df, on=translator.id_col)
        tmp_cols.append(translator.tmp_col)
        id_cols.append(translator.id_col)

    return TranslatedTable(dataframe.sort_values(id_columns), tmp_cols, id_cols)


class TranslatedDatabase:
    tables: tp.Dict[str, TranslatedTable]

    def __init__(self, tables: tp.Dict[str, pd.DataFrame]) -> None:
        self.translate_tables(tables)

    def translate_tables(self, tables: tp.Dict[str, pd.DataFrame]):
        """Translate all tables."""
        self.tables = {}
        for table_name in tables:
            self.tables[table_name] = translate_db_ids(tables, table_name)

    def clean_tables(self) -> tp.Dict[str, pd.DataFrame]:
        """Clean all tables in database."""
        clean_tables: tp.Dict[str, pd.DataFrame] = {}
        for table_name in self.tables:
            clean_tables[table_name] = self.clean_table(table_name)
        return clean_tables

    def clean_table(self, table_name: str) -> pd.DataFrame:
        """Remove TMP_ columns from table."""
        table = self.tables[table_name].dataframe
        return table.drop(
            columns=[col for col in table.columns if col.startswith("TMP_")]
        )

    def table_to_csv(self, table_name: str, folder_name: str) -> Path:
        """Save edited table to csv file."""
        folder_path = PATH_COMPANION_TABLES / folder_name
        folder_path.mkdir(exist_ok=True)
        path = (folder_path / table_name).with_suffix(".csv")
        self.clean_table(table_name).to_csv(path, index=False)
        return path.relative_to(PATH_COMPANION)
