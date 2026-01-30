"""
Data handling module for the adc-toolkit.

This module provides the core data management infrastructure for adc-toolkit
projects, combining configuration-driven data catalogs with automatic data
validation to ensure data quality throughout ML and analytics pipelines.

The module's centerpiece is the ValidatedDataCatalog class, which transparently
validates all data loading and saving operations. By enforcing data quality at
catalog boundaries, it catches schema drift, data corruption, and constraint
violations early in the pipeline, preventing invalid data from propagating to
downstream systems.

The architecture uses protocol-based dependency injection, allowing flexible
combinations of catalog implementations (for I/O) and validator implementations
(for quality checks). Default implementations provide production-ready
functionality with Kedro-based catalogs and Great Expectations or Pandera
validators.

Classes
-------
ValidatedDataCatalog
    Main user-facing API combining a data catalog with automatic validation.
    Factory method: `ValidatedDataCatalog.in_directory(path)`.

Protocols
---------
Data
    Protocol for data objects (requires columns and dtypes properties).
DataCatalog
    Protocol for catalog implementations (load, save, in_directory methods).
DataValidator
    Protocol for validator implementations (validate, in_directory methods).

Submodules
----------
catalogs
    Data catalog implementations, including KedroDataCatalog.
validators
    Data validator implementations: GXValidator, PanderaValidator, NoValidator.
abs
    Protocol definitions for Data, DataCatalog, and DataValidator.
catalog
    ValidatedDataCatalog implementation.
default_attributes
    Factory functions for default catalog and validator instances.

See Also
--------
adc_toolkit.data.catalog.ValidatedDataCatalog : Primary data catalog API.
adc_toolkit.data.catalogs.kedro.KedroDataCatalog : Kedro catalog implementation.
adc_toolkit.data.validators.gx.GXValidator : Great Expectations validator.
adc_toolkit.data.validators.pandera.PanderaValidator : Pandera validator.

Notes
-----
The module follows these design patterns:

- **Factory Pattern**: Use `in_directory(path)` class methods to instantiate
  catalogs and validators from configuration directories.
- **Strategy Pattern**: Swap catalog and validator implementations without
  changing downstream code.
- **Protocol-based Design**: Type safety through structural subtyping rather
  than inheritance.
- **Dependency Injection**: Pass catalog and validator as constructor arguments
  for testability and flexibility.

Configuration-driven approach enables:

- Declarative dataset definitions (where data lives, how to load/save it)
- Environment-specific configurations (dev, staging, production)
- Separation of data access logic from business logic
- Reproducible data pipelines with version-controlled configurations

Data validation workflow:

- On load: `catalog.load()` -> `validator.validate()` -> return validated data
- On save: `validator.validate()` -> `catalog.save()` -> no invalid data persisted

This ensures data quality is enforced at every catalog boundary.

Examples
--------
Basic usage with default catalog and validator:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> catalog = ValidatedDataCatalog.in_directory("config/data")
>>> df = catalog.load("customer_data")  # Automatically validated
>>> processed = transform(df)
>>> catalog.save("processed_data", processed)  # Validated before saving

Using custom validator:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> from adc_toolkit.data.validators.pandera import PanderaValidator
>>> catalog = ValidatedDataCatalog.in_directory("config/data", validator_class=PanderaValidator)

Working directly with protocols for type annotations:

>>> from adc_toolkit.data.abs import DataCatalog, DataValidator, Data
>>> def pipeline(catalog: DataCatalog, validator: DataValidator) -> Data:
...     raw = catalog.load("raw_data")
...     validated = validator.validate("raw_data", raw)
...     return validated

Complete pipeline example:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>>
>>> # Initialize validated catalog
>>> catalog = ValidatedDataCatalog.in_directory("config/production")
>>>
>>> # Load and process with automatic validation
>>> raw_sales = catalog.load("raw_sales")
>>> cleaned_sales = raw_sales.dropna()
>>> catalog.save("cleaned_sales", cleaned_sales)
>>>
>>> aggregated = cleaned_sales.groupby("region").sum()
>>> catalog.save("sales_summary", aggregated)
>>> # All loads validated on read, all saves validated on write
"""
