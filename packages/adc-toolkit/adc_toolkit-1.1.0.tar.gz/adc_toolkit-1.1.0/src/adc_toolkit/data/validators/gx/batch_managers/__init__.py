"""
Batch management infrastructure for Great Expectations validation workflows.

This module provides the core batch management components for orchestrating data
validation with Great Expectations (GX). Batch managers coordinate the creation
of batch requests, expectation suite management, checkpoint execution, and validation
result evaluation. They serve as the foundation for both catalog-integrated validation
(via GXValidator) and standalone batch validation workflows.

The module implements a multi-layered architecture that separates concerns across
several specialized managers and strategy classes:

**Core Components:**

1. **Batch Management**: Creates and manages GX batch requests that reference data
   for validation operations.

2. **Datasource Management**: Automatically configures GX datasources for pandas
   and PySpark DataFrames.

3. **Checkpoint Management**: Orchestrates checkpoint creation, execution, and
   result evaluation.

4. **Expectation Suite Lookup**: Provides strategies for handling missing expectation
   suites (strict mode vs. auto-creation).

5. **Expectation Addition**: Offers multiple approaches to adding expectations to
   suites (skip, schema-based, configuration-based, validator-based).

6. **Batch Validation**: Provides the `validate_dataset` function that orchestrates
   the complete validation workflow.

Classes
-------
BatchManager
    Abstract base class for managing batch requests and data context integration.
    Concrete implementations exist for pandas and PySpark DataFrames.
DatasourceManager
    Manages GX datasources for pandas and PySpark DataFrames, automatically
    detecting the DataFrame type and configuring the appropriate datasource.
CheckpointManager
    Creates, executes, and evaluates GX checkpoints for data validation.
ExpectationSuiteLookupStrategy
    Abstract base class for strategies that handle missing expectation suites.
CustomExpectationSuiteStrategy
    Strict strategy that raises an error if an expectation suite is not found.
AutoExpectationSuiteCreation
    Lenient strategy that automatically creates missing expectation suites.
ExpectationAdditionStrategy
    Protocol defining the interface for adding expectations to suites.
SkipExpectationAddition
    Strategy that bypasses automatic expectation addition (for pre-defined suites).
SchemaExpectationAddition
    Strategy that auto-generates schema validation expectations from DataFrame structure.
ExpectationAddition
    Protocol defining the interface for expectation addition implementations.
ConfigurationBasedExpectationAddition
    Adds expectations to suites from dictionary-based configuration using
    ExpectationConfiguration objects.
ValidatorBasedExpectationAddition
    Adds expectations to suites using the GX Validator API for a more ergonomic,
    method-based approach.

Functions
---------
validate_dataset
    Orchestrate the complete batch validation workflow for a dataset, coordinating
    expectation suite lookup, batch creation, expectation addition, checkpoint
    execution, and result evaluation.

See Also
--------
adc_toolkit.data.validators.gx.gx_validator : High-level validator that integrates with ValidatedDataCatalog
adc_toolkit.data.validators.gx.instant_gx_validator : Simplified validator for rapid prototyping
adc_toolkit.data.catalogs.validated_catalog : ValidatedDataCatalog that uses GXValidator
great_expectations.data_context.AbstractDataContext : GX data context interface

Notes
-----
**Design Patterns:**

This module implements several design patterns to provide flexibility and maintainability:

- **Strategy Pattern**: Used for expectation suite lookup and expectation addition
  strategies, allowing runtime selection of behaviors.
- **Factory Pattern**: Used in datasource creation to automatically select the
  appropriate datasource type based on DataFrame type.
- **Orchestrator Pattern**: The `validate_dataset` function coordinates multiple
  managers and strategies to accomplish complex validation workflows.
- **Protocol-Based Design**: Uses Python Protocols for structural subtyping,
  enabling flexible implementations without tight coupling.

**Architecture Overview:**

The batch management architecture follows a separation of concerns principle:

1. **DatasourceManager**: Handles the low-level details of registering data with GX
2. **BatchManager**: Coordinates batch request creation and dataset naming
3. **CheckpointManager**: Manages checkpoint lifecycle and result evaluation
4. **Expectation Strategies**: Provide pluggable behaviors for suite and expectation management
5. **validate_dataset**: Orchestrates all components into a cohesive workflow

**Typical Validation Workflow:**

1. Look up expectation suite (or create if using auto-creation strategy)
2. Create datasource and batch request for the data
3. Add expectations to the suite (if using schema or configuration strategies)
4. Create and execute checkpoint to validate data
5. Evaluate results and raise ValidationError if any expectations fail

**Use Cases:**

This module supports multiple validation scenarios:

- **Catalog-Integrated Validation**: Used by GXValidator for inline validation
  during load/save operations in ValidatedDataCatalog.
- **Standalone Batch Validation**: Direct usage of `validate_dataset` for batch
  processing pipelines and scheduled data quality checks.
- **Interactive Development**: Validator-based expectation addition for notebook
  workflows and exploratory data analysis.
- **Configuration-Driven Validation**: Configuration-based expectation addition for
  declarative validation rule management.

**Performance Considerations:**

- Batch request creation is lightweight (metadata operations only)
- Schema expectations are fast (no data scanning required)
- Statistical expectations can be slow for large datasets
- Consider sampling large datasets before validation
- Validator-based expectation addition incurs overhead from validator instantiation

**Thread Safety:**

The batch managers are not thread-safe when using file-based data contexts due to
potential file lock contention. For concurrent validation, use separate data context
instances or cloud-based contexts designed for concurrent access.

Examples
--------
Basic batch validation with auto-created suite and schema expectations:

>>> from great_expectations.data_context import EphemeralDataContext
>>> import pandas as pd
>>> from adc_toolkit.data.validators.gx.batch_managers import (
...     validate_dataset,
...     AutoExpectationSuiteCreation,
...     SchemaExpectationAddition,
... )
>>> context = EphemeralDataContext()
>>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
>>> validated_df = validate_dataset(
...     name="customers",
...     data=df,
...     data_context=context,
...     expectation_suite_lookup_strategy=AutoExpectationSuiteCreation,
...     expectation_addition_strategy=SchemaExpectationAddition(),
... )

Strict validation with pre-defined expectation suite:

>>> from adc_toolkit.data.validators.gx.batch_managers import (
...     CustomExpectationSuiteStrategy,
...     SkipExpectationAddition,
... )
>>> # Create and configure suite beforehand
>>> suite = context.add_or_update_expectation_suite("sales_data_suite")
>>> # Add custom expectations to the suite here
>>> sales_df = pd.DataFrame({"revenue": [100.0, 200.0], "date": ["2024-01-01", "2024-01-02"]})
>>> validated_sales = validate_dataset(
...     name="sales_data",
...     data=sales_df,
...     data_context=context,
...     expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy,
...     expectation_addition_strategy=SkipExpectationAddition(),
... )

Using individual managers for fine-grained control:

>>> from adc_toolkit.data.validators.gx.batch_managers import (
...     BatchManager,
...     CheckpointManager,
... )
>>> # Create batch manager
>>> batch_manager = BatchManager(name="my_dataset", data=df, data_context=context)
>>> # Create checkpoint manager
>>> checkpoint_manager = CheckpointManager(batch_manager)
>>> # Execute validation
>>> checkpoint_manager.run_checkpoint_and_evaluate()

Configuration-based expectation addition:

>>> from adc_toolkit.data.validators.gx.batch_managers import ConfigurationBasedExpectationAddition
>>> expectations = [
...     {"expect_column_values_to_be_in_set": {"column": "status", "value_set": ["active", "inactive"]}},
...     {"expect_column_values_to_not_be_null": {"column": "user_id"}},
... ]
>>> adder = ConfigurationBasedExpectationAddition()
>>> adder.add_expectations(batch_manager, expectations)

Handling validation failures:

>>> from adc_toolkit.utils.exceptions import ValidationError
>>> invalid_df = pd.DataFrame({"id": [1, 2, None], "name": ["a", "b", "c"]})
>>> try:
...     validate_dataset(
...         name="my_dataset",
...         data=invalid_df,
...         data_context=context,
...         expectation_suite_lookup_strategy=AutoExpectationSuiteCreation,
...         expectation_addition_strategy=SchemaExpectationAddition(),
...     )
... except ValidationError as e:
...     print(f"Validation failed: {e}")
...     # Inspect checkpoint result for details
...     checkpoint_result = e.args[0]
"""

from adc_toolkit.data.validators.gx.batch_managers.batch_validation import validate_dataset
from adc_toolkit.data.validators.gx.batch_managers.checkpoint_manager import CheckpointManager
from adc_toolkit.data.validators.gx.batch_managers.datasource_manager import DatasourceManager
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import (
    ConfigurationBasedExpectationAddition,
    ExpectationAddition,
    ValidatorBasedExpectationAddition,
)
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
    ExpectationAdditionStrategy,
    SchemaExpectationAddition,
    SkipExpectationAddition,
)
from adc_toolkit.data.validators.gx.batch_managers.expectation_suite_lookup_strategy import (
    AutoExpectationSuiteCreation,
    CustomExpectationSuiteStrategy,
    ExpectationSuiteLookupStrategy,
)


__all__ = [
    "AutoExpectationSuiteCreation",
    "CheckpointManager",
    "ConfigurationBasedExpectationAddition",
    "CustomExpectationSuiteStrategy",
    "DatasourceManager",
    "ExpectationAddition",
    "ExpectationAdditionStrategy",
    "ExpectationSuiteLookupStrategy",
    "SchemaExpectationAddition",
    "SkipExpectationAddition",
    "ValidatorBasedExpectationAddition",
    "validate_dataset",
]
