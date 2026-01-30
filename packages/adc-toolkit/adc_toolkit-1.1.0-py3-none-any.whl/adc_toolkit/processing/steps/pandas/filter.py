"""Predefined library of filtering steps for data processing."""

from collections.abc import Callable

import pandas as pd


def filter_rows(data: pd.DataFrame, condition: Callable[[pd.DataFrame], pd.Series]) -> pd.DataFrame:
    """
    Filter rows based on a condition.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame.
    condition : Callable[[pd.DataFrame], pd.Series]
        A function that returns a boolean Series indicating rows to keep.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.

    Example
    --------
    >>> data = pd.DataFrame({"A": [1, 2, 3, 4], "B": ["a", "b", "c", "d"]})
    >>> condition = lambda df: df["A"] > 2
    >>> filter_rows(data, condition)
       A  B
    2  3  c
    3  4  d
    """
    return data[condition(data)]


def select_columns(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Retain only specified columns in the DataFrame.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame.
    columns : List[str]
        Columns to retain.

    Returns
    -------
    pd.DataFrame
        DataFrame with only the selected columns.
    """
    return data[columns]
