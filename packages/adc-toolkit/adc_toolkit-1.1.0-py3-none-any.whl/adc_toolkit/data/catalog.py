"""
Default adc_toolkit data catalog.

This module provides the ValidatedDataCatalog class, which is the primary
user-facing API for the adc-toolkit data handling system. It combines a
data catalog (for I/O operations) with a data validator (for quality checks)
to provide automatic validation on all data loading and saving operations.
"""

from pathlib import Path
from typing import Any

from adc_toolkit.data.abs import Data, DataCatalog, DataValidator
from adc_toolkit.data.default_attributes import default_catalog, default_validator


class ValidatedDataCatalog:
    """
    Data catalog with automatic validation on load and save operations.

    ValidatedDataCatalog is the main user-facing API for the adc-toolkit data
    handling system. It wraps a DataCatalog (responsible for I/O operations)
    and a DataValidator (responsible for data quality checks) to provide a
    unified interface that automatically validates data after loading and
    before saving.

    This design ensures data quality is enforced at catalog boundaries,
    catching issues early in data pipelines. Validation is transparent to
    the user: simply call load() and save() as you would with a regular
    catalog, and validation happens automatically.

    The class uses dependency injection to allow flexible catalog and
    validator implementations. By default, it uses KedroDataCatalog for
    I/O and GXValidator (Great Expectations) for validation, but these
    can be swapped for custom implementations or alternative validators
    like PanderaValidator.

    Parameters
    ----------
    catalog : DataCatalog
        The data catalog instance responsible for loading and saving datasets.
        Must implement the DataCatalog protocol with load() and save() methods.
        The default implementation is KedroDataCatalog, which uses Kedro's
        configuration-driven catalog system with YAML-based dataset definitions.
    validator : DataValidator
        The data validator instance responsible for validating datasets.
        Must implement the DataValidator protocol with a validate() method.
        The default implementation is GXValidator (Great Expectations), with
        PanderaValidator as a fallback. Use NoValidator to disable validation.

    Attributes
    ----------
    catalog : DataCatalog
        The underlying data catalog for I/O operations. Immutable after
        instantiation.
    validator : DataValidator
        The underlying data validator for quality checks. Immutable after
        instantiation.

    See Also
    --------
    DataCatalog : Protocol defining the catalog interface.
    DataValidator : Protocol defining the validator interface.
    adc_toolkit.data.catalogs.kedro.KedroDataCatalog : Default catalog implementation.
    adc_toolkit.data.validators.gx.GXValidator : Default validator (Great Expectations).
    adc_toolkit.data.validators.pandera.PanderaValidator : Alternative validator.
    adc_toolkit.data.validators.no_validator.NoValidator : No-op validator.

    Notes
    -----
    The class uses `__slots__` to restrict attributes to only 'catalog' and
    'validator', preventing accidental attribute additions and reducing memory
    overhead.

    Attributes are immutable after instantiation. To use a different catalog
    or validator, create a new ValidatedDataCatalog instance.

    Validation happens in the following order:
    - On load: catalog.load() -> validator.validate() -> return validated data
    - On save: validator.validate() -> catalog.save() -> return None

    This means invalid data will never be saved, and loaded data is always
    validated before being returned to the caller.

    The factory method in_directory() is the recommended way to instantiate
    this class for most use cases. Direct instantiation via __init__() is
    primarily useful for testing or custom configurations.

    Examples
    --------
    Basic usage with default catalog and validator:

    >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
    >>> catalog = ValidatedDataCatalog.in_directory("config/data")
    >>> df = catalog.load("customer_data")
    >>> # Data is automatically validated after loading
    >>> processed_df = process_data(df)
    >>> catalog.save("processed_customer_data", processed_df)
    >>> # Data is automatically validated before saving

    Using a custom validator while keeping the default catalog:

    >>> from adc_toolkit.data.validators.pandera import PanderaValidator
    >>> catalog = ValidatedDataCatalog.in_directory("config/data", validator_class=PanderaValidator)
    >>> df = catalog.load("sales_data")

    Using custom catalog and validator implementations:

    >>> from myproject.catalogs import CustomCatalog
    >>> from myproject.validators import CustomValidator
    >>> catalog = ValidatedDataCatalog.in_directory(
    ...     "config/data", catalog_class=CustomCatalog, validator_class=CustomValidator
    ... )

    Direct instantiation for testing or advanced use cases:

    >>> from unittest.mock import Mock
    >>> mock_catalog = Mock(spec=DataCatalog)
    >>> mock_validator = Mock(spec=DataValidator)
    >>> catalog = ValidatedDataCatalog(catalog=mock_catalog, validator=mock_validator)

    Complete data pipeline example:

    >>> import pandas as pd
    >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
    >>>
    >>> # Initialize catalog with validation
    >>> catalog = ValidatedDataCatalog.in_directory("config/production")
    >>>
    >>> # Load and automatically validate raw data
    >>> raw_data = catalog.load("raw_sales")
    >>>
    >>> # Process data
    >>> cleaned = raw_data.dropna()
    >>> aggregated = cleaned.groupby("region").sum()
    >>>
    >>> # Save and automatically validate before writing
    >>> catalog.save("aggregated_sales", aggregated)
    >>>
    >>> # Validation errors are raised if data doesn't meet expectations
    >>> try:
    ...     invalid_df = pd.DataFrame({"bad_column": [1, 2, 3]})
    ...     catalog.save("aggregated_sales", invalid_df)
    ... except Exception as e:
    ...     print(f"Validation failed: {e}")

    Disabling validation for trusted data sources:

    >>> from adc_toolkit.data.validators.no_validator import NoValidator
    >>> catalog = ValidatedDataCatalog.in_directory("config/data", validator_class=NoValidator)
    >>> # No validation overhead, useful for performance-critical paths
    >>> df = catalog.load("trusted_source")
    """

    __slots__ = ("catalog", "validator")

    def __init__(self, catalog: DataCatalog, validator: DataValidator) -> None:
        """
        Initialize a ValidatedDataCatalog with a catalog and validator.

        This constructor is primarily used for testing or advanced use cases
        where you have already instantiated catalog and validator objects.
        For most use cases, prefer the in_directory() factory method.

        Parameters
        ----------
        catalog : DataCatalog
            The data catalog instance for I/O operations. Must implement the
            DataCatalog protocol with load(name) and save(name, data) methods.
        validator : DataValidator
            The data validator instance for quality checks. Must implement the
            DataValidator protocol with a validate(name, data) method.

        See Also
        --------
        in_directory : Factory method for creating instances from configuration.
        load : Load and validate a dataset.
        save : Validate and save a dataset.

        Notes
        -----
        Both catalog and validator are stored as instance attributes and
        become immutable after initialization due to `__slots__`.

        The constructor performs no validation of the provided objects beyond
        type annotations. It's the caller's responsibility to ensure the
        objects implement the required protocols correctly.

        Examples
        --------
        Direct instantiation with concrete implementations:

        >>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
        >>> from adc_toolkit.data.validators.gx import GXValidator
        >>>
        >>> catalog_impl = KedroDataCatalog("config/data")
        >>> validator_impl = GXValidator.in_directory("config/validations")
        >>> validated_catalog = ValidatedDataCatalog(catalog=catalog_impl, validator=validator_impl)

        Using mock objects for testing:

        >>> from unittest.mock import Mock
        >>> import pandas as pd
        >>>
        >>> mock_catalog = Mock(spec=DataCatalog)
        >>> mock_validator = Mock(spec=DataValidator)
        >>>
        >>> # Setup mock behavior
        >>> test_df = pd.DataFrame({"a": [1, 2, 3]})
        >>> mock_catalog.load.return_value = test_df
        >>> mock_validator.validate.return_value = test_df
        >>>
        >>> catalog = ValidatedDataCatalog(mock_catalog, mock_validator)
        >>> result = catalog.load("test_dataset")
        >>> mock_catalog.load.assert_called_once_with("test_dataset")
        """
        self.catalog = catalog
        self.validator = validator

    @classmethod
    def in_directory(
        cls,
        path: str | Path,
        catalog_class: type[DataCatalog] | None = None,
        validator_class: type[DataValidator] | None = None,
    ) -> "ValidatedDataCatalog":
        """
        Create a validated catalog from configuration in a directory.

        This is the recommended factory method for creating ValidatedDataCatalog
        instances in production code. It reads configuration files from the
        specified directory and instantiates both the catalog and validator
        using their respective in_directory() factory methods.

        By default, this method uses KedroDataCatalog for I/O operations and
        GXValidator (Great Expectations) for validation. If Great Expectations
        is not installed, it falls back to PanderaValidator. Custom
        implementations can be provided via the catalog_class and
        validator_class parameters.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to the directory containing catalog and validator configuration
            files. This directory typically contains:
            - catalog.yml: Kedro catalog configuration (for KedroDataCatalog)
            - expectations/: Great Expectations suite definitions (for GXValidator)
            - Or equivalent configuration for custom implementations.
            The path can be absolute or relative to the current working directory.
        catalog_class : type[DataCatalog] or None, optional
            Custom data catalog class to use instead of the default. Must be a
            class (not instance) that implements the DataCatalog protocol and
            provides an in_directory(path) class method. If None (default),
            uses KedroDataCatalog.
        validator_class : type[DataValidator] or None, optional
            Custom data validator class to use instead of the default. Must be
            a class (not instance) that implements the DataValidator protocol
            and provides an in_directory(path) class method. If None (default),
            uses GXValidator if available, otherwise PanderaValidator.

        Returns
        -------
        ValidatedDataCatalog
            A new ValidatedDataCatalog instance with catalog and validator
            initialized from the configuration directory.

        Raises
        ------
        FileNotFoundError
            If the specified directory does not exist or required configuration
            files are missing.
        ImportError
            If default catalog/validator classes are requested but their
            required packages are not installed (e.g., kedro, great_expectations,
            or pandera).
        ValueError
            If configuration files are malformed or contain invalid settings.

        See Also
        --------
        __init__ : Direct constructor for advanced use cases.
        load : Load and validate a dataset from the catalog.
        save : Validate and save a dataset to the catalog.
        adc_toolkit.data.default_attributes.default_catalog : Function that creates default catalog.
        adc_toolkit.data.default_attributes.default_validator : Function that creates default validator.

        Notes
        -----
        The method calls in_directory() on the catalog and validator classes,
        which are responsible for reading their respective configuration files.
        The exact configuration file format depends on the implementations used.

        For KedroDataCatalog (default), the directory should contain:
        - catalog.yml: Dataset definitions in Kedro format
        - (optionally) credentials.yml: Credential configurations

        For GXValidator (default), the directory should contain:
        - great_expectations.yml: GX project configuration
        - expectations/: Directory with expectation suite JSON files
        - checkpoints/: Directory with checkpoint configurations

        For PanderaValidator, the directory should contain:
        - Python files defining Pandera schemas for each dataset

        The directory structure can be organized as needed; implementations
        are responsible for finding their configuration files within the path.

        This method is thread-safe as long as the underlying catalog and
        validator implementations are thread-safe.

        Examples
        --------
        Basic usage with default catalog and validator:

        >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
        >>> catalog = ValidatedDataCatalog.in_directory("config/data")
        >>> # Uses KedroDataCatalog and GXValidator (or PanderaValidator)

        Using pathlib.Path:

        >>> from pathlib import Path
        >>> config_dir = Path("config") / "production" / "data"
        >>> catalog = ValidatedDataCatalog.in_directory(config_dir)

        Using a custom catalog with default validator:

        >>> from myproject.catalogs import S3DataCatalog
        >>> catalog = ValidatedDataCatalog.in_directory("config/data", catalog_class=S3DataCatalog)
        >>> # Uses S3DataCatalog for I/O, GXValidator for validation

        Using a custom validator with default catalog:

        >>> from adc_toolkit.data.validators.pandera import PanderaValidator
        >>> catalog = ValidatedDataCatalog.in_directory("config/data", validator_class=PanderaValidator)
        >>> # Uses KedroDataCatalog for I/O, PanderaValidator for validation

        Using custom catalog and validator:

        >>> from myproject.catalogs import DatabaseCatalog
        >>> from myproject.validators import CustomValidator
        >>> catalog = ValidatedDataCatalog.in_directory(
        ...     "config/data", catalog_class=DatabaseCatalog, validator_class=CustomValidator
        ... )

        Disabling validation for performance-critical scenarios:

        >>> from adc_toolkit.data.validators.no_validator import NoValidator
        >>> catalog = ValidatedDataCatalog.in_directory("config/data", validator_class=NoValidator)
        >>> # No validation overhead, useful for trusted data sources

        Different configurations for different environments:

        >>> # Development: use local files with strict validation
        >>> dev_catalog = ValidatedDataCatalog.in_directory("config/dev")
        >>>
        >>> # Production: use cloud storage with the same validation
        >>> prod_catalog = ValidatedDataCatalog.in_directory("config/prod")
        >>>
        >>> # Testing: use in-memory catalog with no validation
        >>> from unittest.mock import Mock
        >>> test_catalog = ValidatedDataCatalog.in_directory("config/test", validator_class=NoValidator)

        Complete workflow example:

        >>> import pandas as pd
        >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
        >>>
        >>> # Initialize catalog from configuration
        >>> catalog = ValidatedDataCatalog.in_directory("config/pipeline")
        >>>
        >>> # Load raw data (validated on load)
        >>> raw = catalog.load("raw_transactions")
        >>>
        >>> # Process data
        >>> cleaned = raw.dropna()
        >>> features = engineer_features(cleaned)
        >>>
        >>> # Save results (validated before save)
        >>> catalog.save("cleaned_transactions", cleaned)
        >>> catalog.save("feature_matrix", features)
        """
        catalog = catalog_class.in_directory(path) if catalog_class else default_catalog(path)
        validator = validator_class.in_directory(path) if validator_class else default_validator(path)
        return cls(catalog, validator)

    def load(self, name: str, **kwargs: Any) -> Data:
        """
        Load a dataset from the catalog and validate it.

        This method performs a two-step operation:
        1. Load the dataset using the underlying catalog's load() method
        2. Validate the loaded dataset using the validator's validate() method

        The validation step ensures that the loaded data meets all configured
        quality expectations before being returned to the caller. If validation
        fails, an exception is raised and no data is returned.

        This provides a safety guarantee: any data returned from load() has
        been validated and can be trusted to meet the configured expectations.

        Parameters
        ----------
        name : str
            The registered name of the dataset to load. This name must be
            defined in both the catalog configuration (for loading) and the
            validator configuration (for validation rules). The name serves
            as the lookup key for both components.
        **kwargs : Any
            Additional keyword arguments passed through to the underlying
            catalog's load() method. The supported arguments depend on the
            catalog implementation. Common examples include:
            - version: str - Load a specific version of the dataset
            - load_args: dict - Override default load arguments
            - credentials: dict - Override default credentials
            Consult your catalog implementation's documentation for details.

        Returns
        -------
        Data
            The loaded and validated dataset. The specific type depends on
            the catalog configuration (e.g., pandas.DataFrame,
            pyspark.sql.DataFrame). The returned data has passed all
            validation checks configured for this dataset name.

        Raises
        ------
        KeyError
            If the dataset name is not registered in the catalog or validator
            configuration.
        FileNotFoundError
            If the dataset's source file or location does not exist.
        ValidationError
            If the loaded data fails validation. The exception includes details
            about which validation rules failed, expected values, and observed
            values. The specific exception type depends on the validator
            implementation (e.g., great_expectations.exceptions.ValidationError
            for GXValidator, pandera.errors.SchemaError for PanderaValidator).
        ValueError
            If the dataset cannot be loaded due to format errors, parsing
            failures, or incompatible data types.
        TypeError
            If the loaded data type is incompatible with the validator
            expectations.
        PermissionError
            If the dataset source is not readable due to permission issues.

        See Also
        --------
        save : Validate and save a dataset to the catalog.
        in_directory : Factory method for creating catalog instances.
        DataCatalog.load : Underlying catalog load operation.
        DataValidator.validate : Underlying validation operation.

        Notes
        -----
        The load operation is idempotent: calling it multiple times with the
        same name and arguments should return equivalent data (assuming the
        underlying source hasn't changed).

        Validation happens after loading, so the full dataset must be loaded
        into memory before validation can begin. For very large datasets, this
        may have performance implications. Some validator implementations
        support sampling-based validation to mitigate this.

        If validation fails, the loaded data is discarded and not returned.
        This prevents invalid data from propagating through your pipeline.

        The method does not cache loaded data. Each call performs a fresh
        load and validation. If caching is needed, implement it at a higher
        level or use a catalog implementation that supports caching.

        Thread safety depends on the underlying catalog and validator
        implementations. Consult their documentation if concurrent loading
        is required.

        Examples
        --------
        Basic usage:

        >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
        >>> catalog = ValidatedDataCatalog.in_directory("config/data")
        >>> df = catalog.load("customer_data")
        >>> # df is guaranteed to meet all validation rules for "customer_data"
        >>> print(df.columns)
        Index(['customer_id', 'name', 'email', 'signup_date'], dtype='object')

        Loading with additional arguments:

        >>> # Load a specific version
        >>> df_v1 = catalog.load("customer_data", version="2024-01-01")
        >>>
        >>> # Override load arguments
        >>> df_custom = catalog.load("sales_data", load_args={"parse_dates": ["transaction_date"]})

        Handling validation failures:

        >>> try:
        ...     df = catalog.load("strict_dataset")
        ... except Exception as e:
        ...     print(f"Validation failed: {e}")
        ...     # Log the failure, send alert, or handle gracefully
        ...     # The invalid data is not returned

        Loading multiple datasets in a pipeline:

        >>> catalog = ValidatedDataCatalog.in_directory("config/pipeline")
        >>>
        >>> # All datasets are validated on load
        >>> customers = catalog.load("customers")
        >>> orders = catalog.load("orders")
        >>> products = catalog.load("products")
        >>>
        >>> # Merge validated datasets with confidence
        >>> enriched = orders.merge(customers, on="customer_id")
        >>> enriched = enriched.merge(products, on="product_id")

        Using in a data processing function:

        >>> def process_sales_data(catalog: ValidatedDataCatalog) -> pd.DataFrame:
        ...     # Load and validate raw sales data
        ...     sales = catalog.load("raw_sales")
        ...
        ...     # Process with confidence that data meets expectations
        ...     sales["revenue"] = sales["quantity"] * sales["price"]
        ...     sales = sales.groupby("region").agg({"revenue": "sum"})
        ...
        ...     return sales

        Comparing data across environments:

        >>> dev_catalog = ValidatedDataCatalog.in_directory("config/dev")
        >>> prod_catalog = ValidatedDataCatalog.in_directory("config/prod")
        >>>
        >>> # Same dataset name, different sources, same validation
        >>> dev_data = dev_catalog.load("training_data")
        >>> prod_data = prod_catalog.load("training_data")
        >>>
        >>> # Both are guaranteed to have the same schema and quality
        """
        return self.validator.validate(name, self.catalog.load(name, **kwargs))

    def save(self, name: str, data: Data) -> None:
        """
        Validate a dataset and save it to the catalog.

        This method performs a two-step operation:
        1. Validate the dataset using the validator's validate() method
        2. Save the validated dataset using the catalog's save() method

        The validation step ensures that only data meeting all configured
        quality expectations is persisted. If validation fails, an exception
        is raised and no data is saved.

        This provides a safety guarantee: any data saved via this method has
        been validated and meets the configured expectations. Invalid data
        is prevented from entering downstream systems or storage.

        Parameters
        ----------
        name : str
            The registered name of the dataset to save. This name must be
            defined in both the catalog configuration (for saving location
            and format) and the validator configuration (for validation rules).
            The name serves as the lookup key for both components.
        data : Data
            The dataset to validate and save. Must be a Data protocol-compatible
            object (e.g., pandas.DataFrame, pyspark.sql.DataFrame) that has
            'columns' and 'dtypes' properties. The data must satisfy all
            validation rules configured for this dataset name.

        Returns
        -------
        None
            This method does not return a value. It performs a side effect
            (saving data) after successful validation.

        Raises
        ------
        KeyError
            If the dataset name is not registered in the catalog or validator
            configuration.
        ValidationError
            If the data fails validation. The exception includes details about
            which validation rules failed, expected values, and observed values.
            No data is saved when validation fails. The specific exception type
            depends on the validator implementation (e.g.,
            great_expectations.exceptions.ValidationError for GXValidator,
            pandera.errors.SchemaError for PanderaValidator).
        TypeError
            If the data type is incompatible with the catalog's save operation
            or the validator's expectations.
        ValueError
            If the data cannot be saved due to format errors or serialization
            failures.
        PermissionError
            If the target save location is not writable.
        OSError
            If there are filesystem errors during the save operation (e.g.,
            disk full, path too long).

        See Also
        --------
        load : Load and validate a dataset from the catalog.
        in_directory : Factory method for creating catalog instances.
        DataCatalog.save : Underlying catalog save operation.
        DataValidator.validate : Underlying validation operation.

        Notes
        -----
        Validation happens before saving, so invalid data is never persisted.
        This is crucial for maintaining data quality in downstream systems.

        The save operation should be atomic when possible: either the entire
        dataset is saved successfully, or no partial data is written. Atomicity
        depends on the catalog implementation and underlying storage system.

        Some catalog implementations support versioning, automatically creating
        timestamped or numbered versions of saved datasets. Consult your catalog
        documentation for details.

        If the target file or location already exists, the behavior depends on
        the catalog configuration. Common options include:
        - Overwrite: Replace existing data (default for most catalogs)
        - Append: Add to existing data
        - Error: Raise an exception if target exists
        - Version: Create a new version without overwriting

        For very large datasets, validation may have performance implications
        as the entire dataset must be validated before saving begins. Some
        validator implementations support sampling-based validation.

        Thread safety depends on the underlying catalog and validator
        implementations. Consult their documentation if concurrent saving
        is required.

        The method does not modify the input data object. Validation may
        internally create temporary copies or views, but the original data
        parameter is unchanged.

        Examples
        --------
        Basic usage:

        >>> import pandas as pd
        >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
        >>>
        >>> catalog = ValidatedDataCatalog.in_directory("config/data")
        >>> df = pd.DataFrame(
        ...     {
        ...         "customer_id": [1, 2, 3],
        ...         "name": ["Alice", "Bob", "Carol"],
        ...         "email": ["alice@ex.com", "bob@ex.com", "carol@ex.com"],
        ...     }
        ... )
        >>> catalog.save("customer_data", df)
        >>> # Data is validated before saving; only valid data is persisted

        Handling validation failures:

        >>> invalid_df = pd.DataFrame({"wrong_column": [1, 2, 3]})
        >>> try:
        ...     catalog.save("customer_data", invalid_df)
        ... except Exception as e:
        ...     print(f"Validation failed: {e}")
        ...     # Invalid data is not saved; downstream systems protected

        Saving multiple datasets in a pipeline:

        >>> catalog = ValidatedDataCatalog.in_directory("config/pipeline")
        >>>
        >>> # Process and save intermediate results
        >>> raw = catalog.load("raw_transactions")
        >>> cleaned = raw.dropna()
        >>> catalog.save("cleaned_transactions", cleaned)
        >>>
        >>> # Further processing
        >>> features = engineer_features(cleaned)
        >>> catalog.save("feature_matrix", features)
        >>>
        >>> # Final output
        >>> predictions = model.predict(features)
        >>> catalog.save("predictions", predictions)

        Complete validation workflow:

        >>> from adc_toolkit.data.catalog import ValidatedDataCatalog
        >>>
        >>> catalog = ValidatedDataCatalog.in_directory("config/production")
        >>>
        >>> # Load validated input
        >>> input_data = catalog.load("input_dataset")
        >>>
        >>> # Transform data
        >>> output_data = transform(input_data)
        >>>
        >>> # Save with validation
        >>> try:
        ...     catalog.save("output_dataset", output_data)
        ... except Exception as e:
        ...     # Validation failed; investigate and fix transformation
        ...     logger.error(f"Output validation failed: {e}")
        ...     # Original input_data is still available for debugging
        ...     raise

        Using save in a reusable processing function:

        >>> def aggregate_sales(catalog: ValidatedDataCatalog, input_name: str, output_name: str) -> None:
        ...     # Load validated data
        ...     sales = catalog.load(input_name)
        ...
        ...     # Aggregate
        ...     aggregated = sales.groupby("region").agg({"revenue": "sum", "quantity": "sum"})
        ...
        ...     # Save validated output
        ...     catalog.save(output_name, aggregated)
        >>>
        >>> catalog = ValidatedDataCatalog.in_directory("config/data")
        >>> aggregate_sales(catalog, "daily_sales", "monthly_sales")

        Preventing invalid data from reaching production:

        >>> # Development environment - experimenting with new features
        >>> dev_catalog = ValidatedDataCatalog.in_directory("config/dev")
        >>> experimental_df = create_new_features(raw_data)
        >>>
        >>> try:
        ...     dev_catalog.save("feature_matrix", experimental_df)
        ... except Exception as e:
        ...     print(f"New features don't meet schema: {e}")
        ...     # Fix the feature engineering before deploying to production
        >>>
        >>> # Production environment - same validation rules enforced
        >>> prod_catalog = ValidatedDataCatalog.in_directory("config/prod")
        >>> prod_catalog.save("feature_matrix", experimental_df)
        >>> # Only succeeds if data meets production quality standards

        Saving with different formats via catalog configuration:

        >>> # Catalog configuration determines format (CSV, Parquet, etc.)
        >>> catalog = ValidatedDataCatalog.in_directory("config/data")
        >>>
        >>> # Same save() call, different formats based on catalog config
        >>> catalog.save("csv_output", df)  # Saved as CSV
        >>> catalog.save("parquet_output", df)  # Saved as Parquet
        >>> catalog.save("database_table", df)  # Saved to database
        >>> # All validated before saving regardless of format
        """
        self.catalog.save(name, self.validator.validate(name, data))
