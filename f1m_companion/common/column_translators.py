"""Column translators to make editing tables easier.

Add elements to the CONFIG_COLUMN_TRANSLATORS object to map new translations.
"""
import typing as tp
from dataclasses import dataclass

import pandas as pd


def extract_full_name(row: pd.Series) -> tp.Any:
    """Extract 'Charles' and 'Leclerc' from name columns."""
    first_name: str = row["FirstName"]
    first_name = first_name.strip("[|]").split("_")[-1]
    last_name: str = row["LastName"]
    last_name = last_name.strip("[|]").split("_")[-1]
    row["FullName"] = first_name + " " + last_name
    return row["FullName"]


@dataclass(frozen=True)
class ColumnTranslator:
    """Contains the translation rules.

    Args:
        id_col: Name of column to translate
        foreign_table_name: Name of table to generate translation from
        foreign_id_col: Name of column to join on
        foreign_value_col: name of generated translation column
        func: function to generate translation
    """

    id_col: str
    foreign_table_name: str
    foreign_id_col: str
    foreign_value_col: str
    func: tp.Callable[[pd.Series], tp.Any] | None

    @property
    def tmp_col(self) -> str:
        return f"TMP_{self.id_col}_{self.foreign_value_col}"


CONFIG_COLUMN_TRANSLATORS = [
    ColumnTranslator(
        "StaffID", "Staff_BasicData", "StaffID", "FullName", extract_full_name
    ),
    ColumnTranslator(
        "StatID", "Staff_Enum_PerformanceStatTypes", "Value", "Name", None
    ),
]
column_translators = {x.id_col: x for x in CONFIG_COLUMN_TRANSLATORS}
