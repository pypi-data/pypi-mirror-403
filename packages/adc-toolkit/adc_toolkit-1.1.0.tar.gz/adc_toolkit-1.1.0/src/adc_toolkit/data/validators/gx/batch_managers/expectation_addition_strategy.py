"""
Strategy pattern implementations for adding expectations to Great Expectations suites.

This module defines the strategy pattern for adding expectations to expectation suites
in Great Expectations (GX). Expectations are business rules or data quality checks that
define what valid data should look like (e.g., column types, value ranges, uniqueness
constraints). The strategy pattern allows flexible, swappable approaches to populating
expectation suites with these data quality rules.

Different strategies serve different use cases:

- **SkipExpectationAddition**: For pre-existing, manually defined expectation suites
  that should not be modified programmatically.
- **SchemaExpectationAddition**: For auto-generating schema validation expectations from
  a DataFrame's structure, "freezing" the expected schema for future validations.

These strategies integrate with the BatchManager to coordinate expectation suite
creation and population within the broader GX validation workflow. All strategies
conform to the ExpectationAdditionStrategy protocol, enabling polymorphic usage.

Classes
-------
ExpectationAdditionStrategy
    Protocol defining the interface for expectation addition strategies.
SkipExpectationAddition
    Strategy that skips expectation addition entirely.
SchemaExpectationAddition
    Strategy that auto-generates schema expectations from DataFrame structure.

See Also
--------
adc_toolkit.data.validators.gx.batch_managers.batch_manager.BatchManager :
    Manages batches and coordinates expectation addition strategies.
adc_toolkit.data.validators.gx.batch_managers.expectation_addition.ValidatorBasedExpectationAddition :
    Low-level utility for adding expectations via GX Validator API.
adc_toolkit.data.validators.gx.custom_expectations.expect_batch_schema_to_match_dict.ExpectBatchSchemaToMatchDict :
    Custom GX expectation for validating DataFrame schema against a dictionary specification.
adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_schema :
    Utility function for extracting schema metadata from DataFrames.

Notes
-----
The strategy pattern is implemented using Protocol (structural subtyping) rather than
abstract base classes. This provides more flexibility and better type checking support
while maintaining a clear contract for strategy implementations.

Expectation suites in Great Expectations serve as collections of expectations that
define the data quality rules for a specific dataset. Each suite is associated with
a data asset and can contain zero or more expectations. The strategies in this module
determine how (and if) these suites are populated with expectations.

Examples
--------
Use SkipExpectationAddition when working with pre-defined expectation suites:

>>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import SkipExpectationAddition
>>> import pandas as pd
>>> from great_expectations.data_context import EphemeralDataContext
>>>
>>> df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
>>> context = EphemeralDataContext()
>>> batch_manager = BatchManager("my_data", df, context)
>>> strategy = SkipExpectationAddition()
>>> strategy.add_expectations(batch_manager)  # Does nothing

Use SchemaExpectationAddition to auto-generate schema validation:

>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import SchemaExpectationAddition
>>> strategy = SchemaExpectationAddition()
>>> strategy.add_expectations(batch_manager)  # Adds schema expectation
>>> suite = context.get_expectation_suite(f"{batch_manager.name}_suite")
>>> len(suite.expectations)  # Should have 1 schema expectation
1
"""

from typing import Protocol

from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import ValidatorBasedExpectationAddition
from adc_toolkit.data.validators.gx.custom_expectations.expect_batch_schema_to_match_dict import (  # noqa
    ExpectBatchSchemaToMatchDict,
)
from adc_toolkit.data.validators.table_utils.table_properties import extract_dataframe_schema


