"""
No-operation validator implementation.

This module provides a pass-through validator that implements the DataValidator
protocol without performing any validation. It is useful for scenarios where
validation is not required, such as during development, testing, or when working
with trusted data sources.

The NoValidator class satisfies the DataValidator protocol interface while
bypassing all validation logic, effectively making it a no-op (no operation)
implementation. This allows it to be used as a drop-in replacement for actual
validators when validation overhead is not desired.

Classes
-------
NoValidator
    A validator that returns data unchanged without performing validation.

See Also
--------
adc_toolkit.data.abs.DataValidator : Protocol that defines the validator interface.
adc_toolkit.data.validators.gx.GXValidator : Great Expectations-based validator.
adc_toolkit.data.validators.pandera.PanderaValidator : Pandera-based validator.

Notes
-----
Using NoValidator is not recommended for production pipelines where data quality
assurance is critical. It should primarily be used in the following scenarios:

- Development and prototyping: Quickly iterate without validation overhead
- Testing: Unit tests where validation is mocked or not relevant
- Trusted data sources: Data from sources with external validation guarantees
- Performance optimization: Temporary bypass when validation is a bottleneck

When NoValidator is instantiated, it emits a UserWarning to alert developers
that validation is disabled. This helps prevent accidental use in production
environments.

Examples
--------
Using NoValidator in a validated data catalog:

>>> from adc_toolkit.data.validators.no_validator import NoValidator
>>> validator = NoValidator()
>>> import pandas as pd
>>> df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
>>> validated_df = validator.validate("my_dataset", df)
>>> validated_df is df  # Returns the same object unchanged
True

Using with the factory method:

>>> validator = NoValidator.in_directory("/path/to/config")
>>> # Path is ignored, always returns a NoValidator instance

Integration with ValidatedDataCatalog (bypassing validation):

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> from adc_toolkit.data.validators.no_validator import NoValidator
>>> catalog = ValidatedDataCatalog(catalog=my_catalog, validator=NoValidator())
>>> # All loads and saves pass through without validation
"""

import warnings
from pathlib import Path

from adc_toolkit.data.abs import Data


