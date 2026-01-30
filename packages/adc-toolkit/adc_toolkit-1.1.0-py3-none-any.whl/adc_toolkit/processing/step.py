"""
Pipeline step wrapper for transformation functions.

This module provides the :class:`PipelineStep` class, which wraps individual
transformation functions along with their keyword arguments. It serves as the
building block for :class:`~adc_toolkit.processing.ProcessingPipeline`,
encapsulating both the function to execute and the parameters to pass.

The Function Contract
---------------------
``PipelineStep`` is designed to work with any callable that follows this
contract:

1. **First parameter**: Must accept a ``Data`` object (e.g., pandas DataFrame,
   PySpark DataFrame) as the first positional argument.

2. **Return type**: Must return a ``Data`` object of the same or compatible
   type.

3. **Additional parameters**: Any other parameters should be keyword arguments
   that will be stored in the step and passed during execution.

The signature pattern:

    def my_transformation(
        data: Data,
        param1: type1,
        param2: type2 = default,
        ...
    ) -> Data:
        # Transform data
        return transformed_data

Compatible Data Types
---------------------
The ``Data`` protocol (from :mod:`adc_toolkit.data.abs`) requires only two
properties: ``columns`` and ``dtypes``. This makes the framework compatible
with many data structures out of the box:

- **pandas DataFrame**: Has both ``columns`` and ``dtypes`` attributes
- **PySpark DataFrame**: Has both ``columns`` and ``dtypes`` attributes
- **Custom classes**: Any class implementing these properties

Examples
--------
Creating and executing a step manually (typically handled by
:class:`~adc_toolkit.processing.ProcessingPipeline`):

>>> from adc_toolkit.processing.step import PipelineStep
>>> import pandas as pd
>>>
>>> def add_constant(data: pd.DataFrame, column: str, value: float) -> pd.DataFrame:
...     result = data.copy()
...     result[column] = result[column] + value
...     return result
>>> step = PipelineStep(add_constant, column="price", value=10.0)
>>> df = pd.DataFrame({"price": [100, 200, 300]})
>>> result = step.execute(df)
>>> result["price"].tolist()
[110.0, 210.0, 310.0]

See Also
--------
ProcessingPipeline : Orchestrates multiple steps into a pipeline.
adc_toolkit.data.abs.Data : Protocol defining compatible data objects.
adc_toolkit.processing.steps : Library of prebuilt step functions.
"""

from collections.abc import Callable
from typing import Any

from ..data.abs import Data


