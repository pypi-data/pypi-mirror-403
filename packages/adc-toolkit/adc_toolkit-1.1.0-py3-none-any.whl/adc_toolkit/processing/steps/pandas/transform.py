"""Predefined library of transformation steps for data processing."""

from collections.abc import Callable

import pandas as pd


try:
    from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    LabelEncoder = None
    MinMaxScaler = None
    StandardScaler = None


def _check_sklearn_available() -> None:
    """Check if sklearn is available and raise a helpful error if not."""
    if not _SKLEARN_AVAILABLE:
        raise ImportError(
            "scikit-learn is required for this function. " "Install it with: uv sync --extra preprocessing"
        )


def scale_data(
    data: pd.DataFrame,
    columns: list[str],
    method: str | Callable[[pd.DataFrame, list[str]], pd.DataFrame] = "minmax",
) -> pd.DataFrame:
    """
    Scale numerical features using specified scaling method.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame.
    columns : List[str]
        Columns to scale.
    method : Union[str, Callable[[pd.DataFrame, List[str]], pd.DataFrame]]
        Scaling method ('minmax', 'zscore', or custom scaler function).

    Returns
    -------
    pd.DataFrame
        DataFrame with scaled columns.

    Raises
    ------
    ImportError
        If scikit-learn is not installed (required for built-in scalers).
    """
    _check_sklearn_available()
    if isinstance(method, str):
        if method == "minmax":
            scaler = MinMaxScaler()
        elif method == "zscore":
            scaler = StandardScaler()
        else:
            raise ValueError(f"Invalid scaling method: {method}")
    elif callable(method):
        scaler = method
    else:
        raise TypeError("Invalid method type. Method must be a string or a callable function.")

    data[columns] = scaler.fit_transform(data[columns])
    return data


def encode_categorical(data: pd.DataFrame, columns: list[str], method: str = "onehot") -> pd.DataFrame:
    """
    Encode categorical features using the specified encoding method.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame.
    columns : List[str]
        Columns to encode.
    method : str
        Encoding method ('onehot' or 'label').

    Returns
    -------
    pd.DataFrame
        DataFrame with encoded columns.

    Raises
    ------
    ImportError
        If scikit-learn is not installed and method is 'label'.
    """
    if method == "onehot":
        return pd.get_dummies(data, columns=columns)
    elif method == "label":
        _check_sklearn_available()
        encoder = LabelEncoder()
        for col in columns:
            data[col] = encoder.fit_transform(data[col])
        return data
    else:
        raise ValueError(f"Invalid encoding method: {method}")


def divide_one_column_by_another(
    data: pd.DataFrame, numerator: str, denominator: str, new_column_name: str
) -> pd.DataFrame:
    """

    Parameters

    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be transformed.
    numerator : str
        The name of the column to be used as the numerator.
    denominator : str
        The name of the column to be used as the denominator.
    new_column_name : str
        The name of the new column to be created.
    Returns
    -------
    pd.DataFrame
        The transformed DataFrame with the new column added.
    """
    data[new_column_name] = data[numerator] / data[denominator]
    return data
