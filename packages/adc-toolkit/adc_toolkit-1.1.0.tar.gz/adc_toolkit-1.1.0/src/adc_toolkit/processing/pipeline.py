"""
Processing pipeline for orchestrating sequential data transformations.

This module provides the :class:`ProcessingPipeline` class, which enables
composing multiple data transformation steps into a single, reusable pipeline.
The pipeline pattern simplifies complex data processing workflows by breaking
them into discrete, testable steps.

The pipeline is designed to work with any callable that follows the step
contract: accept a ``Data`` object as the first argument and return a ``Data``
object. This flexibility allows mixing prebuilt steps, pandas/PySpark methods,
and custom functions in the same pipeline.

Examples
--------
Create and run a simple pipeline:

>>> from adc_toolkit.processing import ProcessingPipeline
>>> from adc_toolkit.processing.steps.pandas import remove_duplicates
>>>
>>> pipeline = ProcessingPipeline()
>>> pipeline.add(remove_duplicates, subset=["customer_id"])
>>> clean_data = pipeline.run(raw_data)

See Also
--------
PipelineStep : Wrapper for individual transformation functions.
adc_toolkit.processing.steps : Library of prebuilt step functions.
"""

import copy
from collections.abc import Callable
from typing import Any

from ..data.abs import Data
from .step import PipelineStep