class ExpectationAdditionStrategy(Protocol):
    """
    Protocol defining the interface for expectation addition strategies.

    This protocol establishes a contract that all expectation addition strategies
    must fulfill. It uses Python's structural subtyping (PEP 544) to define the
    required interface without requiring explicit inheritance. Any class that
    implements an ``add_expectations`` method with the correct signature is
    considered a valid strategy.

    The protocol enables polymorphic usage of different strategies while maintaining
    static type safety. Strategy implementations can be freely substituted as long
    as they satisfy the protocol's interface requirements.

    Methods
    -------
    add_expectations(batch_manager)
        Add expectations to the expectation suite associated with the batch.

    See Also
    --------
    SkipExpectationAddition : Concrete strategy that skips expectation addition.
    SchemaExpectationAddition : Concrete strategy that adds schema validation expectations.
    BatchManager : Context object passed to strategies containing batch metadata.

    Notes
    -----
    This is a Protocol class, not an abstract base class. Implementers do not need
    to explicitly inherit from this protocol. The Python type checker will recognize
    any class with the correct method signature as conforming to this protocol.

    The strategy pattern is used here to decouple the expectation addition logic
    from the BatchManager that orchestrates the validation workflow. This allows
    different expectation addition behaviors to be selected at runtime based on
    configuration or user preferences.

    Examples
    --------
    Define a custom strategy conforming to this protocol:

    >>> class CustomExpectationStrategy:
    ...     def add_expectations(self, batch_manager: BatchManager) -> None:
    ...         # Custom logic to add expectations
    ...         print(f"Adding custom expectations for {batch_manager.name}")
    >>> # No explicit inheritance needed - structural subtyping
    >>> strategy: ExpectationAdditionStrategy = CustomExpectationStrategy()
    >>> # Type checker validates conformance to protocol

    Use the protocol for type hints:

    >>> def apply_strategy(batch_manager: BatchManager, strategy: ExpectationAdditionStrategy) -> None:
    ...     strategy.add_expectations(batch_manager)
    """

    def add_expectations(self, batch_manager: BatchManager) -> None:
        """
        Add expectations to the expectation suite associated with the batch.

        This method is called by the BatchManager or validation coordinator to
        populate an expectation suite with data quality expectations. The specific
        expectations added (if any) depend on the concrete strategy implementation.

        Parameters
        ----------
        batch_manager : BatchManager
            The batch manager instance containing:
            - ``name``: Name of the data asset, used to identify the expectation suite
            - ``data``: The actual data object (DataFrame) to validate
            - ``data_context``: GX data context for accessing/modifying expectation suites
            - ``batch_request``: BatchRequest for creating validators

        Returns
        -------
        None
            This method modifies the expectation suite in-place within the data context.
            It does not return a value.

        See Also
        --------
        BatchManager : Container for batch metadata and context.
        great_expectations.data_context.AbstractDataContext.get_expectation_suite :
            Retrieve an expectation suite by name.
        great_expectations.data_context.AbstractDataContext.add_or_update_expectation_suite :
            Create or update an expectation suite.

        Notes
        -----
        Implementations of this method should:

        1. Retrieve the appropriate expectation suite from the data context using
           the batch manager's name
        2. Add zero or more expectations to the suite based on the strategy's logic
        3. Ensure the suite is properly saved/updated in the data context

        The method is designed to be idempotent when possible - calling it multiple
        times should not create duplicate expectations unless the strategy explicitly
        allows this behavior.

        Examples
        --------
        Call this method from a validation workflow:

        >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
        >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
        ...     SchemaExpectationAddition,
        ... )
        >>> import pandas as pd
        >>> from great_expectations.data_context import EphemeralDataContext
        >>>
        >>> df = pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
        >>> context = EphemeralDataContext()
        >>> context.add_or_update_expectation_suite("my_data_suite")
        >>> batch_manager = BatchManager("my_data", df, context)
        >>> strategy = SchemaExpectationAddition()
        >>> strategy.add_expectations(batch_manager)
        >>> suite = context.get_expectation_suite("my_data_suite")
        >>> len(suite.expectations) > 0
        True
        """
        ...


