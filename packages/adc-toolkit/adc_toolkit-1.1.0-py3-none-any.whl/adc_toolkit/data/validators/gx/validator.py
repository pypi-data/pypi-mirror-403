"""
Great Expectations validator implementation.

This module provides the primary Great Expectations (GX) validator implementation
for the adc-toolkit data validation system. The GXValidator class implements the
DataValidator protocol, providing comprehensive data quality validation using
Great Expectations' powerful expectation framework.

The module integrates with Great Expectations' data context system, supporting
multiple storage backends (local filesystem, AWS S3, GCP, Azure) and flexible
validation strategies. It orchestrates the complete validation workflow including
expectation suite management, batch creation, checkpoint execution, and result
evaluation.

Classes
-------
GXValidator
    Main Great Expectations validator implementing the DataValidator protocol.

See Also
--------
adc_toolkit.data.abs.DataValidator : Protocol defining validator interface.
adc_toolkit.data.validators.gx.batch_managers : Batch management components.
adc_toolkit.data.validators.gx.data_context : Data context implementations.
adc_toolkit.data.catalog.ValidatedDataCatalog : Catalog with integrated validation.

Notes
-----
Great Expectations is a Python library for data quality, testing, and documentation.
This implementation provides a bridge between adc-toolkit's validation abstraction
and GX's rich validation ecosystem, enabling declarative data quality rules that
are version-controlled, documented, and continuously validated.

The validator supports automatic schema freezing: when validating data for the
first time without pre-existing expectations, it captures the schema (column names
and types) and creates expectations that enforce this schema in future validations.

Examples
--------
Basic usage with automatic expectation suite creation:

>>> from adc_toolkit.data.validators.gx import GXValidator
>>> import pandas as pd
>>> validator = GXValidator.in_directory("config/gx")
>>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
>>> validated = validator.validate("my_dataset", df)

Custom data context and strategies:

>>> from great_expectations.data_context import EphemeralDataContext
>>> from adc_toolkit.data.validators.gx.batch_managers import CustomExpectationSuiteStrategy, SkipExpectationAddition
>>> data_context = EphemeralDataContext()
>>> validator = GXValidator(
...     data_context=data_context,
...     expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy(),
...     expectation_addition_strategy=SkipExpectationAddition(),
... )

Integration with ValidatedDataCatalog:

>>> from adc_toolkit.data.catalog import ValidatedDataCatalog
>>> catalog = ValidatedDataCatalog.in_directory("config", validator=GXValidator.in_directory("config/gx"))
>>> # Validation happens automatically on load and save
>>> df = catalog.load("dataset_name")
>>> catalog.save("processed_dataset", processed_df)
"""

from pathlib import Path

from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext

from adc_toolkit.data.abs import Data
from adc_toolkit.data.validators.gx.batch_managers import (
    AutoExpectationSuiteCreation,
    ExpectationAdditionStrategy,
    ExpectationSuiteLookupStrategy,
    SchemaExpectationAddition,
    validate_dataset,
)
from adc_toolkit.data.validators.gx.data_context import RepoDataContext


