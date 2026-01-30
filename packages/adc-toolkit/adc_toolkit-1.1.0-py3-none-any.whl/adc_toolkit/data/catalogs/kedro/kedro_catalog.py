"""
Kedro-based data catalog implementation.

This module provides a Kedro-based implementation of the DataCatalog protocol,
enabling configuration-driven data I/O operations using Kedro's data catalog
system. The implementation supports YAML-based dataset definitions, multiple
file formats, cloud storage backends, and dynamic SQL queries.

The KedroDataCatalog wraps Kedro's native DataCatalog to provide a simplified
interface that integrates seamlessly with the adc-toolkit's data validation
and processing pipeline.

Classes
-------
KedroDataCatalog
    Main Kedro catalog implementation with factory methods for instantiation
    and scaffolding.

See Also
--------
adc_toolkit.data.abs.DataCatalog : Protocol definition for data catalogs.
adc_toolkit.data.validated_catalog.ValidatedDataCatalog : Catalog with validation.
kedro.io.DataCatalog : Underlying Kedro catalog implementation.

Notes
-----
The Kedro data catalog system uses YAML configuration files to define datasets,
including their file paths, formats, and load/save parameters. This approach
separates data I/O concerns from business logic and enables environment-specific
configurations.

Configuration files should be organized in a directory structure:
- base/catalog.yml: Base dataset definitions
- base/globals.yml: Global variables (e.g., base_path)
- local/catalog.yml: Local overrides (not committed to version control)
- local/credentials.yml: Credentials (not committed to version control)

References
----------
.. [1] Kedro Documentation: Data Catalog
   https://docs.kedro.org/en/stable/data/data_catalog.html

Examples
--------
Basic usage with factory method:

>>> catalog = KedroDataCatalog.in_directory("config/catalog")
>>> data = catalog.load("training_data")
>>> processed = preprocess(data)
>>> catalog.save("processed_data", processed)

Initialize catalog structure:

>>> result = KedroDataCatalog.init_catalog("./config")
>>> print(f"Created {len(result.created_files)} configuration files")

Load data with dynamic SQL query:

>>> catalog = KedroDataCatalog.in_directory("config/catalog")
>>> data = catalog.load("sales_data", year=2024, region="EMEA")
"""

from pathlib import Path
from typing import Any

from kedro.config import AbstractConfigLoader

from adc_toolkit.data.abs import Data
from adc_toolkit.data.catalogs.kedro.kedro_configs import create_catalog, create_omega_config_loader
from adc_toolkit.data.catalogs.kedro.scaffold import (
    ScaffoldResult,
    catalog_structure_exists,
    create_catalog_folder_structure,
)