class NoValidator:
    """
    A no-operation validator that passes data through without validation.

    NoValidator implements the DataValidator protocol but performs no actual
    validation. It returns all data unchanged, making it a pass-through or
    no-op validator. This is useful in scenarios where validation is not
    required, such as during development, testing, or when working with
    pre-validated or trusted data sources.

    The validator emits a UserWarning upon instantiation to alert developers
    that validation is disabled, helping prevent accidental use in production
    environments where data quality assurance is critical.

    Attributes
    ----------
    None
        This class maintains no internal state.

    Methods
    -------
    validate(name, data)
        Return data unchanged without performing any validation.
    in_directory(path)
        Create a NoValidator instance, ignoring the provided path.

    See Also
    --------
    adc_toolkit.data.abs.DataValidator : Protocol defining validator interface.
    adc_toolkit.data.validators.gx.GXValidator : Validator using Great Expectations.
    adc_toolkit.data.validators.pandera.PanderaValidator : Validator using Pandera.
    adc_toolkit.data.ValidatedDataCatalog : Catalog that uses validators.

    Notes
    -----
    This validator is intentionally minimal and does not maintain any
    configuration, validation rules, or state. It exists solely to satisfy
    the DataValidator protocol while bypassing validation logic.

    **When to use NoValidator:**

    - **Development and prototyping**: Quickly iterate on data pipelines
      without validation overhead slowing down the development cycle.
    - **Testing**: Unit tests where validation logic is mocked, not relevant,
      or tested separately.
    - **Trusted data sources**: Data from sources with external validation
      guarantees (e.g., validated by another system before ingestion).
    - **Performance optimization**: Temporary bypass when validation becomes
      a computational bottleneck and data quality is assured through other means.
    - **Debugging**: Isolate issues by removing validation from the pipeline.

    **When NOT to use NoValidator:**

    - Production data pipelines where data quality is critical
    - User-facing applications where invalid data could cause errors
    - Scenarios where schema drift or data corruption must be detected
    - Compliance-driven contexts requiring validation audit trails

    **Protocol conformance:**

    NoValidator satisfies the DataValidator protocol by implementing:

    - ``validate(name: str, data: Data) -> Data``: Returns data unchanged
    - ``in_directory(path: str | Path) -> DataValidator``: Factory method

    The class uses structural subtyping (PEP 544) to conform to the protocol
    without explicit inheritance.

    Warnings
    --------
    UserWarning
        Issued on instantiation to warn that validation is disabled.

    Examples
    --------
    Basic instantiation and usage:

    >>> import pandas as pd
    >>> from adc_toolkit.data.validators.no_validator import NoValidator
    >>> validator = NoValidator()
    UserWarning: Not using any validator is not recommended...
    >>> df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    >>> result = validator.validate("dataset_name", df)
    >>> result is df  # Same object returned
    True

    Using the factory method:

    >>> validator = NoValidator.in_directory("/config/path")
    >>> # Path is ignored; still returns NoValidator instance

    Integration with ValidatedDataCatalog:

    >>> from adc_toolkit.data import ValidatedDataCatalog
    >>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
    >>> catalog = KedroDataCatalog.in_directory("config/")
    >>> validator = NoValidator()
    >>> validated_catalog = ValidatedDataCatalog(catalog=catalog, validator=validator)
    >>> # All data passes through without validation

    Testing scenario where validation is not needed:

    >>> def test_data_transformation():
    ...     # Use NoValidator to focus test on transformation logic
    ...     validator = NoValidator()
    ...     input_data = create_test_data()
    ...     validated = validator.validate("test", input_data)
    ...     result = transform(validated)
    ...     assert result.shape == expected_shape
    """

    def __init__(self) -> None:
        """
        Initialize the NoValidator instance.

        Creates a new NoValidator that will pass all data through unchanged.
        Upon instantiation, a UserWarning is emitted to alert developers that
        validation is disabled. This warning helps prevent accidental use in
        production environments where data quality assurance is critical.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Warns
        -----
        UserWarning
            Always emitted on instantiation, warning that no validation will
            be performed and recommending the use of an actual validator from
            the `adc_toolkit.data.validators` module.

        See Also
        --------
        in_directory : Factory method for creating NoValidator instances.
        validate : Method that returns data unchanged.

        Notes
        -----
        The warning is emitted with ``stacklevel=2`` to ensure it points to
        the caller's location rather than this constructor, making it easier
        to identify where the NoValidator is being instantiated.

        This constructor takes no parameters and maintains no internal state,
        making all NoValidator instances functionally equivalent.

        Examples
        --------
        Instantiating the validator triggers a warning:

        >>> from adc_toolkit.data.validators.no_validator import NoValidator
        >>> validator = NoValidator()
        UserWarning: Not using any validator is not recommended. Consider using
        a validator from the `adc_toolkit.data.validators` module.

        The warning can be suppressed if desired (though not recommended):

        >>> import warnings
        >>> with warnings.catch_warnings():
        ...     warnings.simplefilter("ignore", UserWarning)
        ...     validator = NoValidator()
        >>> # No warning emitted

        Multiple instances are functionally identical:

        >>> validator1 = NoValidator()
        >>> validator2 = NoValidator()
        >>> # Both behave identically
        """
        warnings.warn(
            "Not using any validator is not recommended. "
            "Consider using a validator from the `adc_toolkit.data.validators` module.",
            UserWarning,
            stacklevel=2,
        )

    @classmethod
    def in_directory(cls, path: str | Path) -> "NoValidator":  # noqa: ARG003
        """
        Create a NoValidator instance from a directory path.

        This factory method implements the DataValidator protocol's required
        interface for directory-based instantiation. For NoValidator, the path
        parameter is ignored because no configuration is needed. This method
        exists purely to satisfy the protocol requirement.

        The method simply delegates to the constructor, which creates a
        stateless NoValidator instance. The returned validator will pass all
        data through unchanged regardless of the provided path.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to a configuration directory. This parameter is ignored for
            NoValidator since no configuration is required. It exists only to
            maintain interface compatibility with the DataValidator protocol.

        Returns
        -------
        NoValidator
            A new NoValidator instance that will return all data unchanged.

        Warns
        -----
        UserWarning
            Issued during instantiation (via ``__init__``) warning that
            validation is disabled.

        See Also
        --------
        __init__ : Constructor that creates the NoValidator instance.
        validate : Method that returns data unchanged.
        adc_toolkit.data.abs.DataValidator : Protocol defining this interface.

        Notes
        -----
        Unlike actual validator implementations (GXValidator, PanderaValidator),
        NoValidator does not read any configuration files from the provided
        directory. The path parameter is accepted and ignored to maintain
        protocol compatibility.

        This design allows NoValidator to be used as a drop-in replacement for
        other validators without changing the calling code's interface.

        The ``# noqa: ARG003`` comment suppresses linting warnings about the
        unused ``path`` parameter, which is intentionally unused.

        Examples
        --------
        Creating a NoValidator using the factory method:

        >>> from adc_toolkit.data.validators.no_validator import NoValidator
        >>> validator = NoValidator.in_directory("/path/to/config")
        UserWarning: Not using any validator is not recommended...
        >>> # Path is ignored

        The path parameter has no effect on behavior:

        >>> validator1 = NoValidator.in_directory("/some/path")
        >>> validator2 = NoValidator.in_directory("/different/path")
        >>> # Both validators behave identically

        Using with ValidatedDataCatalog's factory method:

        >>> from adc_toolkit.data import ValidatedDataCatalog
        >>> # If config directory contains NoValidator configuration
        >>> catalog = ValidatedDataCatalog.in_directory("config/")
        >>> # Internally calls NoValidator.in_directory()

        Drop-in replacement for other validators:

        >>> # Switch from GXValidator to NoValidator without code changes
        >>> # Before:
        >>> # validator = GXValidator.in_directory("validations/")
        >>> # After (for testing):
        >>> validator = NoValidator.in_directory("validations/")
        >>> # Same interface, no validation performed
        """
        return cls()

    def validate(self, name: str, data: Data) -> Data:  # noqa: ARG002
        """
        Return data unchanged without performing any validation.

        This method implements the DataValidator protocol's validate interface
        as a no-operation (no-op) pass-through. It accepts a dataset and
        immediately returns it without performing any validation checks, schema
        verification, or data quality assessments.

        Unlike actual validator implementations, this method does not check
        column names, data types, value ranges, null constraints, or any other
        validation rules. The returned data is the exact same object passed as
        input, with no modifications or metadata additions.

        Parameters
        ----------
        name : str
            The name identifying the dataset being validated. For NoValidator,
            this parameter is ignored since no validation is performed. It
            exists only to maintain interface compatibility with the
            DataValidator protocol.
        data : Data
            The dataset to validate (or rather, to pass through unchanged).
            Must be a Data protocol-compatible object such as pandas.DataFrame,
            pyspark.sql.DataFrame, or any object with ``columns`` and ``dtypes``
            properties.

        Returns
        -------
        Data
            The exact same data object that was passed as input, with no
            modifications, transformations, or validation metadata attached.
            The returned value is identical (``is`` relationship) to the input.

        Raises
        ------
        None
            This method never raises validation-related exceptions. It is
            guaranteed to return the input data unchanged.

        See Also
        --------
        __init__ : Constructor that creates the NoValidator instance.
        in_directory : Factory method for instantiation.
        adc_toolkit.data.abs.DataValidator.validate : Protocol method definition.

        Notes
        -----
        **No-op behavior:**

        This method is intentionally a no-operation. It does not:

        - Check schema (column names, data types, structure)
        - Validate constraints (null checks, uniqueness, ranges)
        - Verify statistical properties (distributions, outliers)
        - Execute business rules or custom validation logic
        - Log validation results or maintain audit trails
        - Modify or transform the data in any way
        - Attach validation metadata to the returned data

        **Identity preservation:**

        The returned data is the exact same object reference as the input:

        >>> result = validator.validate("name", data)
        >>> result is data  # Always True

        **Parameter usage:**

        The ``name`` parameter is accepted but ignored (hence ``# noqa: ARG002``).
        In actual validators, this parameter identifies which validation suite
        to execute. For NoValidator, it has no effect on behavior.

        **Thread safety:**

        Since this method maintains no state and performs no I/O, it is
        inherently thread-safe. Multiple threads can call validate
        concurrently without synchronization.

        **Performance:**

        This method has O(1) time complexity and negligible overhead, making
        it suitable for performance-critical scenarios where validation is
        bypassed.

        Examples
        --------
        Basic validation (no-op) with pandas DataFrame:

        >>> import pandas as pd
        >>> from adc_toolkit.data.validators.no_validator import NoValidator
        >>> validator = NoValidator()
        >>> df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        >>> result = validator.validate("my_dataset", df)
        >>> result is df
        True
        >>> # Data passes through completely unchanged

        The name parameter has no effect:

        >>> result1 = validator.validate("dataset_1", df)
        >>> result2 = validator.validate("dataset_2", df)
        >>> result1 is df and result2 is df
        True

        No validation means invalid data passes through:

        >>> invalid_df = pd.DataFrame({"x": [None, None, None]})
        >>> # In real validator, this might fail null checks
        >>> result = validator.validate("strict_schema", invalid_df)
        >>> result is invalid_df  # Passes through anyway
        True

        Integration with ValidatedDataCatalog:

        >>> from adc_toolkit.data import ValidatedDataCatalog
        >>> catalog = ValidatedDataCatalog(catalog=my_catalog, validator=NoValidator())
        >>> # Load data without validation
        >>> df = catalog.load("dataset_name")
        >>> # Save data without validation
        >>> catalog.save("output_name", df)

        Using in a data pipeline (bypass validation during development):

        >>> def pipeline(validator: DataValidator) -> None:
        ...     raw = load_raw_data()
        ...     validated_raw = validator.validate("raw", raw)
        ...     processed = transform(validated_raw)
        ...     validated_processed = validator.validate("processed", processed)
        ...     save(validated_processed)
        >>> # Development: use NoValidator to skip validation
        >>> pipeline(NoValidator())
        >>> # Production: use actual validator
        >>> # pipeline(GXValidator.in_directory("validations/"))
        """
        return data
