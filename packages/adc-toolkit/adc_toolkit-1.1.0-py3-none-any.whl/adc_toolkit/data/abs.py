"""
Protocol definitions for the data module.

This module defines the foundational protocols used throughout the adc-toolkit
data handling system. These protocols establish contracts for data objects,
data catalogs, and data validators, enabling flexible implementations while
maintaining type safety and consistent interfaces.

The protocols support dependency injection and the strategy pattern, allowing
users to swap implementations (e.g., Kedro vs. custom catalogs, GX vs. Pandera
validators) without changing downstream code.

Examples
--------
Implementing a custom data object:

>>> class MyDataFrame:
...     def __init__(self, data):
...         self._data = data
...
...     @property
...     def columns(self):
...         return self._data.columns
...
...     @property
...     def dtypes(self):
...         return self._data.dtypes

Using the protocols for type hints:

>>> def process_data(catalog: DataCatalog, validator: DataValidator) -> None:
...     data = catalog.load("my_dataset")
...     validated = validator.validate("my_dataset", data)
...     catalog.save("processed_dataset", validated)
"""

from pathlib import Path
from typing import Protocol


class Data(Protocol):
    """
    Protocol for data objects in the toolkit.

    This protocol defines the minimal interface that any data object must
    implement to be compatible with the adc-toolkit data handling system.
    Data objects represent structured datasets such as pandas DataFrames,
    Spark DataFrames, or other tabular data structures.

    The protocol requires column metadata and data type information, enabling
    validators and catalogs to inspect data structure without depending on
    specific implementations.

    Attributes
    ----------
    columns : property
        Property that returns the column names or labels of the dataset.
        The exact return type depends on the implementation (e.g.,
        pandas.Index for pandas DataFrames, list of strings for Spark).
    dtypes : property
        Property that returns the data types of each column in the dataset.
        The exact return type depends on the implementation (e.g.,
        pandas.Series for pandas DataFrames, StructType for Spark).

    See Also
    --------
    DataCatalog : Protocol for loading and saving data objects.
    DataValidator : Protocol for validating data objects.

    Notes
    -----
    This is a Protocol class, not an abstract base class. Classes do not need
    to explicitly inherit from Data to be considered compatible. Any class
    that implements the required attributes will satisfy this protocol through
    structural subtyping (PEP 544).

    Common implementations include:
    - pandas.DataFrame: Provides columns and dtypes properties
    - pyspark.sql.DataFrame: Provides columns and dtypes properties
    - Custom data containers with appropriate metadata

    Examples
    --------
    A pandas DataFrame naturally satisfies this protocol:

    >>> import pandas as pd
    >>> df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    >>> df.columns
    Index(['a', 'b'], dtype='object')
    >>> df.dtypes
    a    int64
    b    int64
    dtype: object

    A custom class implementing the protocol:

    >>> class CustomData:
    ...     def __init__(self, col_names, col_types):
    ...         self._columns = col_names
    ...         self._dtypes = col_types
    ...
    ...     @property
    ...     def columns(self):
    ...         return self._columns
    ...
    ...     @property
    ...     def dtypes(self):
    ...         return self._dtypes
    >>> data = CustomData(["x", "y"], ["int", "float"])
    >>> data.columns
    ['x', 'y']
    """

    columns: property
    dtypes: property