class SkipExpectationAddition:
    """
    Strategy that bypasses automatic expectation addition to expectation suites.

    This strategy is a no-op implementation that intentionally does nothing when
    called. It is used when expectation suites have been pre-defined manually or
    through other means, and should not be modified programmatically during the
    validation workflow.

    Common use cases include:

    - Working with production expectation suites that are version-controlled and
      should not be modified by automated processes
    - Using manually crafted expectations that require domain expertise
    - Leveraging expectation suites created through Great Expectations' interactive
      workflow or profilers
    - Preventing accidental modification of carefully tuned expectations

    This strategy conforms to the ExpectationAdditionStrategy protocol, allowing it
    to be used interchangeably with other strategies in validation workflows.

    Methods
    -------
    add_expectations(batch_manager)
        No-op method that does not modify the expectation suite.

    See Also
    --------
    ExpectationAdditionStrategy : Protocol defining the strategy interface.
    SchemaExpectationAddition : Alternative strategy that adds schema expectations.
    BatchManager : Context object containing batch metadata and data context.

    Notes
    -----
    While this strategy does nothing, it is not a code smell or placeholder. It
    represents the intentional decision to skip automatic expectation addition,
    which is a valid and important use case in production data validation workflows.

    The strategy pattern allows this no-op behavior to be explicitly configured
    rather than relying on conditional logic scattered throughout the codebase.
    This makes the intent clear and the behavior predictable.

    When using this strategy, ensure that:

    1. The expectation suite already exists in the data context
    2. The suite contains the necessary expectations for validation
    3. The suite is associated with the correct data asset name

    If the expectation suite does not exist or is empty, validation may pass
    trivially (all expectations are satisfied when there are no expectations),
    which could mask data quality issues.

    Examples
    --------
    Use when working with pre-defined expectation suites:

    >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import SkipExpectationAddition
    >>> import pandas as pd
    >>> from great_expectations.data_context import EphemeralDataContext
    >>>
    >>> # Setup: create a pre-populated expectation suite
    >>> df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    >>> context = EphemeralDataContext()
    >>> suite = context.add_or_update_expectation_suite("my_data_suite")
    >>> # Manually add expectations to the suite
    >>> # ... (expectation addition code here)
    >>>
    >>> # Use SkipExpectationAddition to preserve the manual expectations
    >>> batch_manager = BatchManager("my_data", df, context)
    >>> strategy = SkipExpectationAddition()
    >>> strategy.add_expectations(batch_manager)  # Does nothing
    >>> # Suite remains unchanged

    Combine with validation workflow:

    >>> # The strategy can be configured based on environment or config
    >>> if use_manual_expectations:
    ...     strategy = SkipExpectationAddition()
    ... else:
    ...     strategy = SchemaExpectationAddition()
    >>> strategy.add_expectations(batch_manager)
    """

    def add_expectations(self, batch_manager: BatchManager) -> None:
        """
        No-op method that intentionally does not add any expectations.

        This method is called during the validation workflow but performs no
        operations. It exists to satisfy the ExpectationAdditionStrategy protocol
        while explicitly indicating that no automatic expectation addition should
        occur.

        Parameters
        ----------
        batch_manager : BatchManager
            The batch manager instance containing batch metadata and data context.
            This parameter is accepted for protocol compliance but is not used.

        Returns
        -------
        None
            The method returns immediately without modifying any state.

        See Also
        --------
        SchemaExpectationAddition.add_expectations : Alternative that adds schema expectations.
        ExpectationAdditionStrategy.add_expectations : Protocol method definition.

        Notes
        -----
        This method performs no I/O operations, does not access the data context,
        and has no side effects. It is safe to call multiple times.

        The implementation is intentionally minimal to clearly communicate that
        this is a no-op strategy. Adding logging or other operations would obscure
        the intent.

        Examples
        --------
        Call directly (though typically invoked by validation framework):

        >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
        >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
        ...     SkipExpectationAddition,
        ... )
        >>> import pandas as pd
        >>> from great_expectations.data_context import EphemeralDataContext
        >>>
        >>> df = pd.DataFrame({"x": [1, 2, 3]})
        >>> context = EphemeralDataContext()
        >>> context.add_or_update_expectation_suite("test_suite")
        >>> batch_manager = BatchManager("test", df, context)
        >>> initial_suite = context.get_expectation_suite("test_suite")
        >>> initial_count = len(initial_suite.expectations)
        >>>
        >>> strategy = SkipExpectationAddition()
        >>> strategy.add_expectations(batch_manager)
        >>>
        >>> final_suite = context.get_expectation_suite("test_suite")
        >>> final_count = len(final_suite.expectations)
        >>> assert initial_count == final_count  # Unchanged
        """


