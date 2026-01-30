"""
Pandera-based data validation framework for the adc-toolkit.

This module provides a comprehensive Pandera-based validation implementation that
combines automatic schema generation with manual customization capabilities. It
enables rapid prototyping with zero-setup validation while supporting iterative
refinement of validation rules as data requirements evolve.

The validation workflow is optimized for real-world data engineering scenarios where
schemas need to be established quickly but refined over time. Schema scripts are
stored as editable Python files, enabling version control, code review, and team
collaboration on data quality standards.

Classes
-------
PanderaValidator
    Main validator class implementing the DataValidator protocol. Orchestrates
    automatic schema generation, schema loading, and validation execution using
    Pandera's DataFrameSchema.validate() method. Integrates seamlessly with
    ValidatedDataCatalog for automatic validation on load/save operations.
PanderaParameters
    Immutable configuration dataclass controlling validation behavior. Primary
    setting is the 'lazy' parameter which determines error collection strategy
    (collect all errors vs fail-fast on first error).

Exceptions
----------
PanderaValidationError
    Custom exception raised when validation fails. Wraps Pandera's SchemaError or
    SchemaErrors with additional context including table name and schema file path
    for enhanced debugging and error handling.

Notes
-----
**Key Features**

- **Zero-setup validation**: Auto-generates schemas on first use by introspecting data
- **Incremental refinement**: Generated schemas serve as customizable templates
- **Version control friendly**: Schemas are plain Python files suitable for git
- **Comprehensive error reporting**: Lazy validation collects all errors in one pass
- **Type safety**: Full integration with Python type hints and static analysis
- **Framework support**: Works with pandas and PySpark DataFrames

**Validation Workflow**

The validation process follows a two-phase approach:

1. **Schema Management** (Auto-generation on first use)
   - Check if schema file exists at ``{config_path}/pandera_schemas/{category}/{dataset}.py``
   - If missing, introspect data structure and generate schema script
   - Save generated schema as editable Python file

2. **Validation Execution** (Every use)
   - Load schema script as Python module
   - Extract DataFrameSchema object from module
   - Execute validation: ``schema.validate(data, lazy=parameters.lazy)``
   - Return validated data or raise PanderaValidationError

**Schema Organization**

Schemas are organized hierarchically based on validation names following the
"category.dataset" convention:

.. code-block:: text

    config/validators/pandera_schemas/
    ├── raw/
    │   ├── customers.py
    │   └── orders.py
    ├── processed/
    │   ├── customers.py
    │   └── sales_summary.py
    └── gold/
        └── analytics.py

**Error Collection Strategies**

The ``lazy`` parameter controls error reporting:

- **lazy=True (default)**: Collects all validation errors across the entire dataset
  before raising exception. Provides comprehensive error reporting, showing all
  violations in a single validation run. Recommended for production.
- **lazy=False**: Raises exception immediately on first validation failure. Useful
  for debugging when you want to fix errors incrementally.

**Comparison with Great Expectations**

Use PanderaValidator when:

- You need lightweight, pandas-native validation
- You prefer Python-based schema definitions over YAML/JSON
- You want tight integration with type hints and static analysis
- Your team is comfortable with code-based configuration

Use GXValidator when:

- You need profiling and automatic expectation generation
- You want data documentation websites (Data Docs)
- You need enterprise features (cloud backends, data quality dashboards)
- You prefer declarative YAML/JSON configuration

See Also
--------
adc_toolkit.data.ValidatedDataCatalog : Data catalog with integrated validation.
adc_toolkit.data.validators.gx.GXValidator : Alternative validator using Great Expectations.
adc_toolkit.data.validators.no_validator.NoValidator : No-op validator for testing.
adc_toolkit.data.abs.DataValidator : Protocol defining the validator interface.
pandera.DataFrameSchema : Underlying Pandera schema class used for validation.

Examples
--------
Basic validator setup and usage:

>>> from pathlib import Path
>>> from adc_toolkit.data.validators.pandera import PanderaValidator
>>> import pandas as pd
>>>
>>> # Create validator
>>> validator = PanderaValidator.in_directory("config/validators")
>>>
>>> # Create sample data
>>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]})
>>>
>>> # First validation: auto-generates schema
>>> validated = validator.validate("raw.customers", df)
>>> # Schema created at: config/validators/pandera_schemas/raw/customers.py

Customizing auto-generated schemas:

>>> # After first validation, edit the generated schema file:
>>> # File: config/validators/pandera_schemas/raw/customers.py
>>> #
>>> # import pandera.pandas as pa
>>> #
>>> # schema = pa.DataFrameSchema({
>>> #     "id": pa.Column(
>>> #         "int64",
>>> #         checks=[
>>> #             pa.Check.greater_than(0),  # Add: IDs must be positive
>>> #             pa.Check(lambda s: s.is_unique, element_wise=False),  # Add: unique
>>> #         ],
>>> #     ),
>>> #     "name": pa.Column("object"),
>>> #     "age": pa.Column(
>>> #         "int64",
>>> #         checks=[pa.Check.in_range(0, 120)],  # Add: realistic age range
>>> #     ),
>>> # })
>>>
>>> # Subsequent validations use customized schema
>>> validated = validator.validate("raw.customers", df)

Using custom parameters for fail-fast validation:

>>> from adc_toolkit.data.validators.pandera import PanderaParameters
>>>
>>> # Create validator with fail-fast mode
>>> params = PanderaParameters(lazy=False)
>>> validator_debug = PanderaValidator(config_path="config/validators", parameters=params)
>>>
>>> try:
...     validator_debug.validate("raw.customers", invalid_df)
... except Exception as e:
...     print(f"First error: {e.original_error}")

Integration with ValidatedDataCatalog:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> from adc_toolkit.data.validators.pandera import PanderaValidator
>>>
>>> # Create catalog with Pandera validator
>>> catalog = ValidatedDataCatalog.in_directory(
...     path="config", validator=PanderaValidator.in_directory("config/validators")
... )
>>>
>>> # Load data (automatically validated)
>>> df = catalog.load("raw.customers")
>>>
>>> # Process data
>>> processed_df = transform(df)
>>>
>>> # Save data (automatically validated before saving)
>>> catalog.save("processed.customers", processed_df)

Handling validation errors with comprehensive reporting:

>>> from adc_toolkit.data.validators.pandera import PanderaValidator, PanderaValidationError
>>>
>>> validator = PanderaValidator.in_directory("config/validators")
>>>
>>> # Invalid data
>>> invalid_df = pd.DataFrame(
...     {
...         "id": [1, -2, 3],  # Invalid: negative ID
...         "name": ["Alice", "Bob", None],  # Invalid: null name
...         "age": [25, 30, 150],  # Invalid: unrealistic age
...     }
... )
>>>
>>> try:
...     validator.validate("raw.customers", invalid_df)
... except PanderaValidationError as e:
...     print(f"Validation failed for: {e.table_name}")
...     print(f"Schema file: {e.schema_path}")
...     print(f"All errors: {e.original_error}")
...     # With lazy=True, all validation errors are included

Data pipeline with validation at multiple stages:

>>> def data_pipeline():
...     validator = PanderaValidator.in_directory("config/validators")
...
...     # Load and validate raw data
...     raw_data = load_raw_data()
...     validated_raw = validator.validate("raw.input", raw_data)
...
...     # Transform with confidence
...     transformed = transform(validated_raw)
...
...     # Validate intermediate results
...     validated_intermediate = validator.validate("intermediate.transformed", transformed)
...
...     # Final processing
...     final = aggregate(validated_intermediate)
...
...     # Validate output before downstream consumption
...     validated_output = validator.validate("gold.output", final)
...
...     return validated_output

Using with PySpark DataFrames:

>>> from pyspark.sql import SparkSession
>>>
>>> spark = SparkSession.builder.getOrCreate()
>>> spark_df = spark.createDataFrame([(1, "Alice", 25), (2, "Bob", 30)], ["id", "name", "age"])
>>>
>>> validator = PanderaValidator.in_directory("config/validators")
>>> validated_spark = validator.validate("raw.spark_customers", spark_df)
>>> # Auto-generates PySpark-compatible schema with pyspark.sql.types imports
"""

from adc_toolkit.data.validators.pandera.parameters import PanderaParameters
from adc_toolkit.data.validators.pandera.validator import PanderaValidator


__all__ = ["PanderaParameters", "PanderaValidator"]
