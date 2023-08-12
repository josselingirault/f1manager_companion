import typing as tp
from dataclasses import dataclass

import pandas as pd

# def extract_name(series: pd.Series) -> pd.Series:
#     """Extract 'Charles' from '[StaffName_Forename_Male_Charles]'."""
#     return series.str.strip("[|]").str.split("_").str[-1]


def extract_full_name(row: pd.Series) -> tp.Any:
    """Extract 'Charles' and 'Leclerc' from name columns."""
    first_name: str = row["FirstName"]
    first_name = first_name.strip("[|]").split("_")[-1]
    last_name: str = row["LastName"]
    last_name = last_name.strip("[|]").split("_")[-1]
    row["FullName"] = first_name + " " + last_name
    return row["FullName"]


@dataclass
class ColumnTranslation:
    id_col: str
    foreign_table_name: str
    foreign_id_col: str
    foreign_value_col: str
    func: tp.Callable[[pd.Series], tp.Any] | None

    def tmp_col(self) -> str:
        return f"TMP_{self.id_col}_{self.foreign_value_col}"


CONFIG_COLUMN_TRANSLATION = [
    ColumnTranslation(
        "StaffID", "Staff_BasicData", "StaffID", "FullName", extract_full_name
    ),
    ColumnTranslation(
        "StatID", "Staff_Enum_PerformanceStatTypes", "Value", "Name", None
    ),
]
translators = {x.id_col: x for x in CONFIG_COLUMN_TRANSLATION}
