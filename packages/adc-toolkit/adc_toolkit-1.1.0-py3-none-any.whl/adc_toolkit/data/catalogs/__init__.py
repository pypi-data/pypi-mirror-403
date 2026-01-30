"""
Data catalog implementations for the adc-toolkit.

This module provides concrete implementations of the DataCatalog protocol,
enabling configuration-driven data I/O operations in ML and analytics pipelines.
Data catalogs abstract away the details of data storage, file formats, and
access patterns, providing a simple name-based API for loading and saving
datasets.

The module currently includes Kedro-based catalog implementations, which support
YAML-based dataset definitions, multiple file formats (CSV, Parquet, JSON, Excel,
Pickle, HDF5), diverse storage backends (local filesystem, S3, GCS, Azure Blob),
and advanced features like versioning, partitioning, and dynamic SQL queries.

Submodules
----------
kedro
    Kedro-based data catalog implementation with KedroDataCatalog class and
    scaffolding utilities for creating catalog directory structures.

See Also
--------
adc_toolkit.data.catalogs.kedro.KedroDataCatalog : Main Kedro catalog class.
adc_toolkit.data.abs.DataCatalog : Protocol definition for catalogs.
adc_toolkit.data.catalog.ValidatedDataCatalog : Catalog with automatic validation.

Notes
-----
Data catalogs provide several key benefits:

- **Configuration-Driven**: Dataset locations, formats, and parameters defined
  in YAML files rather than hardcoded in application logic.
- **Environment Flexibility**: Different configurations for dev, staging, and
  production environments without code changes.
- **Reproducibility**: Version-controlled configurations ensure consistent
  data access across team members and deployments.
- **Testability**: Easy to mock or swap catalogs for unit testing.
- **Separation of Concerns**: Data access logic decoupled from business logic.

The catalog pattern is particularly valuable in data science and ML workflows
where data sources, formats, and locations frequently change across environments
and project phases.

Catalog Configuration Structure
--------------------------------
Catalogs typically use a hierarchical configuration structure:

- **base/**: Shared dataset definitions for all environments
- **local/**: Environment-specific overrides and credentials (gitignored)
- **globals.yml**: Global variables and parameters
- **credentials.yml**: Credentials for databases and cloud storage (gitignored)

This structure enables configuration composition: base definitions provide
defaults, while local overrides customize behavior for specific environments.

Supported Dataset Types
-----------------------
Kedro-based catalogs support diverse dataset types:

- **Tabular**: CSV, Parquet, Excel, Feather, ORC
- **Serialized**: Pickle, JSON, YAML, HDF5
- **Database**: SQL queries, table reads/writes
- **Big Data**: Spark DataFrames with various formats
- **Cloud Storage**: S3, GCS, Azure Blob via fsspec
- **Specialized**: NetworkX graphs, Matplotlib figures, text files

Each dataset type has configurable load and save arguments for fine-grained
control over I/O behavior.

Examples
--------
Create a Kedro catalog from configuration directory:

>>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
>>> catalog = KedroDataCatalog.in_directory("config/catalog")
>>> df = catalog.load("training_data")
>>> catalog.save("predictions", predictions_df)

Initialize catalog directory structure with templates:

>>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
>>> result = KedroDataCatalog.init_catalog("./config/catalog")
>>> print(f"Created {len(result.created_files)} configuration files")

Use catalog in a data pipeline:

>>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
>>>
>>> def etl_pipeline(catalog: KedroDataCatalog) -> None:
...     # Load raw data
...     raw = catalog.load("raw_sales")
...
...     # Transform
...     cleaned = raw.dropna()
...     enriched = enrich_with_features(cleaned)
...
...     # Save intermediate and final results
...     catalog.save("cleaned_sales", cleaned)
...     catalog.save("enriched_sales", enriched)
>>>
>>> catalog = KedroDataCatalog.in_directory("config/production")
>>> etl_pipeline(catalog)

Load data with dynamic SQL query parameters:

>>> catalog = KedroDataCatalog.in_directory("config/catalog")
>>> # Query defined in catalog.yml: SELECT * FROM sales WHERE year={year}
>>> sales_2024 = catalog.load("sales_data", year=2024)
>>> sales_2023 = catalog.load("sales_data", year=2023)
"""