class ProcessingPipeline:
    """
    A pipeline for processing data through a sequence of transformation steps.

    ``ProcessingPipeline`` orchestrates the execution of multiple processing
    steps in a defined order. Each step transforms the data and passes the
    result to the next step. The pipeline supports method chaining for fluent
    construction and preserves the original input data through deep copying.

    The pipeline is agnostic to the specific transformation functions used.
    Any callable that accepts a ``Data`` object (e.g., pandas DataFrame) as
    its first argument and returns a ``Data`` object can be added as a step.
    This enables mixing:

    - Prebuilt steps from :mod:`adc_toolkit.processing.steps`
    - Built-in pandas or PySpark transformation methods
    - Custom functions tailored to your specific needs

    Attributes
    ----------
    steps : list[PipelineStep]
        The ordered list of pipeline steps to execute. Each step is a
        :class:`PipelineStep` instance wrapping a transformation function
        and its keyword arguments.

    See Also
    --------
    PipelineStep : The wrapper class for individual transformation functions.
    adc_toolkit.processing.steps.pandas : Prebuilt pandas transformation steps.
    adc_toolkit.data.abs.Data : Protocol defining compatible data objects.

    Notes
    -----
    **Immutability**: The :meth:`run` method creates a deep copy of the input
    data before processing. This ensures the original data is never modified,
    which is important for reproducibility and debugging. However, deep copying
    can be expensive for very large datasets.

    **Sequential Execution**: Steps execute in the order they were added.
    The output of each step becomes the input to the next step. There is no
    parallel execution or branching.

    **Error Propagation**: If any step raises an exception, the pipeline
    stops immediately and the exception propagates to the caller. Partial
    results are not returned.

    Examples
    --------
    **Basic usage with prebuilt steps:**

    >>> from adc_toolkit.processing import ProcessingPipeline
    >>> from adc_toolkit.processing.steps.pandas import (
    ...     remove_duplicates,
    ...     fill_missing_values,
    ...     make_columns_snake_case,
    ... )
    >>> import pandas as pd
    >>>
    >>> # Create sample data
    >>> df = pd.DataFrame(
    ...     {
    ...         "CustomerID": [1, 1, 2, 3],
    ...         "Value": [10.0, 10.0, None, 30.0],
    ...     }
    ... )
    >>>
    >>> # Build and run pipeline
    >>> pipeline = ProcessingPipeline()
    >>> pipeline.add(remove_duplicates, subset=["CustomerID"])
    >>> pipeline.add(fill_missing_values, method="mean", columns=["Value"])
    >>> pipeline.add(make_columns_snake_case)
    >>> result = pipeline.run(df)
    >>> result.columns.tolist()
    ['customer_id', 'value']

    **Method chaining for fluent construction:**

    >>> pipeline = ProcessingPipeline().add(remove_duplicates, subset=["id"]).add(fill_missing_values, method="median")
    >>> len(pipeline)
    2

    **Using custom transformation functions:**

    >>> def log_transform(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    ...     '''Apply log transformation to specified columns.'''
    ...     import numpy as np
    ...
    ...     result = data.copy()
    ...     for col in columns:
    ...         result[col] = np.log1p(result[col])
    ...     return result
    >>> pipeline = ProcessingPipeline()
    >>> pipeline.add(log_transform, columns=["price", "quantity"])
    >>> transformed = pipeline.run(sales_data)

    **Using pandas functions directly:**

    Many pandas functions can be used directly since they accept a DataFrame
    as the first argument and return a DataFrame:

    >>> import pandas as pd
    >>>
    >>> # Merge with a reference table
    >>> pipeline = ProcessingPipeline()
    >>> pipeline.add(pd.merge, right=lookup_df, how="left", on="category_id")
    >>> enriched = pipeline.run(sales_df)
    >>>
    >>> # Query rows using pd.DataFrame.query (via eval)
    >>> pipeline = ProcessingPipeline()
    >>> pipeline.add(pd.eval, expr="amount * quantity", target=df)

    **Inspecting pipeline structure:**

    >>> pipeline = ProcessingPipeline()
    >>> pipeline.add(remove_duplicates, subset=["id"])
    >>> pipeline.add(fill_missing_values, method="mean")
    >>> print(pipeline)
    remove_duplicates(subset=['id']) -> fill_missing_values(method=mean)
    >>> len(pipeline)
    2
    """

    def __init__(self) -> None:
        """
        Initialize an empty processing pipeline.

        Creates a new pipeline with no steps. Steps can be added using the
        :meth:`add` method.

        Examples
        --------
        >>> pipeline = ProcessingPipeline()
        >>> len(pipeline)
        0
        """
        self.steps = list[PipelineStep]()

    def __str__(self) -> str:
        """
        Return a human-readable string representation of the pipeline.

        The string shows each step's function name and parameters, joined
        by arrows to indicate the flow of data through the pipeline.

        Returns
        -------
        str
            A string representation showing all steps in order, formatted as
            ``"step1(params) -> step2(params) -> ..."``. Returns an empty
            string if the pipeline has no steps.

        Examples
        --------
        >>> from adc_toolkit.processing.steps.pandas import (
        ...     remove_duplicates,
        ...     fill_missing_values,
        ... )
        >>> pipeline = ProcessingPipeline()
        >>> pipeline.add(remove_duplicates, subset=["id"])
        >>> pipeline.add(fill_missing_values, method="mean")
        >>> print(pipeline)
        remove_duplicates(subset=['id']) -> fill_missing_values(method=mean)
        """
        return " -> ".join([str(step) for step in self.steps])

    def __len__(self) -> int:
        """
        Return the number of steps in the pipeline.

        Returns
        -------
        int
            The count of transformation steps currently in the pipeline.

        Examples
        --------
        >>> pipeline = ProcessingPipeline()
        >>> len(pipeline)
        0
        >>> pipeline.add(lambda df: df)
        <ProcessingPipeline object>
        >>> len(pipeline)
        1
        """
        return len(self.steps)

    def add(
        self,
        step: Callable[..., Data],
        **kwargs: Any,
    ) -> "ProcessingPipeline":
        """
        Add a transformation step to the pipeline.

        Appends a new step to the end of the pipeline. The step consists of
        a callable (function) and any keyword arguments to pass to it during
        execution. The callable must follow the step contract: accept a
        ``Data`` object as the first positional argument and return a
        ``Data`` object.

        This method returns ``self`` to enable method chaining, allowing
        multiple steps to be added in a fluent style.

        Parameters
        ----------
        step : Callable[..., Data]
            The transformation function to execute. Must accept a ``Data``
            object (e.g., pandas DataFrame, PySpark DataFrame) as its first
            positional argument and return a ``Data`` object. Can be:

            - A prebuilt step from :mod:`adc_toolkit.processing.steps`
            - A pandas/PySpark function directly (e.g., ``pd.merge``)
            - A lambda function for simple inline transformations
            - A custom function you define

        **kwargs : Any
            Keyword arguments to pass to the step function during execution.
            These are stored with the step and applied when :meth:`run` is
            called. The arguments should match the function's signature
            (excluding the first ``data`` parameter).

        Returns
        -------
        ProcessingPipeline
            Returns ``self`` to enable method chaining.

        See Also
        --------
        run : Execute the pipeline on data.
        PipelineStep : The wrapper class for transformation functions.

        Notes
        -----
        **The Step Contract**

        Any function can be used as a step if it follows this signature:

            def my_step(data: Data, param1: T1, param2: T2, ...) -> Data:
                # Transform the data
                return transformed_data

        The ``Data`` protocol requires only ``columns`` and ``dtypes``
        properties. pandas DataFrames and PySpark DataFrames satisfy this
        naturally, so you can use them directly without any wrappers.

        **Keyword Arguments Only**

        Only keyword arguments (not positional) can be passed to the step
        function via the ``**kwargs`` parameter. If your function requires
        positional arguments beyond the ``data`` parameter, consider using
        ``functools.partial`` or a lambda wrapper.

        Examples
        --------
        **Using prebuilt steps:**

        >>> from adc_toolkit.processing.steps.pandas import remove_duplicates
        >>> pipeline = ProcessingPipeline()
        >>> pipeline.add(remove_duplicates, subset=["customer_id"], keep="first")
        <ProcessingPipeline object>

        **Using a custom function:**

        >>> def scale_column(data, column: str, factor: float) -> pd.DataFrame:
        ...     result = data.copy()
        ...     result[column] = result[column] * factor
        ...     return result
        >>> pipeline.add(scale_column, column="price", factor=1.1)
        <ProcessingPipeline object>

        **Method chaining:**

        >>> from adc_toolkit.processing.steps.pandas import (
        ...     remove_duplicates,
        ...     fill_missing_values,
        ...     select_columns,
        ... )
        >>> pipeline = (
        ...     ProcessingPipeline()
        ...     .add(remove_duplicates)
        ...     .add(fill_missing_values, method="mean")
        ...     .add(select_columns, columns=["id", "name", "value"])
        ... )
        >>> len(pipeline)
        3

        **Using pandas functions directly:**

        >>> import pandas as pd
        >>> pipeline = ProcessingPipeline()
        >>> pipeline.add(pd.merge, right=reference_df, how="left", on="id")
        <ProcessingPipeline object>

        **Using a lambda for simple transformations:**

        >>> pipeline = ProcessingPipeline()
        >>> pipeline.add(lambda df: df.reset_index(drop=True))
        <ProcessingPipeline object>
        """
        self.steps.append(PipelineStep(step, **kwargs))

        return self

    def run(self, data: Data) -> Data:
        """
        Execute the pipeline on the provided data.

        Runs all transformation steps in sequence on a deep copy of the
        input data. Each step receives the output of the previous step as
        its input. The original data is never modified.

        Parameters
        ----------
        data : Data
            The input data to process. Must be a ``Data`` protocol-compatible
            object (e.g., pandas DataFrame, PySpark DataFrame). The object
            must support deep copying via ``copy.deepcopy``.

        Returns
        -------
        Data
            The transformed data after all pipeline steps have been applied.
            Returns a new object; the original ``data`` is unchanged.

        Raises
        ------
        TypeError
            If the input data cannot be deep copied.
        Exception
            Any exception raised by a step function propagates directly.
            The exception message indicates which step failed.

        See Also
        --------
        add : Add steps to the pipeline before running.

        Notes
        -----
        **Immutability**

        The pipeline creates a deep copy of the input data before processing.
        This ensures:

        - The original data is preserved for comparison or debugging
        - Multiple runs with the same input produce consistent results
        - Side effects from step functions don't affect the original

        For very large datasets, this copying may have performance
        implications. Consider:

        - Using PySpark for distributed processing of large data
        - Processing data in chunks if memory is constrained
        - Implementing steps that operate in-place if you're certain
          about data ownership

        **Sequential Execution**

        Steps execute strictly in order. The data flow is:

            input -> step1 -> step2 -> ... -> stepN -> output

        There is no parallel execution. If a step fails, subsequent steps
        do not run and the exception propagates immediately.

        **Empty Pipeline**

        Running an empty pipeline (no steps added) returns a deep copy of
        the input data without any transformations.

        Examples
        --------
        **Basic execution:**

        >>> import pandas as pd
        >>> from adc_toolkit.processing import ProcessingPipeline
        >>> from adc_toolkit.processing.steps.pandas import remove_duplicates
        >>>
        >>> df = pd.DataFrame({"id": [1, 1, 2], "value": [10, 10, 20]})
        >>> pipeline = ProcessingPipeline()
        >>> pipeline.add(remove_duplicates, subset=["id"])
        >>> result = pipeline.run(df)
        >>> len(result)
        2
        >>> len(df)  # Original unchanged
        3

        **Running the same pipeline multiple times:**

        >>> result1 = pipeline.run(data_batch_1)
        >>> result2 = pipeline.run(data_batch_2)
        >>> result3 = pipeline.run(data_batch_3)

        **Empty pipeline returns a copy:**

        >>> empty_pipeline = ProcessingPipeline()
        >>> result = empty_pipeline.run(df)
        >>> result is df
        False
        >>> result.equals(df)
        True
        """
        result = copy.deepcopy(data)

        for step in self.steps:
            result = step.execute(result)

        return result
