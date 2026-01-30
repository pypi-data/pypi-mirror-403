"""
Kedro configuration utilities for data catalog and credentials management.

This module provides utility functions for creating and managing Kedro
configuration loaders and data catalogs. It supports OmegaConf-based
configuration loading with global variable substitution, SQL query file
resolution, and credentials management.

The primary workflow involves:
1. Creating a configuration loader from a directory structure
2. Loading catalog and credentials configurations
3. Resolving SQL query files referenced in the catalog
4. Instantiating a Kedro DataCatalog for data I/O operations

Functions
---------
create_omega_config_loader(config_path)
    Create an OmegaConfigLoader for Kedro configuration management.
get_catalog_config(config_loader)
    Extract catalog configuration from a config loader.
get_credentials_config(config_loader)
    Extract credentials configuration from a config loader.
create_catalog(config_loader)
    Create a fully configured Kedro DataCatalog instance.

Notes
-----
This module expects a Kedro-style configuration directory structure:

    config/
    ├── base/
    │   ├── catalog.yml          # Dataset definitions
    │   ├── credentials.yml      # Connection credentials (optional)
    │   └── globals.yml          # Global variables for substitution
    └── local/
        ├── catalog.yml          # Local overrides
        └── credentials.yml      # Local credentials (not committed)

The OmegaConfigLoader supports variable interpolation using OmegaConf syntax.
For example, in globals.yml you might define:

    data_dir: /path/to/data

And reference it in catalog.yml:

    my_dataset:
      type: pandas.CSVDataset
      filepath: ${globals:data_dir}/my_file.csv

See Also
--------
kedro.config.OmegaConfigLoader : The underlying Kedro config loader.
kedro.io.DataCatalog : The Kedro data catalog for I/O operations.

Examples
--------
Basic workflow for creating a data catalog from configuration:

>>> from pathlib import Path
>>> config_path = Path("config")
>>> loader = create_omega_config_loader(str(config_path))
>>> catalog = create_catalog(loader)
>>> data = catalog.load("my_dataset")

Advanced workflow with manual configuration access:

>>> loader = create_omega_config_loader("config")
>>> catalog_config = get_catalog_config(loader)
>>> credentials_config = get_credentials_config(loader)
>>> print(f"Found {len(catalog_config)} datasets")
>>> catalog = create_catalog(loader)
"""

import warnings
from pathlib import Path
from typing import Any

from kedro.config import AbstractConfigLoader, MissingConfigException, OmegaConfigLoader
from kedro.io import DataCatalog


