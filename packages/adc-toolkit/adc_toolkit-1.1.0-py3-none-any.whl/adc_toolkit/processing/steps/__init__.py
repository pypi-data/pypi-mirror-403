"""
Prebuilt transformation functions for data processing pipelines.

This module provides a library of ready-to-use transformation functions
designed to work seamlessly with :class:`~adc_toolkit.processing.ProcessingPipeline`.
These functions handle common data processing tasks such as cleaning, filtering,
transforming, and combining data.

Available Submodules
--------------------
pandas
    Transformation functions for pandas DataFrames. Includes functions for
    removing duplicates, filling missing values, scaling data, encoding
    categorical variables, and more.

All step functions follow the standard contract: they accept a ``Data`` object
(e.g., pandas DataFrame) as the first positional argument and return a ``Data``
object. Additional parameters are passed as keyword arguments.

Examples
--------
**Using prebuilt steps with a pipeline:**

>>> from adc_toolkit.processing import ProcessingPipeline
>>> from adc_toolkit.processing.steps.pandas import (
...     remove_duplicates,
...     fill_missing_values,
...     scale_data,
... )
>>>
>>> pipeline = (
...     ProcessingPipeline()
...     .add(remove_duplicates, subset=["id"])
...     .add(fill_missing_values, method="mean", columns=["value"])
...     .add(scale_data, columns=["value"], method="minmax")
... )
>>> result = pipeline.run(raw_data)

**Importing functions directly:**

>>> from adc_toolkit.processing.steps.pandas import remove_duplicates
>>> clean_df = remove_duplicates(df, subset=["customer_id"])

**Using the convenience re-exports:**

>>> from adc_toolkit.processing import steps
>>> clean_df = steps.remove_duplicates(df, subset=["id"])

See Also
--------
adc_toolkit.processing.ProcessingPipeline : Pipeline for chaining steps.
adc_toolkit.processing.steps.pandas : Pandas-specific step functions.

Notes
-----
The steps module is designed for extensibility. Future versions may include
additional submodules for other data types (e.g., PySpark DataFrames, Polars).

Each step function is a standalone, pure function that can be used independently
of the pipeline framework. This makes them easy to test, compose, and reuse.
"""

# Re-export commonly used functions for convenience
from .pandas import (
    divide_one_column_by_another,
    encode_categorical,
    fill_missing_values,
    filter_rows,
    group_and_aggregate,
    make_columns_snake_case,
    remove_duplicates,
    scale_data,
    select_columns,
    validate_is_dataframe,
)


__all__ = [
    "divide_one_column_by_another",
    "encode_categorical",
    "fill_missing_values",
    "filter_rows",
    "group_and_aggregate",
    "make_columns_snake_case",
    "pandas",
    "remove_duplicates",
    "scale_data",
    "select_columns",
    "validate_is_dataframe",
]
