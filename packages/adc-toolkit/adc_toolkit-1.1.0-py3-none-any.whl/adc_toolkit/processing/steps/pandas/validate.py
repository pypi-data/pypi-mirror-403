import pandas as pd


def validate_is_dataframe(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Validates if the input is a pandas DataFrame.

    Args:
        data (pd.DataFrame): The input data to validate.

    Returns:
        pd.DataFrame: The validated DataFrame if the input is valid.

    Raises:
        ValueError: If the input is not a pandas DataFrame.
    """
    if not isinstance(data, pd.DataFrame):
        raise ValueError("Input data is not a pandas DataFrame.")

    return data