class SchemaExpectationAddition:
    """
    Strategy that auto-generates schema validation expectations from DataFrame structure.

    This strategy automatically creates a schema expectation that "freezes" the current
    structure of a DataFrame, capturing its column names and data types as a validation
    rule. Future validations will verify that incoming data matches this frozen schema,
    catching schema drift, type mismatches, or missing/unexpected columns.

    The strategy uses the custom ``expect_batch_schema_to_match_dict`` expectation to
    validate that a DataFrame's schema matches a dictionary specification mapping
    column names to data types. This provides more comprehensive schema validation than
    individual column expectations.

    Use cases:

    - **Schema contract enforcement**: Ensure data pipelines receive data with the
      expected structure
    - **Type safety**: Catch data type changes that could break downstream processing
    - **Column presence validation**: Detect missing or extra columns that violate
      the expected schema
    - **Automated schema capture**: Generate validation rules from reference data
      without manual expectation authoring

    The strategy is idempotent - if the expectation suite already contains expectations,
    it will not add duplicate schema expectations. This prevents redundant validations
    and allows safe re-execution.

    Attributes
    ----------
    None
        This class maintains no state between method calls.

    Methods
    -------
    add_expectations(batch_manager)
        Add schema validation expectation if the suite is empty.
    _check_if_expectation_exists(batch_manager)
        Check whether the expectation suite already contains expectations.

    See Also
    --------
    ExpectationAdditionStrategy : Protocol defining the strategy interface.
    SkipExpectationAddition : Alternative strategy that skips expectation addition.
    adc_toolkit.data.validators.gx.custom_expectations.expect_batch_schema_to_match_dict.ExpectBatchSchemaToMatchDict :
        Custom GX expectation for schema validation.
    adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_schema :
        Utility for extracting schema metadata from DataFrames.
    adc_toolkit.data.validators.gx.batch_managers.expectation_addition.ValidatorBasedExpectationAddition :
        Low-level utility for adding expectations via GX Validator API.

    Notes
    -----
    **Schema Freezing Concept**

    "Freezing" a schema means capturing the current DataFrame structure and using it
    as a reference point for future validations. This is analogous to:

    - Database schema definitions (CREATE TABLE statements)
    - API contracts (OpenAPI specifications)
    - Type annotations in statically typed languages

    The frozen schema becomes a data quality gate - data that doesn't match is
    rejected before it can cause downstream failures.

    **Idempotency Guarantee**

    The strategy checks if the expectation suite already contains expectations before
    adding new ones. If any expectations exist (even unrelated ones), the schema
    expectation will not be added. This prevents:

    - Duplicate expectations that slow down validation
    - Conflicts between multiple schema expectations
    - Unexpected modifications to carefully curated expectation suites

    **Supported DataFrame Types**

    The strategy works with any DataFrame type supported by the
    ``extract_dataframe_schema`` utility function, including:

    - pandas DataFrames
    - PySpark DataFrames
    - Other data structures conforming to the Data protocol

    **Expectation Suite Naming Convention**

    The strategy assumes expectation suites follow the naming pattern:
    ``{batch_manager.name}_suite``

    Ensure BatchManager instances are initialized with appropriate names to avoid
    suite naming conflicts.

    Examples
    --------
    Auto-generate schema expectations from a pandas DataFrame:

    >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
    ...     SchemaExpectationAddition,
    ... )
    >>> import pandas as pd
    >>> from great_expectations.data_context import EphemeralDataContext
    >>>
    >>> # Create sample data
    >>> df = pd.DataFrame(
    ...     {
    ...         "user_id": [1, 2, 3],
    ...         "username": ["alice", "bob", "charlie"],
    ...         "age": [25, 30, 35],
    ...         "balance": [100.50, 200.75, 150.25],
    ...     }
    ... )
    >>>
    >>> # Setup GX context and batch manager
    >>> context = EphemeralDataContext()
    >>> context.add_or_update_expectation_suite("users_suite")
    >>> batch_manager = BatchManager("users", df, context)
    >>>
    >>> # Apply schema freezing strategy
    >>> strategy = SchemaExpectationAddition()
    >>> strategy.add_expectations(batch_manager)
    >>>
    >>> # Verify the schema expectation was added
    >>> suite = context.get_expectation_suite("users_suite")
    >>> len(suite.expectations)
    1
    >>> suite.expectations[0]["expectation_type"]
    'expect_batch_schema_to_match_dict'
    >>> suite.expectations[0]["kwargs"]["schema"]
    {'user_id': 'int64', 'username': 'object', 'age': 'int64', 'balance': 'float64'}

    Use in a validation workflow with configuration-based strategy selection:

    >>> # Configuration determines which strategy to use
    >>> config = {"auto_generate_schema": True}
    >>>
    >>> if config["auto_generate_schema"]:
    ...     strategy = SchemaExpectationAddition()
    ... else:
    ...     strategy = SkipExpectationAddition()
    >>>
    >>> strategy.add_expectations(batch_manager)

    Demonstrate idempotency - calling twice doesn't duplicate expectations:

    >>> initial_count = len(context.get_expectation_suite("users_suite").expectations)
    >>> strategy.add_expectations(batch_manager)  # First call
    >>> after_first = len(context.get_expectation_suite("users_suite").expectations)
    >>> strategy.add_expectations(batch_manager)  # Second call
    >>> after_second = len(context.get_expectation_suite("users_suite").expectations)
    >>> assert after_first == after_second  # No duplicates
    """

    def _check_if_expectation_exists(self, batch_manager: BatchManager) -> bool:
        """
        Check if the expectation suite already contains any expectations.

        This method determines whether expectations have already been added to the
        suite associated with the batch manager. It serves as an idempotency guard
        to prevent duplicate schema expectations from being added when the strategy
        is invoked multiple times.

        The check is simple: if the suite contains any expectations (regardless of
        type), the method returns True. This prevents schema expectations from being
        added to suites that have been manually curated or populated by other means.

        Parameters
        ----------
        batch_manager : BatchManager
            The batch manager instance containing:
            - ``name``: Used to identify the expectation suite (pattern: "{name}_suite")
            - ``data_context``: GX data context for accessing expectation suites

        Returns
        -------
        bool
            True if the expectation suite contains one or more expectations,
            False if the suite is empty (no expectations defined).

        Raises
        ------
        great_expectations.exceptions.DataContextError
            If the expectation suite does not exist in the data context.
            This typically indicates the suite was not created before attempting
            to add expectations.

        See Also
        --------
        add_expectations : Uses this method to determine whether to add schema expectations.
        great_expectations.data_context.AbstractDataContext.get_expectation_suite :
            Retrieves the expectation suite from the data context.

        Notes
        -----
        **Naming Convention**

        The method assumes expectation suites follow the naming pattern:
        ``{batch_manager.name}_suite``

        For example, if the BatchManager has name "customer_data", the suite name
        will be "customer_data_suite". Ensure your suite naming follows this
        convention to avoid lookup failures.

        **Expectation Suite Pre-existence**

        This method expects the expectation suite to already exist in the data
        context. If you encounter errors about missing suites, ensure the suite
        is created (possibly empty) before the strategy is invoked:

        >>> context.add_or_update_expectation_suite(f"{batch_manager.name}_suite")

        **All-or-Nothing Check**

        The method does not distinguish between different types of expectations.
        Any expectation in the suite (schema-related or otherwise) will cause this
        method to return True. This is intentionally conservative to avoid
        accidentally modifying suites with manually defined expectations.

        If you need more granular control (e.g., only check for schema expectations),
        you would need to inspect the expectation types rather than just the count.

        Examples
        --------
        Check an empty expectation suite:

        >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
        >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
        ...     SchemaExpectationAddition,
        ... )
        >>> import pandas as pd
        >>> from great_expectations.data_context import EphemeralDataContext
        >>>
        >>> df = pd.DataFrame({"col1": [1, 2, 3]})
        >>> context = EphemeralDataContext()
        >>> context.add_or_update_expectation_suite("test_suite")
        >>> batch_manager = BatchManager("test", df, context)
        >>>
        >>> strategy = SchemaExpectationAddition()
        >>> strategy._check_if_expectation_exists(batch_manager)
        False

        Check after adding expectations:

        >>> strategy.add_expectations(batch_manager)
        >>> strategy._check_if_expectation_exists(batch_manager)
        True

        Handle multiple invocations (demonstrates idempotency guard):

        >>> # First check - no expectations
        >>> exists_before = strategy._check_if_expectation_exists(batch_manager)
        >>> # Add expectations
        >>> if not exists_before:
        ...     strategy.add_expectations(batch_manager)
        >>> # Second check - expectations now exist
        >>> exists_after = strategy._check_if_expectation_exists(batch_manager)
        >>> # Attempting to add again will be skipped
        >>> strategy.add_expectations(batch_manager)  # No-op due to check
        """
        suite = batch_manager.data_context.get_expectation_suite(expectation_suite_name=f"{batch_manager.name}_suite")
        return len(suite.expectations) > 0

    def add_expectations(self, batch_manager: BatchManager) -> None:
        """
        Add schema validation expectation to the suite if it is empty.

        This method auto-generates a schema expectation that captures the current
        DataFrame's structure (column names and data types) and adds it to the
        expectation suite. The schema is extracted from the batch manager's data
        and stored as an expectation that future validations must satisfy.

        The method is idempotent - it only adds the schema expectation if the suite
        is empty (contains no expectations). If expectations already exist, the
        method returns immediately without modification. This prevents duplicate
        expectations and preserves manually curated suites.

        The generated expectation uses the custom ``expect_batch_schema_to_match_dict``
        expectation type, which validates that a DataFrame's schema matches a
        dictionary specification.

        Parameters
        ----------
        batch_manager : BatchManager
            The batch manager instance containing:
            - ``name``: Identifies the expectation suite (pattern: "{name}_suite")
            - ``data``: The DataFrame whose schema will be captured
            - ``data_context``: GX data context for accessing/modifying expectation suites
            - ``batch_request``: Used by ValidatorBasedExpectationAddition for creating validators

        Returns
        -------
        None
            The method modifies the expectation suite in-place within the data context.
            It does not return a value.

        Raises
        ------
        great_expectations.exceptions.DataContextError
            If the expectation suite does not exist in the data context.
        TypeError
            If the data in the batch manager is not a supported DataFrame type.
        KeyError
            If the batch manager's data lacks required attributes (columns, dtypes).

        See Also
        --------
        _check_if_expectation_exists : Determines whether to add the schema expectation.
        adc_toolkit.data.validators.gx.batch_managers.expectation_addition.ValidatorBasedExpectationAddition :
            Utility used internally to add expectations via GX Validator API.
        adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_schema :
            Extracts schema metadata (column names and types) from DataFrames.
        adc_toolkit.data.validators.gx.custom_expectations.expect_batch_schema_to_match_dict.ExpectBatchSchemaToMatchDict :
            Custom GX expectation that validates DataFrame schema against a dictionary.

        Notes
        -----
        **Schema Extraction Process**

        The method follows this workflow:

        1. Check if the suite already has expectations using ``_check_if_expectation_exists``
        2. If the suite is empty, extract the DataFrame schema using ``extract_dataframe_schema``
        3. Create an expectation dictionary with the extracted schema
        4. Add the expectation using ``ValidatorBasedExpectationAddition``

        **Schema Dictionary Format**

        The extracted schema is a dictionary mapping column names (str) to data type
        names (str). For pandas DataFrames, this looks like:

        >>> {"col1": "int64", "col2": "float64", "col3": "object"}

        For PySpark DataFrames, the type names reflect Spark SQL types:

        >>> {"col1": "bigint", "col2": "double", "col3": "string"}

        **Idempotency Behavior**

        The method uses a simple idempotency check: if any expectations exist in the
        suite, schema addition is skipped. This is conservative - even non-schema
        expectations will trigger the skip behavior.

        This design choice prioritizes safety over flexibility. If you need to add
        schema expectations to suites that already have other expectations, you would
        need to either:

        - Clear the suite first (not recommended for production)
        - Use ValidatorBasedExpectationAddition directly with custom logic
        - Modify this strategy to check for specific expectation types

        **Expectation Suite Pre-existence**

        The expectation suite must exist before this method is called. Typically,
        the suite is created during validator initialization:

        >>> context.add_or_update_expectation_suite(f"{batch_manager.name}_suite")

        If the suite doesn't exist, a DataContextError will be raised.

        **Custom Expectation Registration**

        The ``expect_batch_schema_to_match_dict`` expectation is a custom expectation
        that must be registered with Great Expectations. The adc-toolkit handles this
        registration automatically through module imports. Ensure the custom
        expectation module is imported before using this strategy.

        Examples
        --------
        Basic usage with a pandas DataFrame:

        >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
        >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
        ...     SchemaExpectationAddition,
        ... )
        >>> import pandas as pd
        >>> from great_expectations.data_context import EphemeralDataContext
        >>>
        >>> # Create sample data with mixed types
        >>> df = pd.DataFrame(
        ...     {
        ...         "id": [1, 2, 3],
        ...         "name": ["Alice", "Bob", "Charlie"],
        ...         "score": [95.5, 87.3, 92.1],
        ...         "active": [True, False, True],
        ...     }
        ... )
        >>>
        >>> # Setup GX context and batch manager
        >>> context = EphemeralDataContext()
        >>> context.add_or_update_expectation_suite("data_suite")
        >>> batch_manager = BatchManager("data", df, context)
        >>>
        >>> # Add schema expectation
        >>> strategy = SchemaExpectationAddition()
        >>> strategy.add_expectations(batch_manager)
        >>>
        >>> # Inspect the generated expectation
        >>> suite = context.get_expectation_suite("data_suite")
        >>> expectation = suite.expectations[0]
        >>> expectation["expectation_type"]
        'expect_batch_schema_to_match_dict'
        >>> expectation["kwargs"]["schema"]
        {'id': 'int64', 'name': 'object', 'score': 'float64', 'active': 'bool'}

        Demonstrate idempotency - repeated calls don't add duplicates:

        >>> # First call adds the expectation
        >>> initial_count = len(context.get_expectation_suite("data_suite").expectations)
        >>> strategy.add_expectations(batch_manager)
        >>> after_first = len(context.get_expectation_suite("data_suite").expectations)
        >>> assert after_first == initial_count + 1  # One expectation added
        >>>
        >>> # Second call is a no-op
        >>> strategy.add_expectations(batch_manager)
        >>> after_second = len(context.get_expectation_suite("data_suite").expectations)
        >>> assert after_second == after_first  # No change

        Use in a data pipeline with schema drift detection:

        >>> def validate_data(df: pd.DataFrame, name: str, context) -> bool:
        ...     # Create batch manager
        ...     batch_manager = BatchManager(name, df, context)
        ...
        ...     # On first run, freeze the schema
        ...     suite = context.get_expectation_suite(f"{name}_suite")
        ...     if len(suite.expectations) == 0:
        ...         strategy = SchemaExpectationAddition()
        ...         strategy.add_expectations(batch_manager)
        ...
        ...     # Validate against the frozen schema
        ...     validator = context.get_validator(batch_request=batch_manager.batch_request)
        ...     results = validator.validate()
        ...     return results.success
        >>>
        >>> # First call freezes the schema
        >>> validate_data(df, "pipeline_data", context)
        True
        >>> # Subsequent calls validate against frozen schema
        >>> validate_data(df, "pipeline_data", context)
        True
        >>> # Data with different schema fails validation
        >>> bad_df = pd.DataFrame({"id": [1, 2], "wrong_column": ["x", "y"]})
        >>> validate_data(bad_df, "pipeline_data", context)
        False
        """
        if not self._check_if_expectation_exists(batch_manager):
            ValidatorBasedExpectationAddition().add_expectations(
                batch_manager,
                expectations=[
                    {"expect_batch_schema_to_match_dict": {"schema": extract_dataframe_schema(batch_manager.data)}}
                ],
            )