class GXValidator:
    """
    Great Expectations validator implementing the DataValidator protocol.

    This validator provides comprehensive data quality validation using Great
    Expectations (GX). It orchestrates the complete validation workflow including
    data context management, expectation suite lookup, expectation creation,
    batch management, checkpoint execution, and validation result evaluation.

    The validator operates in two modes depending on configuration:

    1. **Auto-creation mode** (default): Automatically creates expectation suites
       and freezes schemas on first validation. Subsequent validations enforce
       the captured schema.

    2. **Custom mode**: Uses pre-defined expectation suites and custom strategies
       for suite lookup and expectation addition, enabling manual control over
       validation rules.

    Schema freezing captures the structure of a DataFrame (column names and types)
    and creates expectations that enforce this schema in future validations. This
    provides automatic protection against schema drift while allowing manual
    expectation customization when needed.

    Parameters
    ----------
    data_context : great_expectations.data_context.AbstractDataContext
        Great Expectations data context managing expectation suites, checkpoints,
        validation results, and data source configurations. This can be a
        filesystem-based context, cloud-based context (S3, GCS, Azure), or
        ephemeral in-memory context for testing.
    expectation_suite_lookup_strategy : ExpectationSuiteLookupStrategy or None, optional
        Strategy for handling expectation suite lookup when validating datasets.
        Controls behavior when a suite does not exist for a dataset:

        - AutoExpectationSuiteCreation (default): Automatically creates missing
          suites, enabling zero-configuration validation.
        - CustomExpectationSuiteStrategy: Raises ExpectationSuiteNotFoundError
          for missing suites, enforcing explicit suite definitions.

        Default is None, which uses AutoExpectationSuiteCreation.
    expectation_addition_strategy : ExpectationAdditionStrategy or None, optional
        Strategy for adding expectations to expectation suites during validation.
        Controls how expectations are populated when a suite is created or updated:

        - SchemaExpectationAddition (default): Automatically adds schema
          expectations by inspecting DataFrame structure, freezing the schema.
        - SkipExpectationAddition: Skips automatic expectation addition,
          requiring manual expectation definition.

        Default is None, which uses SchemaExpectationAddition.

    Attributes
    ----------
    data_context : great_expectations.data_context.AbstractDataContext
        The Great Expectations data context instance used for all validation
        operations.
    expectation_suite_lookup_strategy : ExpectationSuiteLookupStrategy
        The strategy used for expectation suite lookup.
    expectation_addition_strategy : ExpectationAdditionStrategy
        The strategy used for adding expectations to suites.

    See Also
    --------
    adc_toolkit.data.abs.DataValidator : Protocol defining validator interface.
    adc_toolkit.data.validators.gx.data_context.RepoDataContext : Filesystem-based data context.
    adc_toolkit.data.validators.gx.data_context.S3DataContext : AWS S3-based data context.
    adc_toolkit.data.validators.gx.data_context.GCPDataContext : Google Cloud Storage context.
    adc_toolkit.data.validators.gx.data_context.AzureDataContext : Azure Blob Storage context.
    adc_toolkit.data.validators.gx.batch_managers.AutoExpectationSuiteCreation : Auto-create suites.
    adc_toolkit.data.validators.gx.batch_managers.CustomExpectationSuiteStrategy : Require suites.
    adc_toolkit.data.validators.gx.batch_managers.SchemaExpectationAddition : Auto-add schema expectations.
    adc_toolkit.data.validators.gx.batch_managers.SkipExpectationAddition : Skip expectation addition.

    Notes
    -----
    **Design Patterns:**

    The GXValidator implements several design patterns:

    - **Strategy Pattern**: Pluggable strategies for suite lookup and expectation
      addition enable flexible validation workflows without modifying core logic.
    - **Facade Pattern**: Simplifies Great Expectations' complex API by providing
      a clean, high-level interface for validation.
    - **Dependency Injection**: Data context and strategies are injected,
      enabling testability and configuration flexibility.

    **Validation Workflow:**

    When validate() is called, the following sequence occurs:

    1. Look up or create expectation suite for the dataset
    2. Create a batch from the data using BatchManager
    3. Add expectations to the suite using the configured strategy
    4. Create or update a checkpoint for the dataset
    5. Execute the checkpoint to validate data against expectations
    6. Evaluate validation results and raise ValidationError on failure
    7. Return the original data if validation succeeds

    **Performance Considerations:**

    - First validation of a dataset (suite creation) is slower than subsequent
      validations due to suite initialization overhead.
    - Schema freezing requires full DataFrame inspection, which scales with
      the number of columns (not rows).
    - Validation performance depends on the number and complexity of expectations.
    - Consider using sampling for large datasets with expensive expectations.

    **Thread Safety:**

    GXValidator instances are not thread-safe. The underlying Great Expectations
    data context may perform file I/O and maintain internal state. For concurrent
    validation, create separate validator instances per thread.

    **Cloud Storage:**

    When using cloud-based data contexts (S3, GCS, Azure), ensure appropriate
    credentials and permissions are configured. The data context stores expectation
    suites, checkpoints, and validation results in cloud storage.

    Examples
    --------
    Create a validator with default auto-creation behavior:

    >>> from adc_toolkit.data.validators.gx import GXValidator
    >>> from great_expectations.data_context import EphemeralDataContext
    >>> import pandas as pd
    >>> context = EphemeralDataContext()
    >>> validator = GXValidator(data_context=context)
    >>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
    >>> validated = validator.validate("dataset_name", df)

    Create a validator requiring pre-defined expectation suites:

    >>> from adc_toolkit.data.validators.gx.batch_managers import (
    ...     CustomExpectationSuiteStrategy,
    ...     SkipExpectationAddition,
    ... )
    >>> validator = GXValidator(
    ...     data_context=context,
    ...     expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy(),
    ...     expectation_addition_strategy=SkipExpectationAddition(),
    ... )
    >>> # This will raise ExpectationSuiteNotFoundError if suite doesn't exist
    >>> validated = validator.validate("strict_dataset", df)

    Use with a filesystem-based data context:

    >>> validator = GXValidator.in_directory("/path/to/gx/config")
    >>> df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    >>> validated = validator.validate("my_data", df)

    Validate with automatic schema freezing:

    >>> df_first = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    >>> validator.validate("users", df_first)  # Creates suite, freezes schema
    >>> df_second = pd.DataFrame({"id": [3, 4], "name": ["Charlie", "Dave"]})
    >>> validator.validate("users", df_second)  # Validates against frozen schema
    >>> df_invalid = pd.DataFrame({"id": [5], "age": [30]})  # Different schema
    >>> validator.validate("users", df_invalid)  # Raises ValidationError

    Integration with ValidatedDataCatalog:

    >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
    >>> catalog = ValidatedDataCatalog.in_directory(
    ...     catalog_dir="config/catalog", validator=GXValidator.in_directory("config/gx")
    ... )
    >>> # Load with automatic validation
    >>> df = catalog.load("customer_data")
    >>> # Process data
    >>> processed = transform(df)
    >>> # Save with automatic validation
    >>> catalog.save("processed_customer_data", processed)
    """

    __slots__ = [
        "data_context",
        "expectation_addition_strategy",
        "expectation_suite_lookup_strategy",
    ]

    def __init__(
        self,
        data_context: AbstractDataContext,
        expectation_suite_lookup_strategy: ExpectationSuiteLookupStrategy | None = None,
        expectation_addition_strategy: ExpectationAdditionStrategy | None = None,
    ) -> None:
        """
        Initialize a Great Expectations validator with specified configuration.

        Creates a new GXValidator instance with the provided data context and
        validation strategies. The data context manages expectation suites,
        checkpoints, and validation results. The strategies control how the
        validator handles missing expectation suites and how it populates
        suites with expectations.

        Parameters
        ----------
        data_context : great_expectations.data_context.AbstractDataContext
            Great Expectations data context to use for all validation operations.
            This context manages the storage and retrieval of expectation suites,
            checkpoints, and validation results. Can be:

            - RepoDataContext: Filesystem-based context stored in a directory
            - S3DataContext: AWS S3-backed context for cloud deployments
            - GCPDataContext: Google Cloud Storage-backed context
            - AzureDataContext: Azure Blob Storage-backed context
            - EphemeralDataContext: In-memory context for testing

        expectation_suite_lookup_strategy : ExpectationSuiteLookupStrategy or None, optional
            Strategy for handling expectation suite lookup operations. Controls
            the behavior when an expectation suite is not found for a dataset:

            - None (default): Uses AutoExpectationSuiteCreation, which
              automatically creates missing suites with zero configuration.
            - AutoExpectationSuiteCreation(): Explicitly auto-creates suites.
            - CustomExpectationSuiteStrategy(): Raises an error for missing
              suites, enforcing that all suites must be pre-defined.

            Default is None, which is equivalent to AutoExpectationSuiteCreation().

        expectation_addition_strategy : ExpectationAdditionStrategy or None, optional
            Strategy for adding expectations to expectation suites. Controls
            how expectations are populated when validating data:

            - None (default): Uses SchemaExpectationAddition, which inspects
              DataFrame structure and adds schema validation expectations.
            - SchemaExpectationAddition(): Explicitly adds schema expectations
              by freezing the DataFrame's column names and types.
            - SkipExpectationAddition(): Skips automatic expectation addition,
              requiring all expectations to be manually defined.

            Default is None, which is equivalent to SchemaExpectationAddition().

        Returns
        -------
        None

        See Also
        --------
        in_directory : Factory method to create validator from configuration directory.
        validate : Validate data using this validator.
        adc_toolkit.data.validators.gx.data_context.RepoDataContext : Create filesystem context.
        adc_toolkit.data.validators.gx.batch_managers.AutoExpectationSuiteCreation : Auto-create strategy.
        adc_toolkit.data.validators.gx.batch_managers.SchemaExpectationAddition : Schema freeze strategy.

        Notes
        -----
        The constructor performs minimal initialization, only storing the provided
        parameters. No I/O operations, file system access, or data context
        initialization occurs during construction. This enables fast instantiation
        and lazy initialization patterns.

        **Default Strategies:**

        When strategy parameters are None, the validator uses sensible defaults:

        - AutoExpectationSuiteCreation: Enables zero-configuration validation
          by automatically creating expectation suites on first use.
        - SchemaExpectationAddition: Provides automatic schema drift protection
          by freezing the DataFrame structure on first validation.

        These defaults are ideal for development, exploration, and rapid
        prototyping. For production deployments with explicit validation rules,
        consider using CustomExpectationSuiteStrategy and pre-defined suites.

        **Strategy Immutability:**

        Once a validator is instantiated, its strategies cannot be changed.
        To use different strategies, create a new validator instance. This
        design ensures consistent validation behavior throughout a validator's
        lifetime.

        **Data Context Lifecycle:**

        The validator does not own the data context lifecycle. The caller is
        responsible for creating and properly disposing of the data context.
        For ephemeral contexts used in testing, ensure proper cleanup:

        >>> context = EphemeralDataContext()
        >>> try:
        ...     validator = GXValidator(data_context=context)
        ...     # Use validator
        ... finally:
        ...     # Clean up context if needed
        ...     pass

        Examples
        --------
        Create a validator with default auto-creation strategies:

        >>> from great_expectations.data_context import EphemeralDataContext
        >>> context = EphemeralDataContext()
        >>> validator = GXValidator(data_context=context)
        >>> # Automatically creates suites and freezes schemas

        Create a validator with strict, manual suite management:

        >>> from adc_toolkit.data.validators.gx.batch_managers import (
        ...     CustomExpectationSuiteStrategy,
        ...     SkipExpectationAddition,
        ... )
        >>> validator = GXValidator(
        ...     data_context=context,
        ...     expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy(),
        ...     expectation_addition_strategy=SkipExpectationAddition(),
        ... )
        >>> # Requires pre-defined suites, no automatic expectations

        Create a validator with auto-creation but manual expectations:

        >>> validator = GXValidator(
        ...     data_context=context,
        ...     expectation_suite_lookup_strategy=AutoExpectationSuiteCreation(),
        ...     expectation_addition_strategy=SkipExpectationAddition(),
        ... )
        >>> # Creates suites automatically but expects manual expectation definition

        Use with a filesystem-based data context:

        >>> from adc_toolkit.data.validators.gx.data_context import RepoDataContext
        >>> context = RepoDataContext("/path/to/gx").create()
        >>> validator = GXValidator(data_context=context)

        Use with a cloud-based data context:

        >>> from adc_toolkit.data.validators.gx.data_context import S3DataContext
        >>> context = S3DataContext("s3://my-bucket/gx-config").create()
        >>> validator = GXValidator(data_context=context)
        """
        self.data_context = data_context
        self.expectation_suite_lookup_strategy = expectation_suite_lookup_strategy or AutoExpectationSuiteCreation()
        self.expectation_addition_strategy = expectation_addition_strategy or SchemaExpectationAddition()

    @classmethod
    def in_directory(cls, path: str | Path) -> "GXValidator":
        """
        Create a GXValidator with a filesystem-based Great Expectations data context.

        This factory method provides a convenient way to create a validator using
        a repository-based (filesystem) data context. It initializes a RepoDataContext
        from the specified directory and creates a validator with default strategies
        for auto-creation and schema freezing.

        The specified directory should contain a Great Expectations project structure
        with configuration files, expectation suites, checkpoints, and validation
        results. If the directory does not contain a valid GX project, the
        RepoDataContext will initialize a new project structure.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to the directory containing Great Expectations configuration.
            This directory should have (or will be initialized with) the
            following structure:

            - great_expectations.yml : Main configuration file
            - expectations/ : Directory containing expectation suite JSON files
            - checkpoints/ : Directory containing checkpoint YAML files
            - uncommitted/ : Directory for validation results and data docs
            - plugins/ : Optional directory for custom expectations

            If the directory does not exist or is empty, a new GX project
            structure will be created. Both absolute and relative paths are
            supported.

        Returns
        -------
        GXValidator
            A new GXValidator instance configured with:

            - RepoDataContext based on the specified directory
            - AutoExpectationSuiteCreation strategy (creates suites automatically)
            - SchemaExpectationAddition strategy (freezes schemas automatically)

        Raises
        ------
        FileNotFoundError
            If the parent directory of the specified path does not exist
            and cannot be created.
        PermissionError
            If the process lacks permissions to read from or write to the
            specified directory.
        ValueError
            If the directory contains invalid Great Expectations configuration
            files that cannot be parsed.

        See Also
        --------
        __init__ : Constructor for custom data context and strategy configuration.
        validate : Validate data using this validator.
        adc_toolkit.data.validators.gx.data_context.RepoDataContext : Filesystem context implementation.
        adc_toolkit.data.validators.gx.data_context.S3DataContext : AWS S3-based context.
        adc_toolkit.data.validators.gx.data_context.GCPDataContext : Google Cloud context.

        Notes
        -----
        **Repository Structure:**

        Great Expectations uses a specific directory structure to organize
        validation artifacts:

        - Expectation suites are stored as JSON in expectations/
        - Checkpoints are stored as YAML in checkpoints/
        - Validation results go in uncommitted/validations/
        - Data docs are generated in uncommitted/data_docs/

        This structure enables version control of validation rules while keeping
        validation results and documentation out of version control.

        **Version Control:**

        When using filesystem-based contexts, consider the following for version
        control (Git):

        - Commit: expectations/, checkpoints/, great_expectations.yml, plugins/
        - Ignore: uncommitted/ (contains validation results and generated docs)

        This approach version controls validation rules while excluding
        environment-specific results.

        **Performance:**

        The in_directory method performs I/O operations to read configuration
        and initialize the data context. For applications creating many validator
        instances, consider caching the data context and passing it to __init__
        instead of using in_directory repeatedly.

        **Automatic Initialization:**

        If the specified directory does not contain a great_expectations.yml file,
        RepoDataContext will initialize a new GX project. This is useful for
        quickly starting validation without manual GX project setup, but may not
        be suitable for production deployments where explicit configuration is
        preferred.

        **Default Strategies:**

        This factory method always uses default strategies (AutoExpectationSuiteCreation
        and SchemaExpectationAddition). For custom strategies, use the __init__
        constructor directly:

        >>> from adc_toolkit.data.validators.gx.data_context import RepoDataContext
        >>> context = RepoDataContext(path).create()
        >>> validator = GXValidator(data_context=context, expectation_suite_lookup_strategy=CustomStrategy())

        Examples
        --------
        Create a validator from a GX project directory:

        >>> validator = GXValidator.in_directory("/path/to/gx_project")
        >>> import pandas as pd
        >>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        >>> validated = validator.validate("my_dataset", df)

        Use with a relative path:

        >>> validator = GXValidator.in_directory("config/validations")
        >>> validated = validator.validate("dataset", data)

        Use with pathlib.Path:

        >>> from pathlib import Path
        >>> config_path = Path("config") / "gx"
        >>> validator = GXValidator.in_directory(config_path)

        Initialize a new GX project and validator:

        >>> # Directory doesn't exist yet
        >>> validator = GXValidator.in_directory("./new_gx_project")
        >>> # Now directory contains initialized GX project structure

        Validate multiple datasets with one validator:

        >>> validator = GXValidator.in_directory("config/gx")
        >>> df1 = pd.DataFrame({"a": [1, 2]})
        >>> df2 = pd.DataFrame({"b": ["x", "y"]})
        >>> validated1 = validator.validate("dataset1", df1)
        >>> validated2 = validator.validate("dataset2", df2)

        Integration in a data pipeline:

        >>> def validate_pipeline_data(data_path: str, gx_path: str) -> None:
        ...     validator = GXValidator.in_directory(gx_path)
        ...     for dataset_name in ["raw", "cleaned", "features"]:
        ...         df = pd.read_csv(f"{data_path}/{dataset_name}.csv")
        ...         validated = validator.validate(dataset_name, df)
        ...         print(f"Validated {dataset_name}: {len(validated)} rows")
        """
        return cls(data_context=RepoDataContext(path).create())

    def validate(self, name: str, data: Data) -> Data:
        """
        Validate data against Great Expectations rules for the named dataset.

        Executes the complete Great Expectations validation workflow for the
        specified dataset. This includes expectation suite lookup or creation,
        batch request generation, expectation addition, checkpoint creation and
        execution, and validation result evaluation.

        The validation process ensures data quality by verifying that the data
        meets all expectations defined in the associated expectation suite. If
        validation fails, detailed error information identifies which expectations
        failed and why.

        On successful validation, the original data is returned unchanged. The
        validation is side-effect free from the data perspective, but may create
        or update expectation suites, checkpoints, and validation results in the
        data context storage.

        Parameters
        ----------
        name : str
            Identifier for the dataset being validated. This name is used to:

            - Look up the corresponding expectation suite (named "{name}_suite")
            - Create or update the checkpoint for this dataset
            - Store validation results associated with this dataset

            The name should be consistent across validation calls for the same
            logical dataset to ensure proper suite reuse and result tracking.
            Use descriptive, stable names like "customer_data", "sales_features",
            or "model_predictions".

        data : Data
            The dataset to validate. Must be a Data protocol-compatible object,
            typically a pandas DataFrame or Spark DataFrame. The data should
            have `columns` and `dtypes` properties for schema inspection.

            The data is not modified by validation. If validation succeeds,
            the same object (or an equivalent copy) is returned.

        Returns
        -------
        Data
            The validated data. This is the same object as the input `data`
            parameter if validation succeeds. The return type matches the input
            type (e.g., pandas.DataFrame returns pandas.DataFrame).

            Returning the data enables method chaining and integration with
            pipelines:

            >>> validated = validator.validate("data", raw_data)
            >>> processed = transform(validated)

        Raises
        ------
        ValidationError
            If the data fails validation against the expectation suite. The
            exception contains detailed information about:

            - Which expectations failed
            - Observed values that violated expectations
            - Expected values or constraints
            - Summary statistics for failed validations

            This exception indicates data quality issues that must be addressed
            before proceeding with downstream processing.

        ExpectationSuiteNotFoundError
            If the expectation suite for the dataset does not exist and the
            validator is configured with CustomExpectationSuiteStrategy. This
            indicates that validation rules must be explicitly defined before
            validation can proceed.

            To resolve, either:
            - Create the expectation suite manually in the data context
            - Switch to AutoExpectationSuiteCreation strategy
            - Ensure the correct data context is being used

        TypeError
            If the data type is incompatible with Great Expectations batch
            creation. For example, if the data does not have the required
            `columns` and `dtypes` attributes.

        KeyError
            If the batch manager cannot create a batch from the data due to
            missing required attributes or metadata.

        See Also
        --------
        __init__ : Constructor for configuring validation strategies.
        in_directory : Factory method for filesystem-based validators.
        adc_toolkit.data.validators.gx.batch_managers.validate_dataset : Underlying validation function.
        adc_toolkit.data.abs.DataValidator.validate : Protocol method specification.

        Notes
        -----
        **Validation Workflow:**

        The validate method orchestrates these steps:

        1. **Suite Lookup**: Check if an expectation suite exists for the dataset.
           If not, behavior depends on the lookup strategy:

           - AutoExpectationSuiteCreation: Create a new suite
           - CustomExpectationSuiteStrategy: Raise ExpectationSuiteNotFoundError

        2. **Batch Creation**: Convert the data into a GX Batch object using
           BatchManager, making it compatible with GX validation operations.

        3. **Expectation Addition**: Add expectations to the suite based on the
           addition strategy:

           - SchemaExpectationAddition: Inspect data schema and add schema expectations
           - SkipExpectationAddition: Skip, expecting manual expectation definition

        4. **Checkpoint Execution**: Create or update a checkpoint for the dataset
           and execute it to validate the batch against the expectation suite.

        5. **Result Evaluation**: Analyze validation results. If all expectations
           pass, return the data. If any fail, raise ValidationError with details.

        **First Validation vs. Subsequent Validations:**

        The first time a dataset is validated (with AutoExpectationSuiteCreation
        and SchemaExpectationAddition), the validator:

        - Creates an expectation suite named "{name}_suite"
        - Inspects the DataFrame schema (column names and types)
        - Adds schema expectations that "freeze" this structure
        - Creates a checkpoint for the dataset
        - Validates the data (which should pass since expectations match the data)

        Subsequent validations of the same dataset:

        - Reuse the existing expectation suite and checkpoint
        - Validate data against the frozen schema and any other expectations
        - Detect schema drift or data quality issues

        **Performance:**

        Validation performance depends on several factors:

        - Number of expectations in the suite
        - Complexity of expectations (simple schema checks vs. statistical tests)
        - Size of the dataset (some expectations scan all data)
        - Data context backend (filesystem vs. cloud storage)

        First validation is slower due to suite and checkpoint creation overhead.
        Subsequent validations are faster, typically scaling with the number of
        expectations rather than data size.

        For large datasets with expensive expectations, consider:
        - Sampling strategies to validate subsets
        - Caching validation results
        - Running validations asynchronously
        - Using incremental validation for streaming data

        **Idempotency:**

        Validation is idempotent: validating the same data multiple times with
        the same name produces the same result (pass or fail). However, validation
        results are stored with timestamps, so each validation creates new result
        artifacts in the data context.

        **Thread Safety:**

        The validate method is not thread-safe. Multiple threads validating
        different datasets concurrently may encounter race conditions when
        accessing the data context. For concurrent validation, create separate
        validator instances (with separate data contexts) per thread.

        **Side Effects:**

        While validation does not modify the data, it may have side effects:

        - Create or update expectation suites in the data context
        - Create or update checkpoints in the data context
        - Write validation results to storage (filesystem or cloud)
        - Generate data documentation if configured

        These artifacts are stored according to the data context configuration.

        Examples
        --------
        Basic validation with automatic suite creation:

        >>> import pandas as pd
        >>> from adc_toolkit.data.validators.gx import GXValidator
        >>> validator = GXValidator.in_directory("config/gx")
        >>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        >>> validated = validator.validate("sales_data", df)
        >>> # First validation creates suite and freezes schema
        >>> validated.shape
        (3, 2)

        Subsequent validation detects schema drift:

        >>> df_valid = pd.DataFrame({"id": [4, 5], "value": [40, 50]})
        >>> validator.validate("sales_data", df_valid)  # Passes, schema matches
        >>> df_invalid = pd.DataFrame({"id": [6], "price": [100]})
        >>> validator.validate("sales_data", df_invalid)  # Raises ValidationError

        Handle validation failures gracefully:

        >>> try:
        ...     validated = validator.validate("strict_data", df)
        ... except ValidationError as e:
        ...     print(f"Validation failed: {e}")
        ...     # Log error, send alert, reject data, etc.
        ...     raise

        Validate multiple datasets in a pipeline:

        >>> def etl_pipeline(validator: GXValidator) -> None:
        ...     raw = load_raw_data()
        ...     validated_raw = validator.validate("raw_data", raw)
        ...     cleaned = clean(validated_raw)
        ...     validated_clean = validator.validate("cleaned_data", cleaned)
        ...     features = engineer_features(validated_clean)
        ...     validated_features = validator.validate("features", features)
        ...     save(validated_features)

        Use validation in data loading:

        >>> class ValidatedDataLoader:
        ...     def __init__(self, validator: GXValidator):
        ...         self.validator = validator
        ...
        ...     def load(self, name: str, path: str) -> pd.DataFrame:
        ...         df = pd.read_csv(path)
        ...         return self.validator.validate(name, df)

        Integration with ValidatedDataCatalog:

        >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
        >>> catalog = ValidatedDataCatalog.in_directory(
        ...     "config/catalog", validator=GXValidator.in_directory("config/gx")
        ... )
        >>> # Validation happens automatically on load
        >>> df = catalog.load("customer_data")  # Validates after loading
        >>> processed = transform(df)
        >>> catalog.save("processed_data", processed)  # Validates before saving

        Validate with custom expectation suite:

        >>> # Pre-create suite with custom expectations
        >>> suite = context.create_expectation_suite("custom_data_suite")
        >>> suite.add_expectation(
        ...     ExpectationConfiguration(
        ...         expectation_type="expect_column_values_to_be_in_range",
        ...         kwargs={"column": "age", "min_value": 0, "max_value": 120},
        ...     )
        ... )
        >>> # Now validate using the custom suite
        >>> df = pd.DataFrame({"age": [25, 30, 35]})
        >>> validator.validate("custom_data", df)  # Uses custom_data_suite
        """
        return validate_dataset(
            name,
            data,
            self.data_context,
            self.expectation_suite_lookup_strategy,
            self.expectation_addition_strategy,
        )
