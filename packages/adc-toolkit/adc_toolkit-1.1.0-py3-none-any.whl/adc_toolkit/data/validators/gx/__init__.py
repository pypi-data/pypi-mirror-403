"""
Great Expectations validator implementation for adc-toolkit.

This module provides a comprehensive Great Expectations (GX) integration for the
adc-toolkit data validation system. It implements the DataValidator protocol using
GX's powerful expectation framework, enabling enterprise-grade data quality validation
with rich features including expectation suites, checkpoints, batch management, data
profiling, and automatic data documentation.

The module orchestrates the complete GX validation workflow through a flexible,
strategy-based architecture that supports multiple storage backends (local filesystem,
AWS S3, Google Cloud Storage, Azure Blob Storage), pluggable validation strategies,
and automatic schema freezing for rapid prototyping.

Classes
-------
GXValidator
    Main validator class implementing the DataValidator protocol. Provides high-level
    validation interface with automatic expectation suite creation, schema freezing,
    and comprehensive error reporting.

BatchManager
    Manages creation and configuration of Great Expectations batch objects from
    pandas or PySpark DataFrames. Handles batch request generation and batch
    execution for validation checkpoints.

ConfigurationBasedExpectationAddition
    Strategy for adding expectations to suites based on configuration files. Enables
    declarative expectation management through YAML or JSON configuration.

ValidatorBasedExpectationAddition
    Strategy for adding expectations using GX Validator objects. Provides programmatic
    expectation addition with full access to GX's validation API.

Functions
---------
None
    This module exports only classes. Validation orchestration is handled by
    GXValidator.validate(), and supporting functionality is encapsulated in
    strategy and manager classes.

See Also
--------
adc_toolkit.data.validators.gx.validator : GXValidator implementation details.
adc_toolkit.data.validators.gx.batch_managers : Batch management components.
adc_toolkit.data.validators.gx.data_context : Data context implementations.
adc_toolkit.data.abs.DataValidator : Protocol defining validator interface.
adc_toolkit.data.ValidatedDataCatalog : Data catalog with integrated validation.
adc_toolkit.data.validators.pandera : Alternative lightweight validator.
adc_toolkit.data.validators.no_validator : No-op validator for testing.

Notes
-----
**Great Expectations Overview**

Great Expectations (https://greatexpectations.io/) is an open-source Python
library for data quality, testing, profiling, and documentation. This integration
provides a bridge between adc-toolkit's validation abstraction and GX's rich
ecosystem, enabling:

- **Declarative data quality rules**: Define expectations in configuration
- **Automatic profiling**: Generate expectations from sample data
- **Data documentation**: Generate comprehensive data docs websites
- **Multiple backends**: Store validation artifacts in cloud storage
- **Extensive expectation library**: 50+ built-in expectations plus custom
- **Version control**: Track changes to expectations over time
- **Integration**: Compatible with Jupyter, Airflow, dbt, and other tools

**Architecture and Design Patterns**

The GX validator implements several design patterns:

**Strategy Pattern:**
    Pluggable strategies for expectation suite lookup and expectation addition
    enable flexible validation workflows without modifying core logic.

    - ``AutoExpectationSuiteCreation``: Auto-creates missing suites
    - ``CustomExpectationSuiteStrategy``: Requires pre-defined suites
    - ``SchemaExpectationAddition``: Automatically adds schema expectations
    - ``SkipExpectationAddition``: Skips automatic expectation addition

**Facade Pattern:**
    GXValidator simplifies GX's complex API by providing a clean, high-level
    interface (``validate()``) that orchestrates multiple underlying operations.

**Dependency Injection:**
    Data context and strategies are injected via constructor, enabling testability,
    configuration flexibility, and easy mocking in unit tests.

**Validation Workflow**

The complete validation sequence when calling ``GXValidator.validate()``:

1. **Suite Lookup**: Check if expectation suite exists for dataset
2. **Suite Creation**: Create suite if missing (based on lookup strategy)
3. **Batch Creation**: Convert data to GX Batch using BatchManager
4. **Expectation Addition**: Add expectations based on addition strategy
5. **Checkpoint Creation**: Create or update checkpoint for dataset
6. **Checkpoint Execution**: Execute checkpoint to validate batch
7. **Result Evaluation**: Analyze results, raise ValidationError on failure
8. **Data Return**: Return original data if validation succeeds

**Storage Backends**

The module supports multiple data context backends through the
``adc_toolkit.data.validators.gx.data_context`` submodule:

- **RepoDataContext**: Filesystem-based (default)
- **S3DataContext**: AWS S3 storage
- **GCPDataContext**: Google Cloud Storage
- **AzureDataContext**: Azure Blob Storage
- **EphemeralDataContext**: In-memory (testing)

Backend selection is transparent to application code, configured through the
``in_directory()`` factory method or by passing a pre-configured data context
to the ``GXValidator`` constructor.

**Schema Freezing**

With default strategies (``AutoExpectationSuiteCreation`` +
``SchemaExpectationAddition``), the validator automatically "freezes" schemas
on first validation:

1. First validation inspects DataFrame structure (columns, types)
2. Schema expectations are generated and stored in expectation suite
3. Subsequent validations enforce frozen schema
4. Schema drift is detected and reported as validation failure

This provides automatic protection against schema changes while allowing manual
customization of expectation suites when needed.

**Performance Considerations**

- **First validation overhead**: Suite creation and checkpoint setup add latency
  to first validation. Subsequent validations are faster (suite reuse).
- **Schema inspection cost**: Schema freezing requires full DataFrame inspection,
  scaling with number of columns (not rows).
- **Expectation complexity**: Simple schema checks are fast; statistical
  expectations (distributions, correlations) can be expensive on large datasets.
- **Backend I/O**: Cloud backends (S3, GCS) add network latency compared to
  local filesystem.
- **Sampling strategies**: For large datasets, consider validating samples
  rather than complete data.

**Thread Safety**

GXValidator instances are not thread-safe. The underlying Great Expectations data
context performs file/network I/O and maintains internal state. For concurrent
validation scenarios, create separate validator instances (with separate data
contexts) per thread or implement external locking.

**Version Control Best Practices**

When using filesystem-based data contexts (RepoDataContext), follow these
version control guidelines:

**Commit to git:**
- ``expectations/``: Expectation suite JSON files
- ``checkpoints/``: Checkpoint YAML configurations
- ``great_expectations.yml``: Main configuration
- ``plugins/``: Custom expectation implementations

**Add to .gitignore:**
- ``uncommitted/``: Validation results and data docs
- ``uncommitted/validations/``: Validation result artifacts
- ``uncommitted/data_docs/``: Generated documentation websites

This approach version controls validation rules while excluding environment-specific
results and generated documentation.

Examples
--------
Basic usage with automatic suite creation and schema freezing:

>>> from adc_toolkit.data.validators.gx import GXValidator
>>> import pandas as pd
>>> validator = GXValidator.in_directory("config/gx")
>>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
>>> validated = validator.validate("sales_data", df)
>>> # First validation: auto-creates suite, freezes schema
>>> # Subsequent validations: enforces frozen schema

Using custom strategies for strict validation:

>>> from adc_toolkit.data.validators.gx import GXValidator
>>> from adc_toolkit.data.validators.gx.batch_managers import (
...     CustomExpectationSuiteStrategy,
...     SkipExpectationAddition,
... )
>>> from great_expectations.data_context import EphemeralDataContext
>>> context = EphemeralDataContext()
>>> validator = GXValidator(
...     data_context=context,
...     expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy(),
...     expectation_addition_strategy=SkipExpectationAddition(),
... )
>>> # Requires pre-defined suites, no automatic expectations

Using with cloud-based data context:

>>> from adc_toolkit.data.validators.gx import GXValidator
>>> from adc_toolkit.data.validators.gx.data_context import S3DataContext
>>> s3_context = S3DataContext("s3://my-bucket/gx-config").create()
>>> validator = GXValidator(data_context=s3_context)
>>> validated = validator.validate("dataset", df)
>>> # Expectations and results stored in S3

Integration with ValidatedDataCatalog:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> from adc_toolkit.data.validators.gx import GXValidator
>>> catalog = ValidatedDataCatalog.in_directory(path="config", validator=GXValidator.in_directory("config/gx"))
>>> df = catalog.load("customer_data")  # Validates after load
>>> catalog.save("processed_data", df)  # Validates before save

Detecting schema drift:

>>> validator = GXValidator.in_directory("config/gx")
>>> # First validation with original schema
>>> df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
>>> validator.validate("users", df1)  # Creates suite, freezes schema
>>> # Subsequent validation with changed schema
>>> df2 = pd.DataFrame({"id": [3], "age": [30]})  # Different columns!
>>> try:
...     validator.validate("users", df2)
... except ValidationError as e:
...     print(f"Schema drift detected: {e}")
...     # Validation fails due to mismatched columns

Manual expectation suite creation:

>>> from great_expectations.data_context import EphemeralDataContext
>>> from great_expectations.core import ExpectationConfiguration
>>> context = EphemeralDataContext()
>>> # Create custom suite with specific expectations
>>> suite = context.create_expectation_suite("custom_suite")
>>> suite.add_expectation(
...     ExpectationConfiguration(
...         expectation_type="expect_column_values_to_be_in_range",
...         kwargs={"column": "age", "min_value": 0, "max_value": 120},
...     )
... )
>>> validator = GXValidator(data_context=context)
>>> df = pd.DataFrame({"age": [25, 30, 35]})
>>> validated = validator.validate("custom", df)

Data pipeline with multiple validation stages:

>>> def quality_pipeline(gx_path: str):
...     validator = GXValidator.in_directory(gx_path)
...
...     # Validate raw input
...     raw = load_raw_data()
...     validated_raw = validator.validate("raw_stage", raw)
...
...     # Transform and validate
...     cleaned = clean_data(validated_raw)
...     validated_clean = validator.validate("clean_stage", cleaned)
...
...     # Feature engineering and validate
...     features = engineer_features(validated_clean)
...     validated_features = validator.validate("feature_stage", features)
...
...     return validated_features
"""

from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import (
    ConfigurationBasedExpectationAddition,
    ValidatorBasedExpectationAddition,
)
from adc_toolkit.data.validators.gx.validator import GXValidator


__all__ = [
    "BatchManager",
    "ConfigurationBasedExpectationAddition",
    "GXValidator",
    "ValidatorBasedExpectationAddition",
]
