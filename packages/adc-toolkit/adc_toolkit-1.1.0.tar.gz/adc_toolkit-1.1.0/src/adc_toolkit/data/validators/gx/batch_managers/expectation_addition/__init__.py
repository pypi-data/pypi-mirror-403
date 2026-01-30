"""
Expectation addition implementations for Great Expectations validation.

This module provides concrete implementations of the ExpectationAddition protocol,
enabling different approaches to adding expectations to Great Expectations expectation
suites. Expectations are data quality rules that define validation criteria (e.g.,
column types, value ranges, uniqueness constraints, referential integrity).

The module offers two primary implementation strategies:

1. **Configuration-Based Addition**: Creates ExpectationConfiguration objects from
   dictionary specifications and adds them directly to suites through the data context
   API. This approach provides explicit control over expectation structure and is ideal
   for declarative, configuration-driven workflows.

2. **Validator-Based Addition**: Uses the GX Validator fluent API to add expectations
   through method calls (e.g., `validator.expect_column_values_to_be_in_set(...)`).
   This approach offers better ergonomics, automatic suite lifecycle management, and
   built-in validation feedback.

Both implementations conform to the ExpectationAddition protocol, enabling polymorphic
usage and dependency injection throughout the validation framework.

Classes
-------
ExpectationAddition
    Protocol defining the interface for expectation addition strategies. All
    implementations must provide an `add_expectations` method that processes
    expectation dictionaries and adds them to GX expectation suites.
ConfigurationBasedExpectationAddition
    Implementation that creates ExpectationConfiguration objects from dictionary
    specifications and adds them to suites using the data context API. Suitable
    for programmatic suite generation from configuration files (YAML, JSON).
ValidatorBasedExpectationAddition
    Implementation that uses the GX Validator API to add expectations through
    ergonomic method calls. Provides automatic suite management and immediate
    validation feedback. Suitable for interactive development and dynamic
    expectation generation.

See Also
--------
adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy : High-level strategies for adding expectations
adc_toolkit.data.validators.gx.batch_managers.batch_manager : BatchManager for coordinating validation workflows
great_expectations.validator.validator.Validator : GX Validator class used by validator-based implementation
great_expectations.expectations.expectation.ExpectationConfiguration : GX configuration class used by configuration-based implementation

Notes
-----
**Protocol-Based Design:**

The module uses Protocol (PEP 544) for structural subtyping, allowing any class
that implements the required `add_expectations` method to be used as an expectation
addition strategy. This provides flexibility without requiring explicit inheritance.

**Implementation Comparison:**

Configuration-Based Approach:
    Advantages:
        - Lower overhead (no validator instantiation)
        - Direct control over ExpectationConfiguration structure
        - Suitable for batch processing of many expectations
        - Explicit suite lifecycle management

    Disadvantages:
        - Less ergonomic API (requires dictionary manipulation)
        - No automatic validation feedback
        - Must manually handle suite saving

Validator-Based Approach:
    Advantages:
        - Fluent, ergonomic API with method chaining
        - Automatic suite lifecycle management
        - Built-in validation and error checking
        - IDE autocomplete support for expectation methods

    Disadvantages:
        - Higher overhead (validator instantiation required)
        - Each expectation triggers a save operation
        - Less suitable for bulk expectation addition

**Expectation Dictionary Format:**

Both implementations expect expectation specifications as dictionaries with the
following structure:

.. code-block:: python

    {
        "expectation_type_name": {
            "param1": value1,
            "param2": value2,
            ...
        }
    }

For example:

.. code-block:: python

    {"expect_column_values_to_be_in_set": {"column": "status", "value_set": ["active", "inactive", "pending"]}}

**Usage Patterns:**

- **Static Configuration**: Use ConfigurationBasedExpectationAddition when loading
  expectations from YAML/JSON configuration files that define validation rules.

- **Dynamic Generation**: Use ValidatorBasedExpectationAddition when building
  expectations dynamically based on data profiling or business logic.

- **Interactive Development**: Use ValidatorBasedExpectationAddition in notebooks
  for rapid prototyping with immediate feedback.

- **Bulk Operations**: Use ConfigurationBasedExpectationAddition when adding many
  expectations at once to minimize overhead.

**Integration Points:**

These implementations are used by:

- `SchemaExpectationAddition` strategy (uses ValidatorBasedExpectationAddition)
- Custom expectation addition strategies
- Batch validation workflows
- ValidatedDataCatalog through GXValidator

**Performance Considerations:**

- Configuration-based addition has O(n) complexity with constant per-expectation overhead
- Validator-based addition has O(n) complexity but with higher per-expectation overhead
  due to suite save operations
- For adding many expectations (n > 10), configuration-based approach is typically faster
- For interactive workflows or small numbers of expectations, validator-based approach
  provides better developer experience

Examples
--------
Using configuration-based expectation addition:

>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import (
...     ConfigurationBasedExpectationAddition,
... )
>>> adder = ConfigurationBasedExpectationAddition()
>>> expectations = [
...     {"expect_column_values_to_be_in_set": {"column": "status", "value_set": ["active", "inactive"]}},
...     {"expect_column_values_to_not_be_null": {"column": "user_id"}},
...     {"expect_column_mean_to_be_between": {"column": "age", "min_value": 0, "max_value": 120}},
... ]
>>> adder.add_expectations(batch_manager, expectations)

Using validator-based expectation addition:

>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import (
...     ValidatorBasedExpectationAddition,
... )
>>> adder = ValidatorBasedExpectationAddition()
>>> expectations = [
...     {"expect_column_to_exist": {"column": "user_id"}},
...     {"expect_column_values_to_be_unique": {"column": "user_id"}},
...     {"expect_column_values_to_match_regex": {"column": "email", "regex": r"^[\\w.-]+@[\\w.-]+\\.\\w+$"}},
... ]
>>> adder.add_expectations(batch_manager, expectations)

Loading expectations from a configuration file:

>>> import yaml
>>> with open("expectations.yaml") as f:
...     config = yaml.safe_load(f)
>>> expectations = config["dataset_expectations"]
>>> adder = ConfigurationBasedExpectationAddition()
>>> adder.add_expectations(batch_manager, expectations)

Choosing implementation based on use case:

>>> # For bulk loading from configuration
>>> if source == "config_file":
...     adder = ConfigurationBasedExpectationAddition()
... # For interactive development
... else:
...     adder = ValidatorBasedExpectationAddition()
>>> adder.add_expectations(batch_manager, expectations)

Custom implementation conforming to the protocol:

>>> class CustomExpectationAddition:
...     '''Custom implementation with logging and error handling.'''
...
...     def add_expectations(self, batch_manager, expectations):
...         '''Add expectations with custom logic.'''
...         for exp in expectations:
...             # Custom processing logic here
...             pass
>>>
>>> custom_adder: ExpectationAddition = CustomExpectationAddition()
"""

from adc_toolkit.data.validators.gx.batch_managers.expectation_addition.base import ExpectationAddition
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition.configuration_based import (
    ConfigurationBasedExpectationAddition,
)
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition.validator_based import (
    ValidatorBasedExpectationAddition,
)


__all__ = [
    "ConfigurationBasedExpectationAddition",
    "ExpectationAddition",
    "ValidatorBasedExpectationAddition",
]
