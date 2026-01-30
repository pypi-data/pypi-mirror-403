"""
Data validation framework for the adc-toolkit.

This module provides a flexible data validation system that supports multiple
validation backends through a protocol-based architecture. Validators implement
the DataValidator protocol, enabling seamless integration with ValidatedDataCatalog
and other toolkit components regardless of the underlying validation framework.

The validators module includes three main implementations:

1. **Great Expectations (GX)**: Enterprise-grade validation with rich features
   including expectation suites, checkpoints, data profiling, and data documentation.
   Supports multiple storage backends (filesystem, AWS S3, GCP, Azure).

2. **Pandera**: Lightweight, pandas-native validation with Python-based schemas,
   automatic schema generation, and tight integration with type hints. Ideal for
   rapid prototyping and teams comfortable with code-based configuration.

3. **NoValidator**: Pass-through validator that bypasses validation for development,
   testing, or scenarios with trusted data sources.

The protocol-based design enables dependency injection and the strategy pattern,
allowing users to swap validator implementations without changing downstream code.
All validators follow a consistent interface: ``in_directory()`` factory method
for configuration-based instantiation and ``validate()`` method for data validation.

Modules
-------
gx
    Great Expectations validator implementation with batch managers, data context
    implementations, and expectation management strategies.
pandera
    Pandera validator implementation with automatic schema generation, compilation,
    and execution.
no_validator
    No-operation validator that passes data through unchanged without validation.

See Also
--------
adc_toolkit.data.abs.DataValidator : Protocol defining the validator interface.
adc_toolkit.data.ValidatedDataCatalog : Data catalog with integrated validation.
adc_toolkit.data.catalogs : Data catalog implementations.

Notes
-----
**Choosing a Validator**

Select a validator based on your project requirements:

**Use Great Expectations (GX) when:**
- You need enterprise features (data docs, profiling, cloud backends)
- You want declarative YAML/JSON configuration
- You require comprehensive data documentation websites
- Your organization has existing Great Expectations infrastructure
- You need advanced features like data quality dashboards and monitoring

**Use Pandera when:**
- You prefer lightweight, pandas-native validation
- You want Python-based schema definitions for better IDE support
- You need tight integration with type hints and static analysis
- Your team prefers code-based configuration over YAML/JSON
- You're building prototypes or smaller-scale projects

**Use NoValidator when:**
- Developing or debugging without validation overhead
- Testing with mocked data where validation is not relevant
- Working with trusted data sources that have external validation guarantees
- Temporarily bypassing validation for performance profiling

**Protocol-Based Architecture**

All validators implement the ``DataValidator`` protocol, ensuring consistent
interfaces:

.. code-block:: python

    class DataValidator(Protocol):
        def validate(self, name: str, data: Data) -> Data: ...
        @classmethod
        def in_directory(cls, path: str | Path) -> "DataValidator": ...

This design enables:
- Dependency injection: Pass validators as constructor parameters
- Strategy pattern: Swap validators without changing application code
- Type safety: Static type checking with protocol-based type hints
- Testability: Easy to mock validators in unit tests

**Integration with ValidatedDataCatalog**

Validators are typically used through ``ValidatedDataCatalog``, which automatically
validates data on load and save operations:

.. code-block:: python

    from adc_toolkit.data import ValidatedDataCatalog
    from adc_toolkit.data.validators.pandera import PanderaValidator

    catalog = ValidatedDataCatalog.in_directory(path="config", validator=PanderaValidator.in_directory("config/validators"))
    # Validation happens automatically
    df = catalog.load("dataset_name")  # Validates after loading
    catalog.save("output_name", df)  # Validates before saving

**Version Control Practices**

For version-controlled validation rules:

**Great Expectations:**
- Commit: expectations/, checkpoints/, great_expectations.yml, plugins/
- Ignore: uncommitted/ (validation results and data docs)

**Pandera:**
- Commit: All schema scripts in pandera_schemas/
- Ignore: None (all schema files should be version controlled)

**Performance Considerations**

Validation adds overhead to data pipelines. Consider these optimization strategies:

- **Caching**: Reuse validator instances across multiple validations
- **Sampling**: Validate representative samples of very large datasets
- **Lazy validation**: Use Pandera's lazy mode to collect all errors at once
- **Selective validation**: Validate only critical datasets in production
- **Async validation**: Run validations in parallel for independent datasets

Examples
--------
Using Great Expectations validator:

>>> from adc_toolkit.data.validators.gx import GXValidator
>>> import pandas as pd
>>> validator = GXValidator.in_directory("config/gx")
>>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
>>> validated = validator.validate("my_dataset", df)

Using Pandera validator:

>>> from adc_toolkit.data.validators.pandera import PanderaValidator
>>> validator = PanderaValidator.in_directory("config/validators")
>>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
>>> validated = validator.validate("customers", df)

Using NoValidator for testing:

>>> from adc_toolkit.data.validators.no_validator import NoValidator
>>> validator = NoValidator()
>>> df = pd.DataFrame({"a": [1, 2, 3]})
>>> validated = validator.validate("test_data", df)  # No validation performed

Swapping validators with dependency injection:

>>> def create_pipeline(validator_type: str):
...     if validator_type == "gx":
...         validator = GXValidator.in_directory("config/gx")
...     elif validator_type == "pandera":
...         validator = PanderaValidator.in_directory("config/pandera")
...     else:
...         validator = NoValidator()
...     return DataPipeline(validator=validator)

Integration with ValidatedDataCatalog:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> from adc_toolkit.data.validators.pandera import PanderaValidator
>>> catalog = ValidatedDataCatalog.in_directory(
...     path="config", validator=PanderaValidator.in_directory("config/validators")
... )
>>> df = catalog.load("dataset")  # Automatically validated
>>> catalog.save("output", df)  # Automatically validated

Validation in a data pipeline:

>>> def etl_pipeline(validator):
...     raw = load_raw_data()
...     validated_raw = validator.validate("raw_data", raw)
...     cleaned = clean_data(validated_raw)
...     validated_clean = validator.validate("cleaned_data", cleaned)
...     features = engineer_features(validated_clean)
...     validated_features = validator.validate("features", features)
...     return validated_features
"""
