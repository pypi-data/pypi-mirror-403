"""
Prebuilt transformation functions for pandas DataFrames.

This module provides a comprehensive library of data transformation functions
specifically designed for pandas DataFrames. All functions follow the standard
step contract: they accept a DataFrame as the first positional argument and
return a transformed DataFrame.

These functions are designed to work seamlessly with
:class:`~adc_toolkit.processing.ProcessingPipeline`, but can also be used
as standalone functions for ad-hoc data transformations.

Function Categories
-------------------
**Cleaning** (from ``clean.py``):
    Functions for data quality and standardization.

    - :func:`remove_duplicates`: Remove duplicate rows based on subset of columns
    - :func:`fill_missing_values`: Fill NaN values using various strategies
      (mean, median, mode, constant, interpolate)
    - :func:`make_columns_snake_case`: Standardize column names to snake_case

**Filtering** (from ``filter.py``):
    Functions for row and column selection.

    - :func:`filter_rows`: Filter rows using a callable condition
    - :func:`select_columns`: Select specific columns by name

**Transforming** (from ``transform.py``):
    Functions for data transformation and feature engineering.

    - :func:`scale_data`: Scale numerical columns (minmax or zscore)
    - :func:`encode_categorical`: Encode categorical columns (onehot or label)
    - :func:`divide_one_column_by_another`: Create ratio columns

**Combining** (from ``combine.py``):
    Functions for aggregation and grouping.

    - :func:`group_and_aggregate`: Group by columns and apply aggregation functions

**Validating** (from ``validate.py``):
    Functions for data validation.

    - :func:`validate_is_dataframe`: Assert input is a pandas DataFrame

Examples
--------
**Using with ProcessingPipeline:**

>>> from adc_toolkit.processing import ProcessingPipeline
>>> from adc_toolkit.processing.steps.pandas import (
...     remove_duplicates,
...     fill_missing_values,
...     make_columns_snake_case,
...     scale_data,
... )
>>>
>>> pipeline = (
...     ProcessingPipeline()
...     .add(remove_duplicates, subset=["CustomerID"])
...     .add(fill_missing_values, method="mean", columns=["Revenue"])
...     .add(make_columns_snake_case)
...     .add(scale_data, columns=["revenue"], method="minmax")
... )
>>> clean_data = pipeline.run(raw_data)

**Using functions standalone:**

>>> import pandas as pd
>>> from adc_toolkit.processing.steps.pandas import fill_missing_values
>>>
>>> df = pd.DataFrame({"A": [1, None, 3], "B": [4, 5, None]})
>>> filled = fill_missing_values(df, method="mean")
>>> filled
     A    B
0  1.0  4.0
1  2.0  5.0
2  3.0  4.5

**Filtering with a condition:**

>>> from adc_toolkit.processing.steps.pandas import filter_rows
>>>
>>> df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]})
>>> adults = filter_rows(df, condition=lambda d: d["age"] >= 30)
>>> adults
      name  age
1      Bob   30
2  Charlie   35

**Scaling numerical features:**

>>> from adc_toolkit.processing.steps.pandas import scale_data
>>>
>>> df = pd.DataFrame({"price": [100, 200, 300]})
>>> scaled = scale_data(df, columns=["price"], method="minmax")
>>> scaled["price"].tolist()
[0.0, 0.5, 1.0]

See Also
--------
adc_toolkit.processing.ProcessingPipeline : Pipeline for chaining transformations.
adc_toolkit.processing.steps : Parent module with convenience re-exports.

Notes
-----
**The Step Contract**

All functions in this module follow this signature pattern::

    def step_function(data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        # Transform data
        return transformed_data

This makes them compatible with :meth:`ProcessingPipeline.add()
<adc_toolkit.processing.ProcessingPipeline.add>`.

**Immutability**

Most functions return a new DataFrame rather than modifying the input in place.
This ensures predictable behavior when used in pipelines. Check individual
function documentation for specific behavior.

**Optional Dependencies**

Some functions (like ``scale_data`` and ``encode_categorical``) require
scikit-learn when using certain methods. Install the ``preprocessing`` extra
to enable these features::

    uv sync --extra preprocessing
"""

from .clean import fill_missing_values, make_columns_snake_case, remove_duplicates
from .combine import group_and_aggregate
from .filter import filter_rows, select_columns
from .transform import divide_one_column_by_another, encode_categorical, scale_data
from .validate import validate_is_dataframe


__all__ = [
    "divide_one_column_by_another",
    "encode_categorical",
    "fill_missing_values",
    "filter_rows",
    "group_and_aggregate",
    "make_columns_snake_case",
    "remove_duplicates",
    "scale_data",
    "select_columns",
    "validate_is_dataframe",
]