def create_omega_config_loader(config_path: str) -> OmegaConfigLoader:
    """
    Create a Kedro OmegaConfigLoader for hierarchical configuration management.

    This function instantiates an OmegaConfigLoader, which is the modern
    replacement for the deprecated TemplatedConfigLoader. It enables
    configuration composition across multiple environments with variable
    interpolation using OmegaConf syntax.

    The loader searches for configuration files in a hierarchical structure:
    1. Base environment (`base/`): Contains default configurations
    2. Runtime environment (`local/`): Contains environment-specific overrides

    Global variables are automatically loaded from any YAML file matching the
    pattern "*globals.yml" (e.g., "globals.yml", "my_globals.yml"). These
    variables can be referenced in other configuration files using the
    interpolation syntax: ${globals:variable_name}.

    Parameters
    ----------
    config_path : str
        Absolute or relative path to the root configuration directory.
        This directory should contain subdirectories for different
        environments (typically `base/` and `local/`).

    Returns
    -------
    OmegaConfigLoader
        A configured instance of Kedro's OmegaConfigLoader ready to load
        configuration files. The loader is set up with:
        - conf_source: The provided config_path
        - base_env: "base" (default configuration directory)
        - default_run_env: "local" (default runtime environment)

    See Also
    --------
    get_catalog_config : Load catalog configuration using the config loader.
    get_credentials_config : Load credentials configuration.
    kedro.config.OmegaConfigLoader : The underlying Kedro configuration class.

    Notes
    -----
    **Configuration Directory Structure**

    The expected directory layout is:

        config_path/
        ├── base/
        │   ├── catalog.yml          # Dataset definitions
        │   ├── credentials.yml      # Credentials (optional)
        │   ├── globals.yml          # Global variables
        │   └── parameters.yml       # Pipeline parameters (optional)
        └── local/
            ├── catalog.yml          # Local dataset overrides
            ├── credentials.yml      # Local credentials
            └── globals.yml          # Local variable overrides

    **Variable Interpolation**

    The OmegaConfigLoader supports OmegaConf's interpolation syntax. Common
    use cases include:

    - Reference global variables: ${globals:data_dir}
    - Reference environment variables: ${oc.env:HOME}
    - Reference other config keys: ${catalog.my_dataset.filepath}
    - Nested interpolation: ${globals:root}/${globals:subdir}

    **Environment Resolution**

    Configuration is resolved in this order:
    1. Load base environment files
    2. Load runtime environment files (default: local)
    3. Merge configurations (runtime overrides base)
    4. Resolve all variable interpolations

    **Migration from TemplatedConfigLoader**

    If migrating from TemplatedConfigLoader:
    - Replace ${variable} with ${globals:variable}
    - Move global variables to a *globals.yml file
    - Update any custom template patterns to OmegaConf syntax

    Examples
    --------
    Create a config loader for a standard Kedro project:

    >>> loader = create_omega_config_loader("config")
    >>> catalog_conf = loader["catalog"]
    >>> credentials_conf = loader["credentials"]

    Create a loader with an absolute path:

    >>> from pathlib import Path
    >>> config_dir = Path.home() / "projects" / "my_project" / "config"
    >>> loader = create_omega_config_loader(str(config_dir))

    Use with different runtime environments:

    >>> loader = create_omega_config_loader("config")
    >>> # Access default environment (local)
    >>> local_catalog = loader["catalog"]
    >>>
    >>> # The loader defaults to 'local' environment
    >>> # To use other environments, configure OmegaConfigLoader directly

    Example globals.yml file:

    >>> # config/base/globals.yml
    >>> # data_root: /opt/data
    >>> # database_host: localhost
    >>> # database_port: 5432
    >>>
    >>> # config/base/catalog.yml
    >>> # raw_data:
    >>> #   type: pandas.CSVDataset
    >>> #   filepath: ${globals:data_root}/raw/data.csv
    >>> #
    >>> # database_connection:
    >>> #   type: pandas.SQLTableDataset
    >>> #   credentials: db_credentials
    >>> #   table_name: my_table

    Example local overrides:

    >>> # config/local/globals.yml
    >>> # data_root: /home/user/local_data  # Override for local development
    >>> # database_host: dev-db-server       # Use different database locally
    """
    return OmegaConfigLoader(
        conf_source=config_path,
        base_env="base",
        default_run_env="local",
    )


