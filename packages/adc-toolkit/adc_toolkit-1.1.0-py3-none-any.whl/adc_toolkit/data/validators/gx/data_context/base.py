"""
Factory protocol for Great Expectations data context creation.

This module defines the Protocol for creating Great Expectations (GX) data
contexts. A data context in GX manages configuration, expectations, validation
results, and data documentation. This Protocol enables multiple backend
implementations (file system, cloud storage) through the factory pattern.

The BaseDataContext Protocol serves as the contract for all data context
factory implementations in the toolkit, ensuring consistent interfaces
regardless of the underlying storage backend.

Examples
--------
Typical usage with a file system implementation:

>>> from adc_toolkit.data.validators.gx.data_context import RepoDataContext
>>> factory = RepoDataContext(project_config_dir="gx_config/")
>>> context = factory.create()
>>> type(context).__name__
'FileDataContext'

Cloud-based implementation example:

>>> from adc_toolkit.data.validators.gx.data_context import S3DataContext
>>> factory = S3DataContext(bucket_name="my-gx-bucket", prefix="gx/")
>>> context = factory.create()
>>> context.list_datasources()
[...]

See Also
--------
great_expectations.data_context.AbstractDataContext : Base GX context class.
great_expectations.data_context.EphemeralDataContext : In-memory GX context.

Notes
-----
The Protocol pattern allows for dependency injection and testing flexibility.
Implementations can use different storage backends (local file system, AWS S3,
GCP Cloud Storage, Azure Blob Storage) while maintaining a consistent interface.

All implementations should return an AbstractDataContext instance that can be
used to manage Great Expectations suites, validations, and checkpoints.
"""

from typing import Protocol

from great_expectations.data_context import AbstractDataContext


class BaseDataContext(Protocol):
    """
    Protocol defining the factory interface for Great Expectations data contexts.

    This Protocol establishes the contract for factory classes that create
    Great Expectations data context instances. A data context is the primary
    entry point for interacting with Great Expectations, providing access to
    datasources, expectation suites, validation results, and data documentation.

    Implementations of this Protocol support different storage backends for
    persisting GX configuration and artifacts. The factory pattern allows for
    runtime selection of the appropriate backend without changing client code.

    Methods
    -------
    create()
        Create and configure a Great Expectations data context instance.

    See Also
    --------
    RepoDataContext : Local file system implementation.
    S3DataContext : AWS S3 storage backend implementation.
    GCPDataContext : Google Cloud Storage backend implementation.
    AzureDataContext : Azure Blob Storage backend implementation.

    Notes
    -----
    This is a Protocol class (PEP 544), meaning it defines a structural subtype
    that doesn't require explicit inheritance. Any class implementing the
    `create()` method with the correct signature satisfies this Protocol.

    The factory pattern is used to decouple data context creation from the
    specific storage backend, enabling:

    - Dependency injection for improved testability
    - Runtime configuration of storage backends
    - Support for multiple cloud providers
    - Easy mocking in unit tests

    Great Expectations data contexts manage:

    - Datasource configurations for connecting to data
    - Expectation suites defining data quality rules
    - Validation results from running expectations
    - Data documentation and data docs sites
    - Checkpoints for orchestrating validation workflows

    Examples
    --------
    Creating a Protocol-compliant factory:

    >>> class CustomDataContext:
    ...     def __init__(self, config_path: str):
    ...         self.config_path = config_path
    ...
    ...     def create(self) -> AbstractDataContext:
    ...         # Implementation-specific logic
    ...         return EphemeralDataContext(project_config=config)

    Using the factory with dependency injection:

    >>> def validate_data(factory: BaseDataContext, data: pd.DataFrame):
    ...     context = factory.create()
    ...     # Use context for validation
    ...     return context.run_checkpoint(checkpoint_name="my_checkpoint")

    >>> fs_factory = FileSystemDataContext("./gx")
    >>> validate_data(fs_factory, df)
    {...}

    Testing with a mock factory:

    >>> class MockDataContext:
    ...     def create(self) -> AbstractDataContext:
    ...         return MagicMock(spec=AbstractDataContext)
    >>> mock_factory = MockDataContext()
    >>> result = validate_data(mock_factory, test_df)
    """

    def create(self) -> AbstractDataContext:
        """
        Create and return a Great Expectations data context instance.

        This factory method constructs an AbstractDataContext instance configured
        for the specific storage backend. The returned context is ready for use
        in validation workflows, including running checkpoints, validating data
        against expectation suites, and generating data documentation.

        Returns
        -------
        AbstractDataContext
            A configured Great Expectations data context instance. This is
            typically an EphemeralDataContext or a subclass of AbstractDataContext
            that provides access to datasources, expectation suites, validation
            results, and checkpoints.

            The returned context includes:

            - Configured datasources for data access
            - Loaded expectation suites from the backend storage
            - Checkpoint configurations for validation workflows
            - Settings for data docs generation
            - Validation result storage configuration

        Raises
        ------
        FileNotFoundError
            If the implementation requires configuration files that cannot be
            found at the specified location.
        PermissionError
            If the implementation cannot access the storage backend due to
            insufficient permissions.
        ValueError
            If the configuration is invalid or malformed.
        ConnectionError
            If the implementation cannot connect to a remote storage backend
            (e.g., cloud storage service unavailable).

        See Also
        --------
        great_expectations.data_context.EphemeralDataContext : Common return type.
        great_expectations.data_context.FileDataContext : File-based context.

        Notes
        -----
        Implementation Responsibilities
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        Implementations of this method should:

        1. Load or construct the GX project configuration
        2. Establish connections to the storage backend
        3. Initialize datasources, stores, and validation operators
        4. Return a fully configured, ready-to-use context instance

        The method should be idempotent when possible, allowing multiple calls
        to create() without side effects. However, some implementations may
        create new context instances on each call.

        Context Lifecycle
        ^^^^^^^^^^^^^^^^^
        The returned context instance manages resources that may need cleanup
        (e.g., database connections, file handles). Implementations should
        document whether contexts need explicit cleanup or use context managers.

        Thread Safety
        ^^^^^^^^^^^^^
        Implementations should document thread safety guarantees. The GX
        AbstractDataContext itself is not guaranteed to be thread-safe, so
        concurrent usage should be avoided unless explicitly supported.

        Examples
        --------
        Basic usage pattern:

        >>> factory = FileSystemDataContext(root_directory="./gx")
        >>> context = factory.create()
        >>> context.list_expectation_suite_names()
        ['suite_1', 'suite_2']

        Using the context for validation:

        >>> context = factory.create()
        >>> batch_request = context.get_batch_request(...)
        >>> validator = context.get_validator(batch_request=batch_request, expectation_suite_name="my_suite")
        >>> results = validator.validate()

        Cloud storage example:

        >>> aws_factory = AwsDataContext(bucket_name="my-gx-bucket", prefix="environments/prod/gx/")
        >>> context = aws_factory.create()
        >>> # Context reads configuration from S3
        >>> context.run_checkpoint(checkpoint_name="daily_validation")

        Testing with dependency injection:

        >>> def process_with_validation(data: pd.DataFrame, context_factory: BaseDataContext) -> dict:
        ...     context = context_factory.create()
        ...     validator = context.get_validator(...)
        ...     return validator.validate()
        >>> # Production
        >>> result = process_with_validation(df, FileSystemDataContext("./gx"))
        >>> # Testing
        >>> result = process_with_validation(df, MockDataContext())
        """
        ...
