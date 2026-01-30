"""
Custom exceptions for Pandera validation.

This module provides enhanced exception classes that wrap Pandera's native
validation errors with additional context to facilitate debugging and error
handling in data validation pipelines.

Classes
-------
PanderaValidationError
    Exception raised when Pandera schema validation fails, enriched with
    table name and schema file path information.

See Also
--------
pandera.errors.SchemaError : Base Pandera exception for single schema failures.
pandera.errors.SchemaErrors : Pandera exception for multiple schema failures.

Examples
--------
Basic usage in a validation workflow:

>>> from pathlib import Path
>>> import pandera as pa
>>> from pandera.errors import SchemaError
>>> try:
...     # Validation logic here
...     pass
... except SchemaError as e:
...     raise PanderaValidationError(table_name="users", schema_path=Path("schemas/users_schema.py"), original_error=e)
"""

from pathlib import Path

from pandera.errors import SchemaError, SchemaErrors


class PanderaValidationError(Exception):
    """
    Exception raised when Pandera schema validation fails.

    This exception wraps the original Pandera validation errors
    (``SchemaError`` or ``SchemaErrors``) and enriches them with contextual
    information including the table name and schema file path. This additional
    context significantly simplifies debugging validation failures in data
    pipelines where multiple datasets and schemas are involved.

    The exception message automatically formats the table name, schema path,
    and original error details into a human-readable diagnostic message.

    Parameters
    ----------
    table_name : str
        Name of the table or dataset that failed validation. This identifier
        should match the key used in the data catalog or validation registry.
    schema_path : Path
        Absolute or relative path to the Pandera schema file that was used
        for validation. This helps developers quickly locate the schema
        definition when debugging validation failures.
    original_error : SchemaError or SchemaErrors
        The original Pandera exception that was raised during validation.
        This can be either a single schema error (``SchemaError``) or a
        collection of multiple errors (``SchemaErrors``). The original error
        contains detailed information about which validation checks failed.

    Attributes
    ----------
    table_name : str
        Name of the table that failed validation. Accessible for programmatic
        error handling and logging.
    schema_path : Path
        Path to the schema file used for validation. Useful for error reporting
        and debugging workflows.
    original_error : SchemaError or SchemaErrors
        The wrapped Pandera exception. Can be inspected to extract detailed
        validation failure information such as failing columns, rows, or
        specific constraint violations.

    See Also
    --------
    pandera.errors.SchemaError : Single schema validation failure.
    pandera.errors.SchemaErrors : Multiple schema validation failures.
    adc_toolkit.data.validators.pandera.validator.PanderaValidator : Main validator class that raises this exception.

    Notes
    -----
    This exception is designed to be raised by the ``PanderaValidator`` class
    when validation fails during data loading or saving operations. The
    enhanced error message format follows this structure:

    .. code-block:: text

        Validation failed for table '{table_name}'
        Schema file: {schema_path}
        Error details:
        {original_error}

    The original Pandera error typically includes:

    - Column names that failed validation
    - Specific constraint violations (dtype, nullable, value ranges, etc.)
    - Row indices where failures occurred (for SchemaErrors)
    - Failure cases with actual vs expected values

    Examples
    --------
    Catching and handling validation errors with custom logic:

    >>> import pandas as pd
    >>> from pathlib import Path
    >>> from pandera.errors import SchemaError
    >>> from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
    >>>
    >>> def validate_dataframe(df, table_name, schema_path):
    ...     try:
    ...         # Simulate validation logic
    ...         # schema.validate(df)
    ...         pass
    ...     except SchemaError as e:
    ...         raise PanderaValidationError(table_name=table_name, schema_path=schema_path, original_error=e)

    Extracting contextual information from the exception:

    >>> try:
    ...     validate_dataframe(df, "customers", Path("schemas/customer_schema.py"))
    ... except PanderaValidationError as e:
    ...     print(f"Table: {e.table_name}")
    ...     print(f"Schema: {e.schema_path}")
    ...     print(f"Original error type: {type(e.original_error).__name__}")
    ...     # Log or handle the error appropriately

    Using the exception in a data validation pipeline:

    >>> from adc_toolkit.data.validators.pandera import PanderaValidator
    >>> validator = PanderaValidator.in_directory("config/pandera_schemas")
    >>> try:
    ...     validated_df = validator.validate(data=df, table_name="transactions")
    ... except PanderaValidationError as e:
    ...     # Send alert with table name and schema path
    ...     alert_system.notify(message=str(e), table=e.table_name, schema=e.schema_path)
    ...     # Re-raise or handle gracefully
    ...     raise
    """

    def __init__(
        self,
        table_name: str,
        schema_path: Path,
        original_error: SchemaError | SchemaErrors,
    ) -> None:
        """
        Initialize the PanderaValidationError with context and original error.

        Creates an enriched validation error that combines table identification,
        schema location, and the underlying Pandera validation failure details
        into a comprehensive error message.

        Parameters
        ----------
        table_name : str
            Name of the table or dataset that failed validation. Should be a
            non-empty string that identifies the dataset in your data catalog
            or validation registry.
        schema_path : Path
            Path to the Pandera schema file used for validation. Can be
            absolute or relative. The path is stored as-is and included in
            the error message to facilitate schema location during debugging.
        original_error : SchemaError or SchemaErrors
            The original Pandera exception raised during validation. This
            exception contains detailed information about validation failures:

            - For ``SchemaError``: Single validation failure with error message
            - For ``SchemaErrors``: Multiple failures with failure cases,
              including row indices, column names, and specific violations

        Notes
        -----
        The constructor performs the following operations:

        1. Stores all three parameters as instance attributes for programmatic access
        2. Constructs a formatted error message combining table name, schema path,
           and original error details
        3. Calls the parent ``Exception`` constructor with the formatted message

        The formatted message structure is:

        .. code-block:: text

            Validation failed for table '{table_name}'
            Schema file: {schema_path}
            Error details:
            {original_error}

        Examples
        --------
        Direct instantiation with a SchemaError:

        >>> from pathlib import Path
        >>> from pandera.errors import SchemaError
        >>> from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
        >>>
        >>> schema_error = SchemaError("Column 'age' failed validation")
        >>> exc = PanderaValidationError(
        ...     table_name="users", schema_path=Path("schemas/users.py"), original_error=schema_error
        ... )
        >>> print(exc.table_name)
        users
        >>> print(exc.schema_path)
        schemas/users.py

        Instantiation with SchemaErrors (multiple failures):

        >>> from pandera.errors import SchemaErrors
        >>> schema_errors = SchemaErrors(
        ...     schema_errors=[
        ...         SchemaError("Column 'email' failed regex validation"),
        ...         SchemaError("Column 'age' has null values"),
        ...     ]
        ... )
        >>> exc = PanderaValidationError(
        ...     table_name="customers",
        ...     schema_path=Path("/absolute/path/to/customer_schema.py"),
        ...     original_error=schema_errors,
        ... )
        """
        self.table_name = table_name
        self.schema_path = schema_path
        self.original_error = original_error

        message = (
            f"Validation failed for table '{table_name}'\nSchema file: {schema_path}\nError details:\n{original_error}"
        )
        super().__init__(message)