def get_catalog_config(
    config_loader: AbstractConfigLoader,
) -> dict[str, dict[str, Any]]:
    """
    Extract and return the catalog configuration from a Kedro config loader.

    This function retrieves the data catalog configuration dictionary from
    a Kedro configuration loader. The catalog configuration defines datasets,
    their types, file paths, connection parameters, and other I/O settings.

    The catalog configuration follows Kedro's DataCatalog specification format,
    where each key is a dataset name and its value is a dictionary containing
    the dataset type, parameters, and optional metadata.

    Parameters
    ----------
    config_loader : AbstractConfigLoader
        A Kedro configuration loader instance (typically OmegaConfigLoader or
        TemplatedConfigLoader) that has access to catalog.yml files in the
        configured environments.

    Returns
    -------
    dict of str to dict of str to any
        A nested dictionary containing the catalog configuration. The structure
        is:
        - Outer keys: Dataset names (str)
        - Inner dictionaries: Dataset parameters including:
            - type: Dataset class (e.g., "pandas.CSVDataset")
            - filepath/sql/table_name/etc.: Location parameters
            - credentials: Reference to credentials (optional)
            - Additional dataset-specific parameters

        Returns an empty dictionary {} if no catalog configuration is found
        or if the catalog configuration is None/empty.

    See Also
    --------
    create_omega_config_loader : Create the config loader to pass to this function.
    get_credentials_config : Get credentials referenced in the catalog.
    create_catalog : Create a DataCatalog from the configuration.
    kedro.io.DataCatalog.from_config : Kedro's method for catalog instantiation.

    Notes
    -----
    **Catalog Configuration Format**

    The catalog.yml file follows this structure:

        dataset_name:
          type: fully.qualified.DataSetClass
          filepath: path/to/file.csv  # or other location parameter
          load_args:
            param1: value1
          save_args:
            param2: value2
          credentials: credential_key  # Optional reference
          metadata:
            description: "Dataset description"

    **Common Dataset Types**

    - pandas.CSVDataset: CSV files
    - pandas.ParquetDataSet: Parquet files
    - pandas.SQLTableDataset: SQL database tables
    - pandas.ExcelDataSet: Excel spreadsheets
    - pickle.PickleDataSet: Pickle files
    - json.JSONDataSet: JSON files

    **Configuration Merging**

    When multiple environments are present (base and local), the config loader
    automatically merges them with local overriding base. This function returns
    the fully merged configuration.

    **SQL Dataset Pattern**

    For SQL datasets, instead of inline SQL strings, you can reference SQL
    files:

        my_query_dataset:
          type: pandas.SQLQueryDataSet
          sql: data/queries/my_query.sql  # Path to SQL file
          credentials: db_credentials

    Use `_replace_sql_with_query()` to resolve these file paths to actual
    query strings.

    Examples
    --------
    Basic usage to inspect catalog configuration:

    >>> loader = create_omega_config_loader("config")
    >>> catalog_config = get_catalog_config(loader)
    >>> print(f"Found {len(catalog_config)} datasets")
    >>> for dataset_name in catalog_config:
    ...     print(f"  - {dataset_name}")

    Access specific dataset configuration:

    >>> loader = create_omega_config_loader("config")
    >>> catalog_config = get_catalog_config(loader)
    >>> raw_data_config = catalog_config.get("raw_data")
    >>> if raw_data_config:
    ...     print(f"Type: {raw_data_config['type']}")
    ...     print(f"Path: {raw_data_config.get('filepath', 'N/A')}")

    Validate all datasets have required keys:

    >>> loader = create_omega_config_loader("config")
    >>> catalog_config = get_catalog_config(loader)
    >>> for name, config in catalog_config.items():
    ...     if "type" not in config:
    ...         print(f"Warning: {name} missing 'type' key")

    Example catalog.yml structure:

    >>> # config/base/catalog.yml
    >>> # iris_data:
    >>> #   type: pandas.CSVDataset
    >>> #   filepath: ${globals:data_dir}/iris.csv
    >>> #   load_args:
    >>> #     sep: ","
    >>> #   save_args:
    >>> #     index: false
    >>> #
    >>> # postgres_table:
    >>> #   type: pandas.SQLTableDataset
    >>> #   table_name: sales_data
    >>> #   credentials: postgres_creds
    >>> #
    >>> # feature_store:
    >>> #   type: pickle.PickleDataSet
    >>> #   filepath: data/06_models/features.pkl
    """
    return config_loader["catalog"] or {}