class DataCatalog(Protocol):
    """
    Protocol for data catalog implementations.

    This protocol defines the interface for data catalogs, which handle loading
    and saving datasets. Data catalogs abstract away the details of data storage,
    file formats, and I/O operations, providing a simple name-based API for data
    access.

    Implementations typically use configuration files (e.g., YAML) to map dataset
    names to storage locations, file formats, and load/save parameters. This
    enables declarative data management and facilitates reproducible data
    pipelines.

    Methods
    -------
    in_directory(path)
        Create a new catalog instance from configuration in a directory.
    load(name)
        Load a dataset by name from the catalog.
    save(name, data)
        Save a dataset by name to the catalog.

    See Also
    --------
    Data : Protocol for data objects handled by the catalog.
    DataValidator : Protocol for validating data from catalogs.
    adc_toolkit.data.catalogs.kedro.KedroDataCatalog : Kedro-based implementation.

    Notes
    -----
    This is a Protocol class using structural subtyping (PEP 544). Implementations
    do not need to explicitly inherit from DataCatalog but must provide all
    required methods with compatible signatures.

    The catalog pattern provides several benefits:
    - Separation of concerns: data access logic separate from business logic
    - Configuration-driven: datasets defined in config files, not hardcoded
    - Testability: easy to mock or swap catalogs for testing
    - Reproducibility: consistent data loading across environments

    Thread safety and caching behavior are implementation-specific and should
    be documented in concrete implementations.

    Examples
    --------
    Using a catalog to load and save data:

    >>> catalog = SomeCatalog.in_directory("path/to/config")
    >>> df = catalog.load("training_data")
    >>> processed_df = preprocess(df)
    >>> catalog.save("processed_data", processed_df)

    Catalogs enable clean separation between data access and processing:

    >>> def pipeline(catalog: DataCatalog) -> None:
    ...     raw = catalog.load("raw_data")
    ...     cleaned = clean_data(raw)
    ...     catalog.save("cleaned_data", cleaned)
    ...     features = engineer_features(cleaned)
    ...     catalog.save("features", features)
    """

    @classmethod
    def in_directory(cls, path: str | Path) -> "DataCatalog":
        """
        Create a catalog instance from configuration in a directory.

        This factory method instantiates a catalog by reading configuration
        files from the specified directory. The configuration typically defines
        dataset names, file paths, formats, and load/save parameters.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to the directory containing catalog configuration files.
            The directory should contain YAML or other configuration files
            that define the datasets available in this catalog.

        Returns
        -------
        DataCatalog
            A new catalog instance configured with datasets from the directory.

        Raises
        ------
        FileNotFoundError
            If the specified directory does not exist.
        ValueError
            If the configuration files are invalid or cannot be parsed.

        See Also
        --------
        load : Load a dataset from the catalog.
        save : Save a dataset to the catalog.

        Notes
        -----
        The exact configuration file format and structure depend on the
        implementation. For example, Kedro-based catalogs expect a
        `catalog.yml` file with dataset definitions.

        Configuration files should not be committed with credentials or
        sensitive information. Use environment variables or separate
        credential files.

        Examples
        --------
        Create a catalog from a configuration directory:

        >>> catalog = MyCatalog.in_directory("/path/to/config")
        >>> catalog.load("my_dataset")
        <Data object>

        Using pathlib.Path:

        >>> from pathlib import Path
        >>> config_dir = Path("configs") / "production"
        >>> catalog = MyCatalog.in_directory(config_dir)
        """
        ...

    def load(self, name: str) -> Data:
        """
        Load a dataset by name from the catalog.

        Retrieve a dataset using its registered name. The catalog handles
        all I/O operations, file format parsing, and type conversions based
        on the configuration for this dataset.

        Parameters
        ----------
        name : str
            The registered name of the dataset to load. This name should
            match a dataset definition in the catalog's configuration.

        Returns
        -------
        Data
            The loaded dataset as a Data protocol-compatible object. The
            specific type depends on the catalog configuration (e.g.,
            pandas DataFrame, Spark DataFrame).

        Raises
        ------
        KeyError
            If no dataset with the given name is registered in the catalog.
        FileNotFoundError
            If the dataset's source file does not exist.
        ValueError
            If the dataset cannot be loaded due to format or parsing errors.

        See Also
        --------
        save : Save a dataset to the catalog.
        in_directory : Create a catalog from configuration.

        Notes
        -----
        The load operation may involve:
        - Reading from local files, cloud storage, or databases
        - Parsing specific file formats (CSV, Parquet, JSON, etc.)
        - Applying transformations defined in the catalog configuration
        - Caching for performance (implementation-dependent)

        Load operations should be idempotent: calling load multiple times
        with the same name should return equivalent data.

        Examples
        --------
        Load a dataset by name:

        >>> catalog = MyCatalog.in_directory("config/")
        >>> df = catalog.load("customer_data")
        >>> df.columns
        Index(['customer_id', 'name', 'email'], dtype='object')

        Load multiple datasets:

        >>> train = catalog.load("training_data")
        >>> test = catalog.load("test_data")
        >>> model = catalog.load("trained_model")
        """
        ...

    def save(self, name: str, data: Data) -> None:
        """
        Save a dataset by name to the catalog.

        Store a dataset using its registered name. The catalog handles all
        I/O operations, file format serialization, and storage operations
        based on the configuration for this dataset.

        Parameters
        ----------
        name : str
            The registered name of the dataset to save. This name should
            match a dataset definition in the catalog's configuration.
        data : Data
            The dataset to save. Must be a Data protocol-compatible object
            (e.g., pandas DataFrame, Spark DataFrame).

        Returns
        -------
        None

        Raises
        ------
        KeyError
            If no dataset with the given name is registered in the catalog.
        TypeError
            If the data type is incompatible with the dataset configuration.
        ValueError
            If the dataset cannot be saved due to validation or format errors.
        PermissionError
            If the target location is not writable.

        See Also
        --------
        load : Load a dataset from the catalog.
        in_directory : Create a catalog from configuration.

        Notes
        -----
        The save operation may involve:
        - Writing to local files, cloud storage, or databases
        - Serializing to specific file formats (CSV, Parquet, JSON, etc.)
        - Creating directories if they don't exist
        - Overwriting existing files (configuration-dependent)
        - Applying transformations before saving

        Save operations should be atomic when possible: either the entire
        dataset is saved successfully, or no partial data is written.

        Some implementations may support versioning, creating timestamped
        or numbered versions of saved datasets.

        Examples
        --------
        Save a processed dataset:

        >>> catalog = MyCatalog.in_directory("config/")
        >>> processed_df = process_data(raw_df)
        >>> catalog.save("processed_data", processed_df)

        Save multiple datasets in a pipeline:

        >>> catalog.save("cleaned_data", cleaned)
        >>> catalog.save("features", features)
        >>> catalog.save("predictions", predictions)
        """
        ...


