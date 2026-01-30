"""
Data processing pipeline framework for composable, chainable transformations.

This module provides a flexible pipeline framework for processing data through
a sequence of transformation steps. The framework is designed to be agnostic
to the underlying data type, working with any object that satisfies the
:class:`~adc_toolkit.data.abs.Data` protocol (e.g., pandas DataFrames,
PySpark DataFrames).

Key Components
--------------
ProcessingPipeline
    Orchestrates the execution of multiple processing steps in sequence.
    Supports method chaining for fluent pipeline construction.
PipelineStep
    Wraps individual transformation functions with their parameters.
    Handles execution and provides debugging information.

The Function Contract
---------------------
The framework's flexibility comes from a simple contract: any function that
accepts a ``Data`` object as its first positional argument and returns a
``Data`` object can be used as a pipeline step. This means you can use:

1. **Prebuilt step functions** from :mod:`adc_toolkit.processing.steps`
2. **pandas/PySpark functions directly** (e.g., ``pd.merge``, ``pd.concat``)
3. **Lambda functions** for simple inline transformations
4. **Custom functions** you write for your specific needs

The function signature should follow this pattern:

    def my_step(data: Data, param1: type1, param2: type2, ...) -> Data:
        # Transform data
        return transformed_data

Where ``Data`` is any object with ``columns`` and ``dtypes`` properties
(pandas DataFrames and PySpark DataFrames satisfy this naturally).

Examples
--------
**Using prebuilt step functions:**

>>> from adc_toolkit.processing import ProcessingPipeline
>>> from adc_toolkit.processing.steps.pandas import remove_duplicates, fill_missing_values
>>>
>>> pipeline = ProcessingPipeline()
>>> pipeline.add(remove_duplicates, subset=["id"])
>>> pipeline.add(fill_missing_values, method="mean", columns=["value"])
>>> result = pipeline.run(raw_data)

**Using pandas functions directly:**

Many pandas functions accept a DataFrame as the first argument and return
a DataFrame, making them directly usable as pipeline steps:

>>> import pandas as pd
>>>
>>> # Merge with another DataFrame
>>> pipeline = ProcessingPipeline()
>>> pipeline.add(pd.merge, right=reference_df, how="left", on="id")
>>> result = pipeline.run(main_df)
>>>
>>> # Concatenate DataFrames
>>> pipeline = ProcessingPipeline()
>>> pipeline.add(pd.concat, objs=[df2, df3], ignore_index=True)
>>> result = pipeline.run(df1)  # df1 is passed as first positional arg

**Using custom transformation functions:**

>>> def normalize_by_group(
...     data: pd.DataFrame,
...     value_col: str,
...     group_col: str,
... ) -> pd.DataFrame:
...     '''Normalize values within each group to [0, 1] range.'''
...     result = data.copy()
...     for group in data[group_col].unique():
...         mask = data[group_col] == group
...         values = data.loc[mask, value_col]
...         min_val, max_val = values.min(), values.max()
...         if max_val > min_val:
...             result.loc[mask, value_col] = (values - min_val) / (max_val - min_val)
...     return result
>>> pipeline = ProcessingPipeline()
>>> pipeline.add(normalize_by_group, value_col="price", group_col="category")
>>> result = pipeline.run(sales_data)

**Using lambda functions for simple transformations:**

>>> pipeline = ProcessingPipeline()
>>> pipeline.add(lambda df: df.dropna())
>>> pipeline.add(lambda df: df.reset_index(drop=True))
>>> result = pipeline.run(messy_data)

**Method chaining for fluent construction:**

>>> pipeline = (
...     ProcessingPipeline()
...     .add(remove_duplicates)
...     .add(fill_missing_values, method="median")
...     .add(lambda df: df.reset_index(drop=True))
... )
>>> result = pipeline.run(data)

See Also
--------
adc_toolkit.processing.pipeline.ProcessingPipeline : The pipeline orchestrator.
adc_toolkit.processing.step.PipelineStep : The step wrapper class.
adc_toolkit.processing.steps : Prebuilt transformation functions.
adc_toolkit.data.abs.Data : The protocol defining compatible data objects.

Notes
-----
The pipeline creates a deep copy of input data before processing, ensuring
the original data remains unmodified. This is important for reproducibility
but may have performance implications for very large datasets.

For production workloads with large data, consider:
- Using PySpark DataFrames which handle distributed processing
- Processing data in chunks if memory is a constraint
- Using in-place operations in custom step functions when appropriate
"""

from . import steps
from .pipeline import ProcessingPipeline
from .step import PipelineStep


__all__ = ["PipelineStep", "ProcessingPipeline", "steps"]
