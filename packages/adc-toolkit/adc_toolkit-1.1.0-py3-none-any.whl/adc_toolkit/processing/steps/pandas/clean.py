"""Predefined library of cleaning steps for data processing."""

import re
from enum import Enum
from typing import Any, Literal

import pandas as pd


def remove_duplicates(
    data: pd.DataFrame,
    subset: list[str] | None = None,
    keep: Literal["first", "last", False] = "first",
) -> pd.DataFrame:
    """
    Remove duplicate rows from the DataFrame.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame.
    subset : Optional[List[str]]
        Columns to consider for identifying duplicates. By default, considers all columns.
    keep : str
        Which duplicates to keep ('first', 'last', or False for dropping all).

    Returns
    -------
    pd.DataFrame
        DataFrame without duplicate rows.
    """
    return data.drop_duplicates(subset=subset, keep=keep)


class FillMethod(Enum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    CONSTANT = "constant"
    INTERPOLATE = "interpolate"


def fill_missing_values(
    data: pd.DataFrame,
    method: str = FillMethod.MEAN.value,
    value: Any = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Fill or interpolate missing values in the DataFrame.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame.
    method : str
        The method to fill missing values ("mean", "median", "mode", "constant" or "interpolate").
    value : Any
        Specific value to use for filling if `method="constant"`.
    columns : Optional[List[str]]
        List of columns to apply the filling method to. If None, applies to all columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with missing values filled.
    """
    try:
        fill_method = FillMethod(method)
    except ValueError as e:
        raise ValueError(f"Invalid method: {method}") from e

    if columns is None:
        columns = list(data.columns)

    missing_columns = [col for col in columns if col not in data.columns]
    if missing_columns:
        raise ValueError(
            f"The following columns are not in the DataFrame: {missing_columns}. Available columns: {data.columns}"
        )

    data = data.copy()
    if fill_method == FillMethod.MEAN:
        data[columns] = data[columns].fillna(data[columns].mean())
    elif fill_method == FillMethod.MEDIAN:
        data[columns] = data[columns].fillna(data[columns].median())
    elif fill_method == FillMethod.MODE:
        data[columns] = data[columns].apply(lambda col: col.fillna(col.mode().iloc[0]))
    elif fill_method == FillMethod.CONSTANT and value is not None:
        data[columns] = data[columns].fillna(value)
    elif fill_method == FillMethod.INTERPOLATE:
        data[columns] = data[columns].interpolate()

    return data


def _convert_camel_case_to_snake_case(word: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", word).strip().lower()


def make_columns_snake_case(data: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to snake case.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with standardized column names.
    """
    data.columns = [_convert_camel_case_to_snake_case(col) for col in data.columns]
    return data