def _replace_sql_with_query(catalog_config: dict) -> dict[str, dict[str, Any]]:
    """
    Replace SQL file path references with actual query strings from files.

    This internal utility function processes a catalog configuration dictionary
    and replaces any `sql` parameter values that reference file paths with the
    actual SQL query content from those files. This enables storing SQL queries
    in separate .sql files rather than embedding them as strings in YAML
    configuration files.

    The function modifies the input dictionary in-place while also returning
    it for convenience. Only file paths that exist and are readable will be
    replaced; non-existent paths or inline SQL strings are left unchanged.

    Parameters
    ----------
    catalog_config : dict
        A catalog configuration dictionary as returned by `get_catalog_config()`.
        The dictionary has dataset names as keys and parameter dictionaries as
        values. Any dataset configuration with an `sql` key pointing to a valid
        file path will have that path replaced with the file's contents.

    Returns
    -------
    dict of str to dict of str to any
        The same catalog configuration dictionary with SQL file path references
        replaced by their actual query contents. The structure is:
        - Keys: Dataset names (unchanged)
        - Values: Parameter dictionaries with resolved SQL queries

        Note: The input dictionary is modified in-place; the return value
        references the same object.

    See Also
    --------
    get_catalog_config : Retrieve the catalog configuration to pass here.
    create_catalog : Uses this function internally before creating DataCatalog.

    Notes
    -----
    **SQL File Resolution Logic**

    For each dataset in the catalog configuration:
    1. Check if the configuration has an `sql` key
    2. Check if the `sql` value is a valid file path (using Path.is_file())
    3. If both conditions are true, read the file contents and replace the path
    4. If either condition is false, leave the `sql` value unchanged

    **File Path Handling**

    - Relative paths are resolved relative to the current working directory
    - Absolute paths are used as-is
    - The function expects text files with UTF-8 encoding
    - Whitespace and newlines in SQL files are preserved

    **Common Use Cases**

    This pattern is useful for:
    - Version controlling SQL queries separately from configuration
    - Managing complex, multi-line SQL queries
    - Enabling SQL syntax highlighting and linting in IDEs
    - Sharing SQL queries across multiple catalog entries

    **YAML Configuration Pattern**

    Instead of embedding SQL:

        my_query:
          type: pandas.SQLQueryDataSet
          sql: "SELECT * FROM table WHERE date > '2023-01-01'"
          credentials: db_creds

    Reference a SQL file:

        my_query:
          type: pandas.SQLQueryDataSet
          sql: data/queries/my_query.sql  # Path to SQL file
          credentials: db_creds

    **File Organization**

    A typical project structure:

        project/
        ├── config/
        │   └── base/
        │       └── catalog.yml          # References SQL files
        └── data/
            └── queries/
                ├── extract_sales.sql
                ├── aggregate_metrics.sql
                └── join_tables.sql

    **Error Handling**

    The function silently skips entries where:
    - The `sql` value is not a file path (e.g., inline SQL string)
    - The file path doesn't exist or isn't accessible
    - The entry doesn't have an `sql` key

    This permissive behavior allows mixing inline SQL and file-based SQL
    in the same catalog configuration.

    Examples
    --------
    Basic usage with file path resolution:

    >>> catalog_config = {
    ...     "sales_query": {
    ...         "type": "pandas.SQLQueryDataSet",
    ...         "sql": "data/queries/sales.sql",
    ...         "credentials": "db_creds",
    ...     }
    ... }
    >>> resolved_config = _replace_sql_with_query(catalog_config)
    >>> # Now resolved_config["sales_query"]["sql"] contains the query string

    Mixed inline and file-based SQL:

    >>> catalog_config = {
    ...     "inline_query": {
    ...         "sql": "SELECT * FROM users",  # Inline, unchanged
    ...         "type": "pandas.SQLQueryDataSet",
    ...     },
    ...     "file_query": {
    ...         "sql": "queries/complex.sql",  # File path, will be resolved
    ...         "type": "pandas.SQLQueryDataSet",
    ...     },
    ... }
    >>> resolved = _replace_sql_with_query(catalog_config)

    Example SQL file (data/queries/sales.sql):

    >>> # SELECT
    >>> #     date,
    >>> #     product_id,
    >>> #     SUM(quantity) as total_quantity,
    >>> #     SUM(revenue) as total_revenue
    >>> # FROM sales
    >>> # WHERE date >= '2023-01-01'
    >>> # GROUP BY date, product_id
    >>> # ORDER BY date, product_id

    Checking what gets resolved:

    >>> catalog_config = get_catalog_config(loader)
    >>> print("Before resolution:")
    >>> for name, conf in catalog_config.items():
    ...     if "sql" in conf:
    ...         print(f"  {name}: {conf['sql'][:50]}...")
    >>> resolved = _replace_sql_with_query(catalog_config)
    >>> print("After resolution:")
    >>> for name, conf in resolved.items():
    ...     if "sql" in conf:
    ...         sql_preview = conf["sql"].replace("\n", " ")[:50]
    ...         print(f"  {name}: {sql_preview}...")
    """
    for df_name, params in catalog_config.items():
        if "sql" in params and Path(params["sql"]).is_file():
            file_path = Path(params["sql"])
            catalog_config[df_name]["sql"] = file_path.read_text()

    return catalog_config