class DataValidator(Protocol):
    """
    Protocol for data validator implementations.

    This protocol defines the interface for data validators, which verify that
    datasets meet specified quality, schema, and business rule requirements.
    Validators execute validation rules (expectations, schemas, constraints)
    and either return validated data or raise exceptions on validation failures.

    Implementations typically use configuration files to define validation
    rules separate from code. This enables declarative data validation and
    facilitates maintaining data quality in production pipelines.

    Methods
    -------
    validate(name, data)
        Validate a dataset against configured validation rules.
    in_directory(path)
        Create a new validator instance from configuration in a directory.

    See Also
    --------
    Data : Protocol for data objects being validated.
    DataCatalog : Protocol for loading data to validate.
    adc_toolkit.data.validators.gx.GXValidator : Great Expectations implementation.
    adc_toolkit.data.validators.pandera.PanderaValidator : Pandera implementation.
    adc_toolkit.data.validators.no_validator.NoValidator : No-op implementation.

    Notes
    -----
    This is a Protocol class using structural subtyping (PEP 544). Implementations
    do not need to explicitly inherit from DataValidator but must provide all
    required methods with compatible signatures.

    Validators serve multiple purposes:
    - Data quality assurance: catch schema drift and data corruption early
    - Contract enforcement: ensure data meets expectations between pipeline stages
    - Documentation: validation rules document expected data characteristics
    - Monitoring: track validation results over time to detect degradation

    Different implementations offer different trade-offs:
    - Great Expectations: Rich ecosystem, profiling, data docs, cloud support
    - Pandera: Lightweight, tight pandas integration, statistical validation
    - NoValidator: No validation overhead for trusted data sources

    Validation can be expensive on large datasets. Implementations may support
    sampling or lazy validation strategies.

    Examples
    --------
    Using a validator in a data pipeline:

    >>> validator = SomeValidator.in_directory("config/validations")
    >>> raw_data = load_data()
    >>> validated_data = validator.validate("raw_data", raw_data)

    Combining validators with catalogs:

    >>> catalog = MyCatalog.in_directory("config/")
    >>> validator = MyValidator.in_directory("config/validations")
    >>> data = catalog.load("customer_data")
    >>> validated = validator.validate("customer_data", data)
    >>> catalog.save("validated_customer_data", validated)
    """

    def validate(self, name: str, data: Data) -> Data:
        """
        Validate a dataset against configured validation rules.

        Execute all validation rules associated with the named dataset. If
        validation succeeds, return the data (potentially with validation
        metadata attached). If validation fails, raise an exception with
        details about which rules failed.

        Parameters
        ----------
        name : str
            The name identifying which validation rules to apply. This should
            correspond to a validation configuration (expectation suite, schema,
            etc.) defined in the validator's configuration.
        data : Data
            The dataset to validate. Must be a Data protocol-compatible object
            (e.g., pandas DataFrame, Spark DataFrame).

        Returns
        -------
        Data
            The validated dataset. This is typically the same object as the
            input data parameter, but implementations may attach validation
            metadata or perform transformations during validation.

        Raises
        ------
        KeyError
            If no validation rules are configured for the given name.
        ValidationError
            If the data fails validation. The exception should include details
            about which validation rules failed and the observed values.
        TypeError
            If the data type is incompatible with the validation rules.

        See Also
        --------
        in_directory : Create a validator from configuration.

        Notes
        -----
        Validation typically checks:
        - Schema: column names, data types, nullability
        - Constraints: value ranges, uniqueness, referential integrity
        - Statistical properties: distributions, correlations, outliers
        - Business rules: domain-specific requirements

        The behavior on validation failure is implementation-specific:
        - Some validators raise immediately on first failure
        - Others collect all failures and raise with complete results
        - Some support warning-level validations that log but don't raise

        Validation may modify data in some implementations:
        - Type coercion to match schema
        - Null filling or imputation
        - Outlier capping or filtering

        For large datasets, implementations may support sampling-based
        validation to reduce computational cost while maintaining statistical
        confidence.

        Examples
        --------
        Validate a dataset:

        >>> validator = MyValidator.in_directory("config/validations")
        >>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        >>> validated = validator.validate("my_dataset", df)

        Handle validation failures:

        >>> try:
        ...     validated = validator.validate("strict_dataset", df)
        ... except ValidationError as e:
        ...     print(f"Validation failed: {e}")
        ...     # Log failure, send alert, or handle gracefully

        Use in a data pipeline:

        >>> def pipeline(validator: DataValidator) -> None:
        ...     raw = load_raw_data()
        ...     validated_raw = validator.validate("raw_schema", raw)
        ...     processed = process(validated_raw)
        ...     validated_processed = validator.validate("processed_schema", processed)
        ...     save_results(validated_processed)
        """
        ...

    @classmethod
    def in_directory(cls, path: str | Path) -> "DataValidator":
        """
        Create a validator instance from configuration in a directory.

        This factory method instantiates a validator by reading validation
        configurations from the specified directory. The configuration defines
        validation rules (expectations, schemas, constraints) for named datasets.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to the directory containing validator configuration files.
            The directory should contain validation rule definitions in a
            format appropriate for the implementation (e.g., Great Expectations
            checkpoints, Pandera schemas).

        Returns
        -------
        DataValidator
            A new validator instance configured with rules from the directory.

        Raises
        ------
        FileNotFoundError
            If the specified directory does not exist.
        ValueError
            If the configuration files are invalid or cannot be parsed.

        See Also
        --------
        validate : Validate a dataset using this validator.

        Notes
        -----
        The exact configuration file format and structure depend on the
        implementation:
        - GXValidator expects Great Expectations project structure
          (expectations/, checkpoints/, great_expectations.yml)
        - PanderaValidator expects Python files defining Pandera schemas
        - Custom validators may use JSON, YAML, or other formats

        Configuration should be version controlled to track changes to
        validation rules over time.

        Some implementations support multiple configuration directories,
        allowing validation rules to be composed from multiple sources.

        Examples
        --------
        Create a validator from a configuration directory:

        >>> validator = MyValidator.in_directory("/path/to/validations")
        >>> validator.validate("dataset_name", data)
        <validated Data object>

        Using pathlib.Path:

        >>> from pathlib import Path
        >>> validation_dir = Path("config") / "data_quality"
        >>> validator = MyValidator.in_directory(validation_dir)

        Separate validators for different environments:

        >>> dev_validator = MyValidator.in_directory("config/validations/dev")
        >>> prod_validator = MyValidator.in_directory("config/validations/prod")
        """
        ...