class PipelineStep:
    """
    A wrapper for transformation functions in a data processing pipeline.

    ``PipelineStep`` encapsulates a transformation function along with its
    keyword arguments, creating a reusable, inspectable unit of data
    transformation. It handles the invocation of the wrapped function with
    the stored arguments during pipeline execution.

    This class is typically not instantiated directly by users. Instead,
    steps are created implicitly when calling
    :meth:`ProcessingPipeline.add() <adc_toolkit.processing.ProcessingPipeline.add>`.
    However, understanding ``PipelineStep`` is useful for debugging and
    creating custom pipeline behaviors.

    Parameters
    ----------
    step : Callable[..., Data]
        The transformation function to wrap. Must accept a ``Data`` object
        as its first positional argument and return a ``Data`` object.
    **kwargs : Any
        Keyword arguments to pass to the function during execution. These
        are stored and applied every time :meth:`execute` is called.

    Attributes
    ----------
    step : Callable[..., Data]
        The wrapped transformation function.
    kwargs : dict[str, Any]
        Dictionary of keyword arguments to pass to the function.

    See Also
    --------
    ProcessingPipeline : Uses ``PipelineStep`` to orchestrate transformations.
    adc_toolkit.processing.steps.pandas : Prebuilt step functions for pandas.

    Notes
    -----
    **The Step Function Contract**

    Any function can be wrapped in a ``PipelineStep`` if it follows this
    pattern:

        def transformation(data: Data, **kwargs) -> Data:
            # Perform transformation
            return transformed_data

    Where:

    - ``Data`` is any object satisfying the ``Data`` protocol (has ``columns``
      and ``dtypes`` properties)
    - ``**kwargs`` represents any additional parameters your function needs
    - The return value must also satisfy the ``Data`` protocol

    **Flexibility**

    This design enables wrapping:

    - **Prebuilt functions** from :mod:`adc_toolkit.processing.steps`
    - **pandas built-in methods** wrapped as functions
    - **PySpark transformations** wrapped as functions
    - **Custom domain-specific** transformation logic

    **Debugging**

    The :meth:`__str__` method provides a human-readable representation
    showing the function name and its bound arguments, useful for
    debugging and logging pipeline structure.

    Examples
    --------
    **Creating a step with a custom function:**

    >>> import pandas as pd
    >>> from adc_toolkit.processing.step import PipelineStep
    >>>
    >>> def normalize(data: pd.DataFrame, column: str) -> pd.DataFrame:
    ...     result = data.copy()
    ...     col_data = result[column]
    ...     result[column] = (col_data - col_data.min()) / (col_data.max() - col_data.min())
    ...     return result
    >>> step = PipelineStep(normalize, column="temperature")
    >>> print(step)
    normalize(column=temperature)

    **Creating a step with a prebuilt function:**

    >>> from adc_toolkit.processing.steps.pandas import fill_missing_values
    >>>
    >>> step = PipelineStep(fill_missing_values, method="mean", columns=["value"])
    >>> print(step)
    fill_missing_values(method=mean, columns=['value'])

    **Executing a step:**

    >>> df = pd.DataFrame({"temperature": [0, 50, 100]})
    >>> step = PipelineStep(normalize, column="temperature")
    >>> result = step.execute(df)
    >>> result["temperature"].tolist()
    [0.0, 0.5, 1.0]

    **Wrapping a pandas operation:**

    >>> def drop_na(data: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    ...     return data.dropna(subset=subset)
    >>> step = PipelineStep(drop_na, subset=["critical_column"])
    >>> step.execute(df_with_nulls)
    """

    def __init__(
        self,
        step: Callable[..., Data],
        **kwargs: Any,
    ) -> None:
        """
        Initialize a pipeline step with a function and its arguments.

        Creates a new step by storing the transformation function and any
        keyword arguments that should be passed to it during execution.

        Parameters
        ----------
        step : Callable[..., Data]
            The transformation function to wrap. This function must:

            - Accept a ``Data`` object as its first positional argument
            - Return a ``Data`` object
            - Accept any additional parameters as keyword arguments

            The function can be a prebuilt step, a pandas/PySpark method
            wrapped as a function, or a custom transformation.

        **kwargs : Any
            Keyword arguments to pass to the step function when
            :meth:`execute` is called. These should match the function's
            parameter names (excluding the first ``data`` parameter).

        See Also
        --------
        execute : Run the step on data.

        Notes
        -----
        The keyword arguments are stored as-is in the ``kwargs`` attribute.
        They are not validated at initialization time; validation happens
        when the function is called during :meth:`execute`. This allows
        for flexible argument passing but means errors in argument names
        or types will only surface at execution time.

        Examples
        --------
        **Basic initialization:**

        >>> def add_suffix(data, column: str, suffix: str) -> pd.DataFrame:
        ...     result = data.copy()
        ...     result[column] = result[column].astype(str) + suffix
        ...     return result
        >>> step = PipelineStep(add_suffix, column="name", suffix="_processed")
        >>> step.kwargs
        {'column': 'name', 'suffix': '_processed'}

        **With no additional arguments:**

        >>> def identity(data):
        ...     return data.copy()
        >>> step = PipelineStep(identity)
        >>> step.kwargs
        {}
        """
        self.step = step
        self.kwargs = kwargs

    def __str__(self) -> str:
        """
        Return a human-readable string representation of the step.

        The string includes the function name and a comma-separated list
        of the keyword arguments in ``key=value`` format. This is useful
        for debugging, logging, and understanding pipeline structure.

        Returns
        -------
        str
            A string in the format ``"function_name(arg1=val1, arg2=val2)"``.
            If there are no keyword arguments, returns ``"function_name()"``.

        Examples
        --------
        **Step with arguments:**

        >>> from adc_toolkit.processing.steps.pandas import fill_missing_values
        >>> step = PipelineStep(fill_missing_values, method="mean", columns=["a", "b"])
        >>> str(step)
        "fill_missing_values(method=mean, columns=['a', 'b'])"

        **Step without arguments:**

        >>> def simple_transform(data):
        ...     return data
        >>> step = PipelineStep(simple_transform)
        >>> str(step)
        'simple_transform()'

        **Used in pipeline string representation:**

        >>> from adc_toolkit.processing import ProcessingPipeline
        >>> from adc_toolkit.processing.steps.pandas import remove_duplicates
        >>> pipeline = ProcessingPipeline()
        >>> pipeline.add(remove_duplicates, subset=["id"])
        >>> print(pipeline)  # Uses PipelineStep.__str__ internally
        remove_duplicates(subset=['id'])
        """
        kwargs_strings = [f"{key}={value}" for key, value in self.kwargs.items()]
        return f"{self.step.__name__}({', '.join(kwargs_strings)})"

    def execute(self, data: Data) -> Data:
        """
        Execute the wrapped transformation function on the provided data.

        Calls the stored function with the input data as the first argument
        and the stored keyword arguments. Returns the transformed data.

        Parameters
        ----------
        data : Data
            The input data to transform. Must be a ``Data`` protocol-compatible
            object (e.g., pandas DataFrame, PySpark DataFrame). The object
            should be compatible with the wrapped function's expectations.

        Returns
        -------
        Data
            The transformed data returned by the wrapped function. The exact
            type depends on what the wrapped function returns, but it should
            satisfy the ``Data`` protocol.

        Raises
        ------
        TypeError
            If the function cannot accept the provided data type, or if
            required keyword arguments are missing.
        ValueError
            If the function raises a ``ValueError`` due to invalid input
            data or argument values (e.g., referencing a column that
            doesn't exist).
        KeyError
            If the function attempts to access non-existent columns or keys.
        Exception
            Any other exception raised by the wrapped function propagates
            unchanged. The exception type and message depend on the specific
            function implementation.

        See Also
        --------
        ProcessingPipeline.run : Executes multiple steps in sequence.

        Notes
        -----
        **Execution Flow**

        The execution is straightforward:

            result = self.step(data, **self.kwargs)

        The wrapped function receives the data as its first positional
        argument and all stored keyword arguments are unpacked and passed.

        **No Validation**

        This method does not validate the input data or the function's
        return value against the ``Data`` protocol. It trusts that:

        1. The input satisfies the wrapped function's requirements
        2. The function returns a valid ``Data`` object

        Validation failures will surface as exceptions from the wrapped
        function.

        **Error Handling**

        Exceptions from the wrapped function propagate directly to the
        caller. When used within a :class:`ProcessingPipeline`, this means
        the pipeline stops on the first error. Consider wrapping sensitive
        operations with try-except in your step functions if you need
        custom error handling.

        Examples
        --------
        **Basic execution:**

        >>> import pandas as pd
        >>> from adc_toolkit.processing.step import PipelineStep
        >>>
        >>> def double_values(data: pd.DataFrame, column: str) -> pd.DataFrame:
        ...     result = data.copy()
        ...     result[column] = result[column] * 2
        ...     return result
        >>> step = PipelineStep(double_values, column="amount")
        >>> df = pd.DataFrame({"amount": [10, 20, 30]})
        >>> result = step.execute(df)
        >>> result["amount"].tolist()
        [20, 40, 60]

        **Handling errors:**

        >>> def strict_transform(data: pd.DataFrame, required_col: str) -> pd.DataFrame:
        ...     if required_col not in data.columns:
        ...         raise ValueError(f"Column '{required_col}' not found")
        ...     return data
        >>> step = PipelineStep(strict_transform, required_col="missing_column")
        >>> try:
        ...     step.execute(df)
        ... except ValueError as e:
        ...     print(f"Step failed: {e}")
        Step failed: Column 'missing_column' not found
        """
        result = self.step(data, **self.kwargs)

        return result