def get_credentials_config(
    config_loader: AbstractConfigLoader,
) -> dict[str, dict[str, Any]]:
    """
    Extract and return the credentials configuration from a Kedro config loader.

    This function retrieves credentials from a Kedro configuration loader,
    typically from credentials.yml files. Credentials include database
    connection strings, API keys, authentication tokens, and other sensitive
    configuration that should not be hardcoded in catalog configurations.

    The function gracefully handles missing credentials files by issuing a
    warning and returning an empty dictionary, allowing the application to
    continue with datasets that don't require credentials.

    Parameters
    ----------
    config_loader : AbstractConfigLoader
        A Kedro configuration loader instance (typically OmegaConfigLoader or
        TemplatedConfigLoader) that has access to credentials.yml files in the
        configured environments.

    Returns
    -------
    dict of str to dict of str to any
        A nested dictionary containing credentials configuration. The structure
        is:
        - Outer keys: Credential identifiers/names (str)
        - Inner dictionaries: Credential parameters including connection
          strings, usernames, passwords, API keys, host addresses, ports, etc.

        Returns an empty dictionary {} if:
        - No credentials.yml file exists in any environment
        - The credentials configuration is None or empty
        - A MissingConfigException or KeyError is raised

    Warns
    -----
    UserWarning
        Issued when credentials.yml is not found or cannot be loaded. The
        warning message includes a reference to Kedro's credentials
        documentation with instructions for setting up credentials properly.

    See Also
    --------
    create_omega_config_loader : Create the config loader to pass to this function.
    get_catalog_config : Get catalog configuration that references credentials.
    create_catalog : Uses credentials when instantiating the DataCatalog.

    Notes
    -----
    **Credentials File Location**

    Credentials files should be placed in environment-specific directories:

        config/
        ├── base/
        │   └── credentials.yml      # Shared/template credentials (optional)
        └── local/
            └── credentials.yml      # Local credentials (gitignored)

    **Security Best Practices**

    - NEVER commit credentials.yml to version control
    - Add `credentials.yml` to .gitignore
    - Use environment variables for production deployments
    - Store only credential names/keys in base, actual values in local
    - Use credential management systems (AWS Secrets Manager, etc.) in production

    **Credentials Format**

    The credentials.yml file follows this structure:

        credential_name:
          connection_string: "postgresql://user:pass@host:5432/db"

        another_credential:
          username: my_user
          password: my_password
          host: database.example.com
          port: 5432
          database: my_database

        api_credentials:
          api_key: "abc123xyz"
          api_secret: "secret789"

    **Referencing Credentials in Catalog**

    In catalog.yml, reference credentials by name:

        my_dataset:
          type: pandas.SQLTableDataset
          table_name: users
          credentials: credential_name  # References credentials.yml

    **Environment Variable Substitution**

    Using OmegaConfigLoader, you can reference environment variables:

        production_db:
          connection_string: ${oc.env:DATABASE_URL}
          # Or individual components:
          username: ${oc.env:DB_USER}
          password: ${oc.env:DB_PASSWORD}

    **Error Handling**

    The function catches two types of exceptions:
    - MissingConfigException: Raised by Kedro when credentials.yml doesn't exist
    - KeyError: Raised when the "credentials" key is not in the config loader

    Both cases result in a warning and an empty dictionary return value.

    **Warning Configuration**

    The warning is issued with stacklevel=2 to show the caller's location
    rather than this function's location, making debugging easier.

    Examples
    --------
    Basic usage to retrieve credentials:

    >>> loader = create_omega_config_loader("config")
    >>> credentials = get_credentials_config(loader)
    >>> if "db_credentials" in credentials:
    ...     print("Database credentials found")

    Inspect available credentials:

    >>> loader = create_omega_config_loader("config")
    >>> credentials = get_credentials_config(loader)
    >>> print(f"Available credentials: {list(credentials.keys())}")

    Handle missing credentials gracefully:

    >>> loader = create_omega_config_loader("config")
    >>> credentials = get_credentials_config(loader)
    >>> # If no credentials.yml exists, this prints empty list with warning
    >>> db_creds = credentials.get("database", {})
    >>> if not db_creds:
    ...     print("Using default/embedded credentials")

    Example credentials.yml structure:

    >>> # config/local/credentials.yml
    >>> #
    >>> # dev_postgres:
    >>> #   connection_string: "postgresql://user:pass@localhost:5432/dev_db"
    >>> #
    >>> # snowflake_prod:
    >>> #   account: "xy12345.us-east-1"
    >>> #   user: "prod_user"
    >>> #   password: "secure_password"
    >>> #   warehouse: "COMPUTE_WH"
    >>> #   database: "ANALYTICS"
    >>> #   schema: "PUBLIC"
    >>> #
    >>> # s3_credentials:
    >>> #   aws_access_key_id: "AKIAIOSFODNN7EXAMPLE"
    >>> #   aws_secret_access_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    >>> #   region_name: "us-east-1"

    Using credentials with environment variables:

    >>> # config/base/credentials.yml (template)
    >>> # production_db:
    >>> #   connection_string: ${oc.env:DATABASE_URL}
    >>> #
    >>> # api_service:
    >>> #   api_key: ${oc.env:API_KEY}
    >>> #   api_secret: ${oc.env:API_SECRET}

    Check for required credentials at startup:

    >>> required_creds = ["database", "api_service", "s3_bucket"]
    >>> loader = create_omega_config_loader("config")
    >>> credentials = get_credentials_config(loader)
    >>> missing = [c for c in required_creds if c not in credentials]
    >>> if missing:
    ...     raise ValueError(f"Missing required credentials: {missing}")
    """
    try:
        return config_loader["credentials"] or {}
    except (MissingConfigException, KeyError):
        warning_message = (
            "Your Kedro project does not have a `credentials.yml` file. "
            "Please refer to https://docs.kedro.org/en/stable/configuration/credentials.html "
            "for instructions on how to set up credentials."
        )
        warnings.warn(warning_message, stacklevel=2)
        return {}


