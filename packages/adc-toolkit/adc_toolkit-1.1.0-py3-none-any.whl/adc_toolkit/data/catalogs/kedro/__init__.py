"""
Kedro-based data catalog implementation for the adc-toolkit.

This module provides a production-ready data catalog implementation using Kedro's
DataCatalog as the underlying I/O engine. It enables configuration-driven dataset
management through YAML files, supporting diverse data formats, storage backends,
versioning, partitioning, and dynamic SQL queries.

The KedroDataCatalog wraps Kedro's native catalog with a simplified interface
that integrates seamlessly with the adc-toolkit's validation and processing
pipeline. It provides factory methods for instantiation and utilities for
scaffolding new catalog configurations.

Classes
-------
KedroDataCatalog
    Main Kedro catalog implementation with methods for loading and saving
    datasets based on YAML configuration files. Provides `in_directory()`
    factory method and `init_catalog()` scaffolding utility.

Submodules
----------
kedro_catalog
    Core KedroDataCatalog implementation.
kedro_configs
    Configuration loader utilities for Kedro OmegaConfigLoader.
scaffold
    Utilities for creating catalog directory structures with template files.
templates
    Template YAML files for catalog, globals, and credentials configurations.

See Also
--------
adc_toolkit.data.abs.DataCatalog : Protocol definition for catalogs.
adc_toolkit.data.catalog.ValidatedDataCatalog : Catalog with automatic validation.
kedro.io.DataCatalog : Underlying Kedro catalog implementation.
kedro.config.OmegaConfigLoader : Configuration loader for YAML files.

Notes
-----
The Kedro data catalog system uses YAML configuration files to define datasets,
including file paths, formats, load/save parameters, and storage backends. This
declarative approach separates data I/O concerns from business logic and enables
environment-specific configurations without code changes.

Expected Directory Structure
----------------------------
The catalog expects a specific configuration directory structure::

    config_path/
        base/
            catalog.yml      # Base dataset definitions shared across environments
            globals.yml      # Global variables (e.g., base_path, bucket_name)
        local/
            catalog.yml      # Local overrides for development (gitignored)
            credentials.yml  # Credentials for databases/cloud (gitignored)

The `base/` directory contains shared definitions, while `local/` contains
environment-specific overrides. Local files should be added to .gitignore to
prevent committing credentials or environment-specific paths.

Configuration Format
--------------------
Dataset definitions in catalog.yml follow Kedro's format:

.. code-block:: yaml

    # Simple CSV dataset
    customer_data:
      type: pandas.CSVDataset
      filepath: data/raw/customers.csv
      load_args:
        sep: ","
        parse_dates: ["signup_date"]
      save_args:
        index: False

    # Parquet dataset with versioning
    processed_features:
      type: pandas.ParquetDataset
      filepath: data/processed/features.parquet
      versioned: true

    # SQL dataset with dynamic query parameters
    sales_query:
      type: pandas.SQLQueryDataset
      sql: "SELECT * FROM sales WHERE year={year} AND region='{region}'"
      credentials: database_creds

    # Cloud storage dataset
    s3_data:
      type: pandas.ParquetDataset
      filepath: s3://my-bucket/data/dataset.parquet
      credentials: aws_credentials

Global variables in globals.yml can be referenced in catalog.yml using
`${globals:variable_name}` syntax for parameterization.

Supported Features
------------------
- **File Formats**: CSV, Parquet, JSON, Excel, Pickle, HDF5, Feather, ORC
- **Storage Backends**: Local filesystem, S3, GCS, Azure Blob, HDFS
- **Versioning**: Automatic timestamping of saved datasets
- **Partitioning**: Split large datasets across multiple files
- **Dynamic Queries**: SQL query parameterization at load time
- **Dataset Factories**: Pattern-based dataset definitions for systematic naming
- **Credentials Management**: Secure credential storage in local/credentials.yml

Thread Safety
-------------
KedroDataCatalog delegates to Kedro's DataCatalog, which is not thread-safe for
concurrent writes to the same dataset. Concurrent reads are safe. Use external
locking mechanisms if concurrent writes are required.

References
----------
.. [1] Kedro Documentation: Data Catalog
   https://docs.kedro.org/en/stable/data/data_catalog.html
.. [2] Kedro Documentation: Configuration
   https://docs.kedro.org/en/stable/configuration/configuration_basics.html

Examples
--------
Create a catalog from an existing configuration directory:

>>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
>>> catalog = KedroDataCatalog.in_directory("config/catalog")
>>> df = catalog.load("customer_data")
>>> df.columns
Index(['customer_id', 'name', 'email', 'signup_date'], dtype='object')

Save processed data:

>>> processed_df = process_customers(df)
>>> catalog.save("processed_customers", processed_df)

Initialize a new catalog structure with template files:

>>> result = KedroDataCatalog.init_catalog(
...     "./my_project/config/catalog",
...     include_globals=True,
...     include_catalog=True,
...     include_credentials=True,
... )
>>> print(f"Created: {[f.name for f in result.created_files]}")
Created: ['catalog.yml', 'globals.yml', 'credentials.yml']

Load data with dynamic SQL query parameters:

>>> # catalog.yml defines: sql: "SELECT * FROM sales WHERE year={year}"
>>> catalog = KedroDataCatalog.in_directory("config/catalog")
>>> sales_2024 = catalog.load("sales_data", year=2024)
>>> sales_2023 = catalog.load("sales_data", year=2023)

Use in a complete data pipeline:

>>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
>>>
>>> def run_pipeline():
...     catalog = KedroDataCatalog.in_directory("config/production")
...
...     # Extract
...     raw_sales = catalog.load("raw_sales")
...     raw_customers = catalog.load("raw_customers")
...
...     # Transform
...     cleaned_sales = clean_data(raw_sales)
...     enriched = enrich_with_customer_data(cleaned_sales, raw_customers)
...
...     # Load (save results)
...     catalog.save("cleaned_sales", cleaned_sales)
...     catalog.save("enriched_sales", enriched)
>>> run_pipeline()

Create catalog with custom configuration loader:

>>> from kedro.config import OmegaConfigLoader
>>> loader = OmegaConfigLoader(
...     conf_source="config",
...     env="production",
...     base_env="base",
...     default_run_env="local",
... )
>>> catalog = KedroDataCatalog("config/catalog", config_loader=loader)
"""

from .kedro_catalog import KedroDataCatalog


__all__ = ["KedroDataCatalog"]