class KedroDataCatalog:
    """
    Kedro-based implementation of the DataCatalog protocol.

    This class provides a production-ready data catalog using Kedro's DataCatalog
    as the underlying I/O engine. It supports configuration-driven dataset management
    through YAML files, enabling declarative definitions of data sources, file formats,
    load/save parameters, and storage backends.

    The catalog handles diverse data formats (CSV, Parquet, JSON, Excel, Pickle, HDF5),
    storage locations (local filesystem, S3, GCS, Azure Blob), and advanced features
    like versioning, partitioning, and dynamic SQL queries.

    Parameters
    ----------
    config_path : str or pathlib.Path
        Path to the configuration directory containing catalog YAML files.
        The directory should contain base/ and local/ subdirectories with
        catalog.yml, globals.yml, and optionally credentials.yml files.
    config_loader : kedro.config.AbstractConfigLoader or None, default=None
        Kedro configuration loader instance. If None, an OmegaConfigLoader
        will be created automatically to load YAML configurations from the
        config_path directory.

    Attributes
    ----------
    config_path : str
        Path to the configuration directory as a string.
    config_loader : kedro.config.AbstractConfigLoader
        The configuration loader instance used to read YAML files.
    _catalog : kedro.io.DataCatalog
        Internal Kedro DataCatalog instance handling actual I/O operations.

    Methods
    -------
    load(name, **query_args)
        Load a dataset by name from the catalog.
    save(name, data)
        Save a dataset by name to the catalog.
    in_directory(path)
        Factory method to create a catalog from a configuration directory.
    init_catalog(path, overwrite=False, include_globals=True, ...)
        Create the Kedro catalog folder structure with template files.

    Raises
    ------
    FileNotFoundError
        If the configuration directory does not exist or the catalog structure
        is incomplete (missing required base/ or local/ directories).

    See Also
    --------
    adc_toolkit.data.abs.DataCatalog : Protocol definition for data catalogs.
    adc_toolkit.data.validated_catalog.ValidatedDataCatalog : Catalog with validation.
    kedro.io.DataCatalog : Underlying Kedro catalog implementation.
    kedro.config.OmegaConfigLoader : Default configuration loader.

    Notes
    -----
    The catalog expects a specific directory structure:

    config_path/
        base/
            catalog.yml      # Base dataset definitions
            globals.yml      # Global variables and parameters
        local/
            catalog.yml      # Local overrides (gitignored)
            credentials.yml  # Credentials (gitignored)

    Dataset definitions in catalog.yml follow Kedro's format:

    .. code-block:: yaml

        dataset_name:
          type: pandas.CSVDataset
          filepath: data/raw/dataset.csv
          load_args:
            sep: ","
          save_args:
            index: False

    The catalog supports versioning, which automatically timestamps saved datasets
    and allows loading specific versions. Partitioning enables splitting large
    datasets into multiple files for parallel processing.

    For SQL datasets, the catalog supports dynamic query parameters that can be
    provided at load time using the query_args keyword arguments.

    Thread Safety
    -------------
    The KedroDataCatalog delegates to Kedro's DataCatalog, which is not thread-safe
    for concurrent writes to the same dataset. Concurrent reads are safe.

    References
    ----------
    .. [1] Kedro Documentation: Data Catalog
       https://docs.kedro.org/en/stable/data/data_catalog.html
    .. [2] Kedro Documentation: Configuration
       https://docs.kedro.org/en/stable/configuration/configuration_basics.html

    Examples
    --------
    Create a catalog using the factory method:

    >>> catalog = KedroDataCatalog.in_directory("config/catalog")
    >>> df = catalog.load("customer_data")
    >>> df.columns
    Index(['customer_id', 'name', 'email', 'signup_date'], dtype='object')

    Save processed data:

    >>> processed_df = process_customers(df)
    >>> catalog.save("processed_customers", processed_df)

    Load data with dynamic SQL query parameters:

    >>> # catalog.yml defines: SELECT * FROM sales WHERE year={year} AND region='{region}'
    >>> sales = catalog.load("sales_data", year=2024, region="EMEA")
    >>> sales.shape
    (15420, 8)

    Create a catalog with custom config loader:

    >>> from kedro.config import OmegaConfigLoader
    >>> loader = OmegaConfigLoader(conf_source="config", env="production", base_env="base", default_run_env="local")
    >>> catalog = KedroDataCatalog("config/catalog", config_loader=loader)

    Initialize a new catalog structure:

    >>> result = KedroDataCatalog.init_catalog(
    ...     "./my_project/config", include_globals=True, include_catalog=True, include_credentials=True
    ... )
    >>> print(f"Created: {[f.name for f in result.created_files]}")
    Created: ['catalog.yml', 'globals.yml', 'credentials.yml']
    """

    def __init__(
        self,
        config_path: str | Path,
        config_loader: AbstractConfigLoader | None = None,
    ) -> None:
        """
        Initialize a Kedro data catalog from configuration files.

        This constructor creates a new catalog instance by reading dataset
        definitions from YAML configuration files in the specified directory.
        It validates that the required directory structure exists and creates
        the underlying Kedro DataCatalog.

        Parameters
        ----------
        config_path : str or pathlib.Path
            Path to the configuration directory containing catalog definitions.
            The directory must contain base/ and local/ subdirectories with
            the required YAML files (catalog.yml at minimum).
        config_loader : kedro.config.AbstractConfigLoader or None, default=None
            Kedro configuration loader for reading YAML files. If None, an
            OmegaConfigLoader will be created automatically with default settings
            (base_env="base", default_run_env="local").

        Raises
        ------
        FileNotFoundError
            If the configuration directory does not exist. The error message
            includes instructions for creating the directory structure using
            the CLI command or the ``init_catalog`` class method.
        FileNotFoundError
            If the catalog structure is incomplete (missing base/ or local/
            directories or required catalog.yml files). The error message
            includes instructions for creating the complete structure.

        See Also
        --------
        in_directory : Factory method for creating catalog instances.
        init_catalog : Class method for scaffolding catalog directory structure.

        Notes
        -----
        The constructor performs the following steps:
        1. Validates that the config_path directory exists
        2. Checks for required catalog structure (base/ and local/ directories)
        3. Creates or uses the provided config_loader
        4. Loads catalog configuration and creates the Kedro DataCatalog

        The catalog structure validation requires:
        - base/ directory with catalog.yml
        - local/ directory (can be empty initially)

        Credentials are optional and should be placed in local/credentials.yml
        to prevent accidental commits to version control.

        Examples
        --------
        Create a catalog with default configuration loader:

        >>> catalog = KedroDataCatalog("config/catalog")
        >>> catalog.config_path
        'config/catalog'

        Create a catalog with custom configuration loader:

        >>> from kedro.config import OmegaConfigLoader
        >>> loader = OmegaConfigLoader(conf_source="config", env="staging", base_env="base", default_run_env="local")
        >>> catalog = KedroDataCatalog("config/catalog", config_loader=loader)

        Handle missing configuration directory:

        >>> try:
        ...     catalog = KedroDataCatalog("nonexistent/path")
        ... except FileNotFoundError as e:
        ...     print("Directory not found. Run init_catalog to create it.")
        Directory not found. Run init_catalog to create it.
        """
        self.config_path = str(config_path)
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Configuration directory not found: {config_path}\n"
                f"To create the catalog folder structure, run:\n"
                f"  adc-toolkit init-catalog {config_path}\n"
                f"Or use the class method:\n"
                f"  KedroDataCatalog.init_catalog('{config_path}')"
            )

        if not catalog_structure_exists(config_path, require_credentials=False):
            raise FileNotFoundError(
                f"Catalog structure is incomplete at: {path}\n"
                f"Missing required files in base/ or local/.\n"
                f"To create the catalog folder structure, run:\n"
                f"  adc-toolkit init-catalog {config_path}\n"
                f"Or use the class method:\n"
                f"  KedroDataCatalog.init_catalog('{config_path}')"
            )

        self.config_loader = config_loader
        if not self.config_loader:
            self.config_loader = create_omega_config_loader(self.config_path)
        self._catalog = create_catalog(self.config_loader)

    @classmethod
    def in_directory(cls, path: str | Path) -> "KedroDataCatalog":
        """
        Create a catalog instance from a configuration directory.

        This factory method provides a convenient way to instantiate a
        KedroDataCatalog by specifying only the configuration directory path.
        It is the recommended way to create catalog instances in application code.

        The method creates a catalog with default settings, using an automatically
        configured OmegaConfigLoader to read YAML files from the directory.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to the configuration directory containing catalog definitions.
            The directory must have the required Kedro catalog structure with
            base/ and local/ subdirectories.

        Returns
        -------
        KedroDataCatalog
            A new catalog instance configured with datasets from the directory.
            The catalog is immediately ready to load and save data.

        Raises
        ------
        FileNotFoundError
            If the specified directory does not exist or lacks the required
            catalog structure (base/ and local/ directories with catalog.yml).

        See Also
        --------
        __init__ : Constructor with additional configuration options.
        init_catalog : Create the catalog directory structure.

        Notes
        -----
        This factory method is equivalent to calling the constructor with just
        the path parameter:

        >>> catalog = KedroDataCatalog(path)

        However, using ``in_directory`` is preferred because:
        - It matches the DataCatalog protocol interface
        - It provides better semantic clarity
        - It enables polymorphism when using multiple catalog implementations

        The method uses default configuration settings:
        - Base environment: "base"
        - Default run environment: "local"
        - Configuration format: YAML

        For advanced configuration needs (custom environments, config merging
        strategies, runtime parameters), use the constructor directly with a
        custom AbstractConfigLoader.

        Examples
        --------
        Basic usage:

        >>> catalog = KedroDataCatalog.in_directory("config/catalog")
        >>> df = catalog.load("training_data")

        Using pathlib.Path:

        >>> from pathlib import Path
        >>> config_dir = Path("config") / "catalog"
        >>> catalog = KedroDataCatalog.in_directory(config_dir)

        Load and save in a pipeline:

        >>> catalog = KedroDataCatalog.in_directory("./config")
        >>> raw = catalog.load("raw_data")
        >>> processed = transform(raw)
        >>> catalog.save("processed_data", processed)

        Polymorphic usage with DataCatalog protocol:

        >>> def run_pipeline(catalog: DataCatalog) -> None:
        ...     data = catalog.load("input")
        ...     result = process(data)
        ...     catalog.save("output", result)
        >>> catalog = KedroDataCatalog.in_directory("config/catalog")
        >>> run_pipeline(catalog)
        """
        return cls(path)

    @classmethod
    def init_catalog(
        cls,
        path: str | Path,
        *,
        overwrite: bool = False,
        include_globals: bool = True,
        include_catalog: bool = True,
        include_credentials: bool = True,
    ) -> ScaffoldResult:
        """
        Create Kedro catalog directory structure with template configuration files.

        This class method scaffolds a complete Kedro catalog configuration directory
        with the required folder structure and template YAML files. It is intended
        for initializing new projects or adding catalog functionality to existing
        projects.

        The method creates a directory structure following Kedro conventions:

        - path/base/catalog.yml: Base dataset definitions
        - path/base/globals.yml: Global variables and parameters
        - path/local/catalog.yml: Local environment overrides
        - path/local/credentials.yml: Credentials (should be gitignored)

        Template files include helpful comments and examples to guide configuration.

        Parameters
        ----------
        path : str or pathlib.Path
            Root path for the configuration directory. The directory will be
            created if it doesn't exist. Subdirectories base/ and local/ will
            be created within this path.
        overwrite : bool, default=False
            If True, overwrite existing files at the destination paths. If False,
            existing files are preserved and reported in skipped_files. Use with
            caution to avoid losing custom configurations.
        include_globals : bool, default=True
            If True, create base/globals.yml with template global variables.
            Global variables can be referenced in catalog.yml using ${variable}
            syntax for parameterization.
        include_catalog : bool, default=True
            If True, create base/catalog.yml and local/catalog.yml with template
            dataset definitions. These files are essential for catalog operation.
        include_credentials : bool, default=True
            If True, create local/credentials.yml for storing credentials. This
            file should be added to .gitignore to prevent committing secrets.

        Returns
        -------
        ScaffoldResult
            A result object containing:
            - created_files: List of Path objects for files that were created
            - skipped_files: List of Path objects for files that already existed
            - created_directories: List of Path objects for directories created

        See Also
        --------
        in_directory : Factory method to create catalog from existing config.
        adc_toolkit.data.catalogs.kedro.scaffold.create_catalog_folder_structure :
            Underlying scaffolding function.

        Notes
        -----
        The scaffolded directory structure follows Kedro best practices:

        - **base/**: Contains base configurations shared across environments
        - **local/**: Contains local overrides and credentials (gitignored)

        Template catalog.yml includes examples for common dataset types:
        - CSV files with pandas.CSVDataset
        - Parquet files with pandas.ParquetDataset
        - Excel files with pandas.ExcelDataset
        - Pickle files with pickle.PickleDataset

        Template globals.yml includes examples for:
        - Base paths (data directories)
        - Common parameters (date formats, separators)
        - Environment-specific settings

        After running this method, you should:
        1. Review and customize the generated YAML files
        2. Add local/credentials.yml to .gitignore
        3. Define your project-specific datasets in base/catalog.yml
        4. Add environment-specific overrides in local/catalog.yml

        This is equivalent to running the CLI command:
        ``adc-toolkit init-catalog <path>``

        Examples
        --------
        Initialize a catalog in a new project:

        >>> result = KedroDataCatalog.init_catalog("./config/catalog")
        >>> print(f"Created {len(result.created_files)} files")
        Created 4 files
        >>> print(f"Directories: {[d.name for d in result.created_directories]}")
        Directories: ['base', 'local']

        Initialize with selective templates:

        >>> result = KedroDataCatalog.init_catalog(
        ...     "./config/catalog",
        ...     include_globals=True,
        ...     include_catalog=True,
        ...     include_credentials=False,  # No credentials needed
        ... )

        Reinitialize with overwrite (use carefully):

        >>> result = KedroDataCatalog.init_catalog(
        ...     "./config/catalog",
        ...     overwrite=True,  # Overwrites existing files
        ... )

        Check what was created vs. skipped:

        >>> result = KedroDataCatalog.init_catalog("./config/catalog")
        >>> if result.skipped_files:
        ...     print(f"Skipped existing: {[f.name for f in result.skipped_files]}")
        ... if result.created_files:
        ...     print(f"Created new: {[f.name for f in result.created_files]}")

        Use in project setup script:

        >>> from pathlib import Path
        >>> project_root = Path("./my_project")
        >>> catalog_dir = project_root / "config" / "catalog"
        >>> result = KedroDataCatalog.init_catalog(catalog_dir)
        >>> assert catalog_dir.exists()
        >>> assert (catalog_dir / "base" / "catalog.yml").exists()
        """
        return create_catalog_folder_structure(
            path,
            overwrite=overwrite,
            include_globals=include_globals,
            include_catalog=include_catalog,
            include_credentials=include_credentials,
        )

    def load(self, name: str, **query_args: Any) -> Data:
        """
        Load a dataset by name from the catalog.

        Retrieve a dataset using its registered name as defined in the catalog
        configuration files. The method handles all I/O operations, file format
        parsing, and type conversions based on the dataset's configuration.

        For SQL-based datasets with parameterized queries, this method supports
        dynamic query parameter substitution through keyword arguments, enabling
        flexible data filtering and selection at load time.

        Parameters
        ----------
        name : str
            The registered name of the dataset to load. This name must match
            a dataset definition in the catalog configuration files (catalog.yml).
        **query_args : Any
            Keyword arguments for dynamic SQL query parameterization. Only
            applicable to SQL-based datasets with parameterized queries using
            Python format string syntax (e.g., WHERE year={year}). For non-SQL
            datasets, query_args are ignored.

        Returns
        -------
        Data
            The loaded dataset as a Data protocol-compatible object. The specific
            type depends on the dataset configuration (typically pandas.DataFrame,
            but can be Spark DataFrame, numpy array, or other types defined in
            the catalog).

        Raises
        ------
        KeyError
            If no dataset with the given name is registered in the catalog.
        FileNotFoundError
            If the dataset's source file or database does not exist.
        ValueError
            If the dataset cannot be loaded due to format errors, parsing errors,
            or invalid query_args for datasets that don't support queries.
        PermissionError
            If the dataset's source file or database is not readable.

        See Also
        --------
        save : Save a dataset to the catalog.
        _load_with_dynamic_query : Internal method for parameterized SQL queries.

        Notes
        -----
        Load behavior depends on the dataset type configured in catalog.yml:

        - **File-based datasets** (CSV, Parquet, JSON, Excel, Pickle, HDF5):
          Reads from the configured filepath using the specified load_args.

        - **Database datasets** (SQL, SQLQuery, SQLTable): Executes queries
          or reads tables from the configured database connection.

        - **Versioned datasets**: Loads the latest version unless a specific
          version is requested in the configuration.

        - **Partitioned datasets**: Loads and concatenates all partitions.

        For SQL datasets with dynamic queries, the query string in catalog.yml
        should use Python format string syntax with named placeholders:

        .. code-block:: yaml

            sales_data:
              type: pandas.SQLQueryDataset
              sql: SELECT * FROM sales WHERE year={year} AND region='{region}'
              credentials: database_creds

        Query parameters are substituted at load time:

        >>> df = catalog.load("sales_data", year=2024, region="EMEA")

        The load operation is idempotent: calling it multiple times with the
        same parameters returns equivalent data (though not necessarily the
        same object instance).

        Performance Considerations
        --------------------------
        - Large datasets may take significant time and memory to load
        - For large files, consider using chunking or lazy loading
        - Cloud storage (S3, GCS, Azure) may incur network latency
        - Partitioned datasets are loaded in parallel when possible

        Examples
        --------
        Load a simple dataset:

        >>> catalog = KedroDataCatalog.in_directory("config/catalog")
        >>> df = catalog.load("customer_data")
        >>> df.shape
        (10000, 8)

        Load with dynamic SQL query parameters:

        >>> # catalog.yml: sql: "SELECT * FROM sales WHERE year={year} AND region='{region}'"
        >>> sales_2024 = catalog.load("sales_data", year=2024, region="EMEA")
        >>> sales_2024["year"].unique()
        array([2024])
        >>> sales_2024["region"].unique()
        array(['EMEA'], dtype=object)

        Load multiple datasets in sequence:

        >>> raw = catalog.load("raw_data")
        >>> features = catalog.load("feature_set")
        >>> model = catalog.load("trained_model")

        Handle missing datasets gracefully:

        >>> try:
        ...     data = catalog.load("nonexistent_dataset")
        ... except KeyError as e:
        ...     print(f"Dataset not found: {e}")
        ...     # Use default data or prompt user
        Dataset not found: 'nonexistent_dataset'

        Load with different query parameters:

        >>> q1_data = catalog.load("sales_data", quarter=1, year=2024)
        >>> q2_data = catalog.load("sales_data", quarter=2, year=2024)
        """
        if query_args:
            return self._load_with_dynamic_query(name, **query_args)
        return self._catalog.load(name)

    def save(self, name: str, data: Data) -> None:
        """
        Save a dataset by name to the catalog.

        Store a dataset using its registered name as defined in the catalog
        configuration files. The method handles all I/O operations, file format
        serialization, and storage operations based on the dataset's configuration.

        Parameters
        ----------
        name : str
            The registered name of the dataset to save. This name must match
            a dataset definition in the catalog configuration files (catalog.yml).
            The dataset configuration determines the output location, format,
            and serialization parameters.
        data : Data
            The dataset to save. Must be a Data protocol-compatible object
            (e.g., pandas.DataFrame, Spark DataFrame) that is compatible with
            the dataset type specified in the catalog configuration.

        Returns
        -------
        None

        Raises
        ------
        KeyError
            If no dataset with the given name is registered in the catalog.
        TypeError
            If the data type is incompatible with the dataset configuration
            (e.g., attempting to save a DataFrame to a PickleDataset expecting
            a different object type).
        ValueError
            If the dataset cannot be saved due to validation errors, format
            incompatibilities, or invalid configuration.
        PermissionError
            If the target location is not writable due to filesystem permissions.
        OSError
            If disk space is insufficient or other I/O errors occur during save.

        See Also
        --------
        load : Load a dataset from the catalog.

        Notes
        -----
        Save behavior depends on the dataset type configured in catalog.yml:

        - **File-based datasets** (CSV, Parquet, JSON, Excel, Pickle, HDF5):
          Writes to the configured filepath using the specified save_args.
          Parent directories are created automatically if they don't exist.

        - **Database datasets** (SQL, SQLTable): Writes to the configured
          database table using the specified connection and save parameters.

        - **Versioned datasets**: Creates a new timestamped version rather
          than overwriting. Version format: filepath/YYYY-MM-DDTHH.mm.ss.sssZ/

        - **Partitioned datasets**: Splits data across multiple files based
          on partitioning configuration.

        The save operation typically overwrites existing data at the target
        location unless versioning is enabled. For versioned datasets, each
        save creates a new version without removing previous versions.

        Format-Specific Behavior
        ------------------------
        Different formats have different save characteristics:

        - **CSV**: Human-readable, widely compatible, larger file size
        - **Parquet**: Columnar format, compressed, efficient for analytics
        - **Pickle**: Python-specific, preserves exact objects, version-sensitive
        - **JSON**: Human-readable, good for nested structures
        - **HDF5**: Binary format, good for large numerical arrays

        Atomicity and Error Handling
        -----------------------------
        The atomicity of save operations depends on the underlying dataset type
        and storage backend:

        - Local filesystem writes may be atomic for small files
        - Cloud storage (S3, GCS, Azure) uses multi-part uploads
        - Database writes depend on transaction support
        - Partitioned saves may be partially successful

        If a save operation fails partway through, partial data may be written.
        For critical applications, consider implementing save-to-temporary-then-move
        patterns or using versioned datasets.

        Performance Considerations
        --------------------------
        - Large datasets may take significant time to serialize and write
        - Cloud storage uploads may have network latency and bandwidth limits
        - Compression (enabled in save_args) trades CPU time for disk space
        - Partitioned datasets can write partitions in parallel

        Examples
        --------
        Save a processed dataset:

        >>> catalog = KedroDataCatalog.in_directory("config/catalog")
        >>> processed_df = process_data(raw_df)
        >>> catalog.save("processed_data", processed_df)

        Save multiple datasets in a pipeline:

        >>> catalog = KedroDataCatalog.in_directory("config/catalog")
        >>> raw = catalog.load("raw_data")
        >>> cleaned = clean_data(raw)
        >>> catalog.save("cleaned_data", cleaned)
        >>> features = engineer_features(cleaned)
        >>> catalog.save("features", features)
        >>> predictions = model.predict(features)
        >>> catalog.save("predictions", predictions)

        Save with versioning (configured in catalog.yml):

        >>> # catalog.yml:
        >>> #   versioned_output:
        >>> #     type: pandas.CSVDataset
        >>> #     filepath: data/output.csv
        >>> #     versioned: true
        >>> catalog.save("versioned_output", result_df)
        >>> # Saves to: data/output.csv/2024-01-15T10.30.45.123Z/output.csv

        Handle save errors:

        >>> try:
        ...     catalog.save("output_data", large_df)
        ... except PermissionError as e:
        ...     print(f"Cannot write to output location: {e}")
        ... except OSError as e:
        ...     print(f"I/O error during save: {e}")

        Save to different formats (configured per dataset):

        >>> # Same data, different formats for different use cases
        >>> catalog.save("output_csv", df)  # Human-readable
        >>> catalog.save("output_parquet", df)  # Efficient storage
        >>> catalog.save("output_json", df)  # API consumption
        """
        self._catalog.save(name, data)

    def _load_with_dynamic_query(self, name: str, **query_args: Any) -> Data:
        """
        Load data from the catalog with dynamic SQL query parameterization.

        This internal method implements dynamic query parameter substitution for
        SQL-based datasets. It temporarily modifies the dataset's query string
        by substituting format placeholders with provided arguments, executes
        the load operation, then restores the original query template.

        Parameters
        ----------
        name : str
            The registered name of the SQL dataset to load. The dataset must
            be configured with a parameterized query using Python format string
            syntax (e.g., SELECT * FROM table WHERE id={id}).
        **query_args : Any
            Keyword arguments providing values for query parameters. Keys must
            match the placeholder names in the query template. Values are
            substituted using Python's str.format() method.

        Returns
        -------
        Data
            The loaded dataset with the parameterized query applied. The return
            type depends on the dataset configuration (typically pandas.DataFrame
            for SQL datasets).

        Raises
        ------
        ValueError
            If the dataset does not support queries (i.e., the dataset
            configuration does not include a 'query' parameter in load_args),
            or if query parameter substitution fails due to format string errors.
        KeyError
            If query_args are missing required parameters referenced in the
            query template, or if the dataset name is not registered.

        See Also
        --------
        load : Public method that delegates to this internal method when query_args provided.

        Notes
        -----
        This method directly manipulates the internal Kedro DataCatalog's dataset
        configuration by:
        1. Accessing the dataset's _load_args dictionary
        2. Extracting the query template string
        3. Substituting placeholders with provided arguments using str.format()
        4. Loading data with the substituted query
        5. Restoring the original query template for subsequent loads

        The query restoration ensures that the catalog remains stateless and
        multiple calls with different parameters don't interfere with each other.

        Query Parameterization Format
        ------------------------------
        The query template in catalog.yml should use Python format string syntax:

        - Named placeholders: {parameter_name}
        - String parameters need explicit quotes: WHERE name='{name}'
        - Numeric parameters don't need quotes: WHERE id={id}

        Example catalog.yml configuration:

        .. code-block:: yaml

            parameterized_sales:
              type: pandas.SQLQueryDataset
              sql: |
                SELECT * FROM sales
                WHERE year={year}
                  AND region='{region}'
                  AND revenue > {min_revenue}
              credentials: db_credentials

        Security Considerations
        -----------------------
        This method uses Python's str.format() for parameter substitution, which
        does NOT provide SQL injection protection. Use this method only with:

        - Trusted parameter values from application code
        - Validated and sanitized user inputs
        - Internal pipeline parameters

        For user-provided inputs, consider using database-specific parameter
        binding mechanisms instead of string formatting.

        Examples
        --------
        Internal usage by the load method:

        >>> # User calls load with query parameters
        >>> df = catalog.load("sales_data", year=2024, region="EMEA")
        >>> # Internally delegates to _load_with_dynamic_query

        Query template in catalog.yml:

        .. code-block:: yaml

            sales_data:
              type: pandas.SQLQueryDataset
              sql: SELECT * FROM sales WHERE year={year} AND region='{region}'
              credentials: database_creds

        Equivalent direct call (not recommended for users):

        >>> data = catalog._load_with_dynamic_query("sales_data", year=2024, region="EMEA")

        Error when dataset doesn't support queries:

        >>> try:
        ...     catalog._load_with_dynamic_query("csv_dataset", param=123)
        ... except ValueError as e:
        ...     print(e)
        Data set `csv_dataset` does not support queries.
        """
        load_args = self._catalog._datasets[name]._load_args
        if "query" not in load_args:
            raise ValueError(f"Data set `{name}` does not support queries.")

        raw_query = load_args["query"]
        load_args["query"] = raw_query.format(**query_args)
        data = self._catalog.load(name)
        load_args["query"] = raw_query

        return data