def create_catalog(
    config_loader: AbstractConfigLoader,
) -> DataCatalog:
    """
    Create a fully configured Kedro DataCatalog from configuration files.

    This function orchestrates the complete workflow for creating a production-
    ready Kedro DataCatalog instance. It retrieves catalog and credentials
    configurations, resolves SQL file references to their query contents, and
    instantiates a DataCatalog with all datasets properly configured and ready
    for data I/O operations.

    The function performs these steps in order:
    1. Extract catalog configuration (dataset definitions)
    2. Resolve SQL file paths to actual query strings
    3. Extract credentials configuration (connection details)
    4. Create and return a DataCatalog instance

    This is the recommended high-level function for catalog creation, as it
    handles all necessary preprocessing and configuration resolution.

    Parameters
    ----------
    config_loader : AbstractConfigLoader
        A Kedro configuration loader instance (typically OmegaConfigLoader or
        TemplatedConfigLoader) that has been configured with the path to
        configuration files. This loader provides access to catalog.yml,
        credentials.yml, and other configuration files.

        Usually created via `create_omega_config_loader()`.

    Returns
    -------
    DataCatalog
        A fully configured Kedro DataCatalog instance containing all datasets
        defined in the catalog configuration. The catalog is ready to:
        - Load datasets using `catalog.load("dataset_name")`
        - Save datasets using `catalog.save("dataset_name", data)`
        - List available datasets using `catalog.list()`
        - Check dataset existence using `"dataset_name" in catalog`

        All SQL queries from referenced files are resolved, and credentials
        are properly linked to their respective datasets.

    See Also
    --------
    create_omega_config_loader : Create the config loader for this function.
    get_catalog_config : Lower-level function to get raw catalog config.
    get_credentials_config : Lower-level function to get credentials.
    kedro.io.DataCatalog : The Kedro DataCatalog class documentation.

    Notes
    -----
    **Complete Workflow Example**

    The typical workflow involves:

    1. Project structure:
        project/
        ├── config/
        │   ├── base/
        │   │   ├── catalog.yml
        │   │   └── globals.yml
        │   └── local/
        │       └── credentials.yml
        └── data/
            └── queries/
                └── my_query.sql

    2. Create config loader and catalog:
        loader = create_omega_config_loader("config")
        catalog = create_catalog(loader)

    3. Use the catalog for I/O:
        data = catalog.load("my_dataset")
        catalog.save("processed_data", result)

    **SQL File Resolution**

    If your catalog.yml contains SQL file references:

        my_query_dataset:
          type: pandas.SQLQueryDataSet
          sql: data/queries/extract.sql
          credentials: db_creds

    The `create_catalog()` function automatically reads the SQL file and
    replaces the path with the actual query string before creating the catalog.

    **Credentials Integration**

    Datasets that specify a `credentials` parameter in catalog.yml will
    automatically have their credentials resolved from credentials.yml:

        # catalog.yml
        postgres_table:
          type: pandas.SQLTableDataset
          table_name: users
          credentials: postgres_creds

        # credentials.yml
        postgres_creds:
          connection_string: "postgresql://user:pass@host:5432/db"

    **Dataset Types and Capabilities**

    The returned DataCatalog supports various dataset types:
    - File-based: CSV, Parquet, Excel, JSON, Pickle
    - Database: SQL tables, SQL queries (PostgreSQL, MySQL, etc.)
    - Cloud storage: S3, GCS, Azure Blob Storage
    - In-memory: Memory datasets for pipeline intermediates
    - Custom: User-defined dataset classes

    **Lazy Loading**

    Datasets are not loaded when the catalog is created. Data is only loaded
    when you explicitly call `catalog.load("dataset_name")`. This allows
    efficient memory usage and fast catalog initialization.

    **Thread Safety**

    The DataCatalog instance is thread-safe for concurrent reads but not for
    concurrent writes to the same dataset. Design your pipeline accordingly.

    **Error Handling**

    Common issues and their causes:
    - FileNotFoundError: File path in catalog.yml doesn't exist
    - ImportError: Dataset type class not installed (e.g., pandas.ExcelDataSet needs openpyxl)
    - KeyError: Referenced credentials not found in credentials.yml
    - ConnectionError: Database credentials incorrect or database unreachable

    Examples
    --------
    Basic catalog creation and usage:

    >>> from pathlib import Path
    >>> config_path = Path("config")
    >>> loader = create_omega_config_loader(str(config_path))
    >>> catalog = create_catalog(loader)
    >>> # Load a dataset
    >>> df = catalog.load("raw_data")
    >>> # Save processed data
    >>> catalog.save("processed_data", processed_df)

    Inspect available datasets:

    >>> loader = create_omega_config_loader("config")
    >>> catalog = create_catalog(loader)
    >>> print("Available datasets:")
    >>> for dataset_name in catalog.list():
    ...     print(f"  - {dataset_name}")

    Check if a dataset exists before loading:

    >>> catalog = create_catalog(create_omega_config_loader("config"))
    >>> if "optional_data" in catalog:
    ...     data = catalog.load("optional_data")
    ... else:
    ...     print("Optional data not configured")

    Load multiple datasets:

    >>> catalog = create_catalog(create_omega_config_loader("config"))
    >>> datasets = ["raw_data", "reference_data", "parameters"]
    >>> loaded_data = {name: catalog.load(name) for name in datasets}

    Example catalog.yml with various dataset types:

    >>> # config/base/catalog.yml
    >>> #
    >>> # # CSV file
    >>> # iris_data:
    >>> #   type: pandas.CSVDataset
    >>> #   filepath: data/01_raw/iris.csv
    >>> #
    >>> # # Parquet with partitions
    >>> # sales_data:
    >>> #   type: pandas.ParquetDataSet
    >>> #   filepath: data/02_intermediate/sales.parquet
    >>> #   load_args:
    >>> #     engine: pyarrow
    >>> #   save_args:
    >>> #     compression: snappy
    >>> #
    >>> # # SQL query from file
    >>> # customer_features:
    >>> #   type: pandas.SQLQueryDataSet
    >>> #   sql: data/queries/customer_features.sql
    >>> #   credentials: postgres_creds
    >>> #
    >>> # # SQL table
    >>> # transactions:
    >>> #   type: pandas.SQLTableDataset
    >>> #   table_name: transactions
    >>> #   credentials: postgres_creds
    >>> #
    >>> # # In-memory dataset
    >>> # intermediate_result:
    >>> #   type: MemoryDataSet

    Error handling example:

    >>> loader = create_omega_config_loader("config")
    >>> try:
    ...     catalog = create_catalog(loader)
    ...     data = catalog.load("my_dataset")
    ... except FileNotFoundError as e:
    ...     print(f"Data file not found: {e}")
    ... except KeyError as e:
    ...     print(f"Missing configuration or credentials: {e}")

    Working with SQL file resolution:

    >>> # Before: catalog.yml references SQL file
    >>> # my_query:
    >>> #   type: pandas.SQLQueryDataSet
    >>> #   sql: data/queries/complex_query.sql
    >>> #   credentials: db_creds
    >>> #
    >>> # After: create_catalog() resolves the file
    >>> catalog = create_catalog(create_omega_config_loader("config"))
    >>> # The SQL query is now loaded and ready to execute
    >>> result = catalog.load("my_query")

    Advanced: Custom dataset type registration:

    >>> from kedro.io import AbstractDataSet
    >>> # Register custom dataset type before creating catalog
    >>> # Then use it in catalog.yml:
    >>> # custom_data:
    >>> #   type: my_package.CustomDataSet
    >>> #   filepath: data/custom.dat
    >>> catalog = create_catalog(create_omega_config_loader("config"))
    >>> data = catalog.load("custom_data")
    """
    catalog_config = get_catalog_config(config_loader)
    catalog_config_updated = _replace_sql_with_query(catalog_config)
    credentials_config = get_credentials_config(config_loader)
    catalog = DataCatalog.from_config(
        catalog=catalog_config_updated,
        credentials=credentials_config,
    )
    return catalog
