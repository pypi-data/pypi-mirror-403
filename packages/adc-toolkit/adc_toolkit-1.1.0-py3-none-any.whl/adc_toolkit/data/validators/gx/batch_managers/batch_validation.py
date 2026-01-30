"""
Batch validation orchestration for Great Expectations.

This module provides the main entry point for coordinating batch-based data validation
workflows in Great Expectations. It orchestrates the complete validation process by
coordinating multiple components: batch management, expectation suite lookup, expectation
creation, checkpoint execution, and validation result evaluation.

The validation workflow implemented in this module follows a multi-stage pipeline:

1. **Expectation Suite Lookup**: Verify that the expectation suite exists or create it
2. **Batch Creation**: Create a batch request from the data using BatchManager
3. **Expectation Addition**: Add expectations to the suite using the configured strategy
4. **Checkpoint Execution**: Run a checkpoint to validate the data against expectations
5. **Result Evaluation**: Evaluate checkpoint results and raise errors on validation failure

This module is designed for batch validation scenarios where data is validated as discrete
batches rather than continuously. Unlike the GXValidator class, which integrates with
ValidatedDataCatalog for inline validation during load/save operations, this module is
intended for standalone batch validation workflows, batch processing pipelines, and
scheduled data quality checks.

The module contains the following public functions:

- `validate_dataset` : Main orchestration function for batch validation workflow

See Also
--------
adc_toolkit.data.validators.gx.batch_managers.batch_manager : BatchManager for batch creation
adc_toolkit.data.validators.gx.batch_managers.checkpoint_manager : CheckpointManager for validation execution
adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy : Strategies for adding expectations
adc_toolkit.data.validators.gx.batch_managers.expectation_suite_lookup_strategy : Strategies for suite lookup
adc_toolkit.data.validators.gx.gx_validator : GXValidator for catalog-integrated validation

Notes
-----
**Design Patterns:**

This module implements the Orchestrator pattern, coordinating multiple specialized
managers and strategies to accomplish a complex workflow. The design emphasizes:

- **Separation of Concerns**: Each component handles one aspect of validation
- **Strategy Pattern**: Pluggable strategies for suite lookup and expectation addition
- **Fail-Fast**: Validation errors are raised immediately with detailed context
- **Idempotency**: Running the same validation multiple times produces the same result

**Typical Use Cases:**

- Batch ETL pipelines where data quality must be verified at pipeline stages
- Scheduled data quality checks that run independently of data pipelines
- One-off data validation for exploratory analysis or data migration
- Integration testing where data fixtures must meet quality standards
- Data validation in notebook workflows

**Integration Points:**

The validation workflow integrates with several Great Expectations components:

- **Data Context**: Manages expectation suites, checkpoints, and validation results
- **Datasources**: Provide access to data for validation
- **Batch Requests**: Define what data to validate
- **Checkpoints**: Execute validation and capture results
- **Expectation Suites**: Define validation rules

Examples
--------
Basic batch validation with auto-created expectation suite:

>>> from great_expectations.data_context import EphemeralDataContext
>>> import pandas as pd
>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_suite_lookup_strategy import (
...     AutoExpectationSuiteCreation,
... )
>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import SchemaExpectationAddition
>>> data_context = EphemeralDataContext()
>>> df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
>>> validated_df = validate_dataset(
...     name="my_dataset",
...     data=df,
...     data_context=data_context,
...     expectation_suite_lookup_strategy=AutoExpectationSuiteCreation,
...     expectation_addition_strategy=SchemaExpectationAddition(),
... )

Strict validation with pre-defined expectation suite:

>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_suite_lookup_strategy import (
...     CustomExpectationSuiteStrategy,
... )
>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import SkipExpectationAddition
>>> # Assume expectation suite "sales_data_suite" already exists
>>> sales_df = pd.DataFrame({"revenue": [100, 200, 300], "date": ["2024-01-01", "2024-01-02", "2024-01-03"]})
>>> validated_sales = validate_dataset(
...     name="sales_data",
...     data=sales_df,
...     data_context=data_context,
...     expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy,
...     expectation_addition_strategy=SkipExpectationAddition(),
... )

Handling validation failures:

>>> from adc_toolkit.utils.exceptions import ValidationError
>>> invalid_df = pd.DataFrame({"col1": [1, 2, None], "col2": ["a", "b", "c"]})
>>> try:
...     validate_dataset(
...         name="my_dataset",
...         data=invalid_df,
...         data_context=data_context,
...         expectation_suite_lookup_strategy=AutoExpectationSuiteCreation,
...         expectation_addition_strategy=SchemaExpectationAddition(),
...     )
... except ValidationError as e:
...     print(f"Validation failed: {e}")
...     # Handle validation failure appropriately
"""

from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext

from adc_toolkit.data.abs import Data
from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
from adc_toolkit.data.validators.gx.batch_managers.checkpoint_manager import CheckpointManager
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import ExpectationAdditionStrategy
from adc_toolkit.data.validators.gx.batch_managers.expectation_suite_lookup_strategy import (
    ExpectationSuiteLookupStrategy,
)


def validate_dataset(
    name: str,
    data: Data,
    data_context: AbstractDataContext,
    expectation_suite_lookup_strategy: ExpectationSuiteLookupStrategy,
    expectation_addition_strategy: ExpectationAdditionStrategy,
) -> Data:
    """
    Orchestrate complete batch validation workflow for a dataset.

    This function coordinates the end-to-end validation of a dataset using Great
    Expectations. It implements a multi-stage validation pipeline that ensures data
    quality by verifying the data against a suite of expectations and raising
    exceptions if validation fails.

    The validation workflow proceeds through five sequential stages:

    1. **Expectation Suite Lookup**: Verifies that the expectation suite exists in
       the data context, or handles the missing suite according to the configured
       lookup strategy (strict failure or auto-creation).

    2. **Batch Creation**: Creates a BatchManager that registers the data as a
       datasource, creates a data asset, and builds a batch request for validation.

    3. **Expectation Addition**: Adds expectations to the suite according to the
       configured addition strategy (skip if pre-defined, add schema expectations,
       or use custom expectations).

    4. **Checkpoint Execution**: Creates and runs a checkpoint that validates the
       data batch against all expectations in the suite.

    5. **Result Evaluation**: Evaluates the checkpoint result and raises a
       ValidationError if any expectations failed.

    If all stages complete successfully, the original data is returned unchanged.
    The validation is non-destructive and does not modify the input data.

    Parameters
    ----------
    name : str
        The name identifier for the dataset being validated. This name is used to:

        - Look up the expectation suite (`{name}_suite`)
        - Name the datasource in the data context
        - Name the checkpoint (`{name}_checkpoint`)
        - Identify the dataset in validation results

        The name should be descriptive and unique within the data context to avoid
        conflicts with other datasets being validated.

    data : Data
        The data object to be validated. This must be a data structure that conforms
        to the Data protocol, typically a pandas DataFrame, Spark DataFrame, or other
        tabular data structure with columns and dtypes attributes.

        The data is used to:

        - Create a batch request for validation
        - Extract schema information for schema-based expectations
        - Execute expectation validations

        The data is not modified during validation.

    data_context : AbstractDataContext
        The Great Expectations data context that manages validation resources. This
        context provides access to:

        - Expectation suites (stored validation rules)
        - Datasources (data connections and batch requests)
        - Checkpoints (validation execution configuration)
        - Validation results (historical validation outcomes)

        Typical implementations include FileDataContext (file-based storage),
        EphemeralDataContext (in-memory for testing), or CloudDataContext (cloud
        storage backends like S3, GCS, Azure Blob Storage).

    expectation_suite_lookup_strategy : ExpectationSuiteLookupStrategy
        Strategy class (not instance) that determines how to handle missing expectation
        suites. Common strategies include:

        - `CustomExpectationSuiteStrategy`: Strict mode that raises an error if the
          suite doesn't exist. Recommended for production environments where suites
          must be pre-defined and version-controlled.

        - `AutoExpectationSuiteCreation`: Lenient mode that automatically creates an
          empty suite if it doesn't exist. Useful for development and prototyping.

        The strategy is provided as a class rather than an instance to support the
        class method calling pattern used internally.

    expectation_addition_strategy : ExpectationAdditionStrategy
        Strategy instance that determines which expectations to add to the suite.
        Common strategies include:

        - `SkipExpectationAddition()`: Don't add any expectations. Use when the suite
          is pre-populated with expectations.

        - `SchemaExpectationAddition()`: Add schema validation expectations that check
          column names and types. Useful for ensuring data structure consistency.

        - Custom strategies: Implement the protocol to add domain-specific expectations.

        Unlike the lookup strategy, this is provided as an instance to allow for
        configuration through constructor parameters.

    Returns
    -------
    Data
        The original data object, unchanged. The data is returned to allow method
        chaining and to maintain a consistent interface with other validation
        functions. Validation is non-destructive; the returned data is the same
        object as the input parameter.

        Even though the data is unchanged, returning it allows for usage patterns like:

        >>> validated_data = validate_dataset(name, data, ...)
        >>> process_data(validated_data)

    Raises
    ------
    ExpectationSuiteNotFoundError
        Raised when using `CustomExpectationSuiteStrategy` and the expectation suite
        `{name}_suite` does not exist in the data context. This error indicates that
        the suite must be created before validation can proceed. The error message
        includes guidance on creating the missing suite.

    ValidationError
        Raised when one or more expectations fail during validation. The exception
        contains the full CheckpointResult object with detailed information about:

        - Which expectations failed
        - Actual values vs. expected values
        - Statistics about the validation run
        - Batch identifiers and metadata

        This error indicates that the data does not meet the quality standards
        defined in the expectation suite.

    DataContextError
        Raised when there are issues with the Great Expectations data context, such as:

        - Inability to access or create datasources
        - Problems with expectation suite storage
        - Checkpoint configuration errors
        - Data context configuration issues

    ValueError
        Raised when parameters are invalid, such as:

        - Empty or invalid dataset name
        - Invalid expectation suite names
        - Malformed batch requests

    TypeError
        Raised when the data object does not conform to the Data protocol or when
        strategy objects don't implement the required protocol methods.

    See Also
    --------
    BatchManager : Creates and manages batch requests for validation
    CheckpointManager : Executes checkpoints and evaluates validation results
    ExpectationSuiteLookupStrategy : Base class for suite lookup strategies
    ExpectationAdditionStrategy : Protocol for expectation addition strategies
    adc_toolkit.data.validators.gx.gx_validator.GXValidator : Catalog-integrated validation
    great_expectations.data_context.AbstractDataContext : GX data context interface

    Notes
    -----
    **Validation Workflow Details:**

    The validation workflow is designed to be composable and extensible through
    the strategy pattern. Each stage can be customized by providing different
    strategy implementations without modifying the core orchestration logic.

    **Stage 1: Expectation Suite Lookup**

    The lookup strategy determines whether validation can proceed. In strict mode,
    missing suites cause immediate failure, ensuring that validation rules are
    explicit and version-controlled. In lenient mode, missing suites are created
    automatically, enabling rapid prototyping and exploratory workflows.

    **Stage 2: Batch Creation**

    The BatchManager handles the complexity of registering the data with Great
    Expectations. It creates or updates a datasource, adds a dataframe asset, and
    builds a batch request that references the data. This allows GX to access the
    data during checkpoint execution.

    **Stage 3: Expectation Addition**

    The addition strategy determines which expectations are enforced. Schema
    expectations freeze the data structure (column names and types), preventing
    schema drift. Custom strategies can add domain-specific expectations like
    value ranges, pattern matching, or referential integrity checks.

    **Stage 4: Checkpoint Execution**

    The CheckpointManager creates a checkpoint configuration that links the batch
    request to the expectation suite, then runs the checkpoint. Great Expectations
    evaluates each expectation in the suite against the data batch, recording
    results for each expectation.

    **Stage 5: Result Evaluation**

    The checkpoint result indicates success only if ALL expectations pass. If any
    expectation fails, a ValidationError is raised with the complete result object,
    allowing downstream code to inspect which expectations failed and why.

    **Idempotency:**

    This function is idempotent with respect to expectation suites and checkpoints.
    Running it multiple times with the same parameters:

    - Updates the expectation suite if the addition strategy runs
    - Updates the checkpoint configuration
    - Does not accumulate duplicate expectations or checkpoints

    **Performance Considerations:**

    - Batch creation overhead is typically minimal (microseconds to milliseconds)
    - Expectation evaluation time depends on data size and expectation complexity
    - Schema expectations are fast (metadata-only checks)
    - Statistical expectations can be slow for large datasets
    - Consider sampling large datasets before validation for performance

    **Thread Safety:**

    This function is not thread-safe when using file-based data contexts, as
    multiple threads may contend for file locks on expectation suite and checkpoint
    storage. For concurrent validation, use separate data context instances or
    cloud-based data contexts designed for concurrent access.

    **Error Recovery:**

    When validation fails:

    1. The ValidationError contains complete checkpoint results
    2. The expectation suite and checkpoint remain in the data context
    3. The original data is unchanged
    4. Validation can be re-run after fixing data issues
    5. Consider logging checkpoint results for debugging

    References
    ----------
    .. [1] Great Expectations Documentation - Checkpoints
           https://docs.greatexpectations.io/docs/guides/validation/checkpoints/
    .. [2] Great Expectations Documentation - Expectation Suites
           https://docs.greatexpectations.io/docs/guides/expectations/create_manage_expectations_lp/
    .. [3] Great Expectations Documentation - Batch Requests
           https://docs.greatexpectations.io/docs/guides/connecting_to_your_data/fluent/batch_requests/

    Examples
    --------
    Basic validation with auto-created suite and schema expectations:

    >>> from great_expectations.data_context import EphemeralDataContext
    >>> import pandas as pd
    >>> from adc_toolkit.data.validators.gx.batch_managers.batch_validation import validate_dataset
    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_suite_lookup_strategy import (
    ...     AutoExpectationSuiteCreation,
    ... )
    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
    ...     SchemaExpectationAddition,
    ... )
    >>> data_context = EphemeralDataContext()
    >>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    >>> validated_df = validate_dataset(
    ...     name="customers",
    ...     data=df,
    ...     data_context=data_context,
    ...     expectation_suite_lookup_strategy=AutoExpectationSuiteCreation,
    ...     expectation_addition_strategy=SchemaExpectationAddition(),
    ... )
    >>> assert validated_df is df  # Data is unchanged

    Strict validation with pre-defined expectation suite:

    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_suite_lookup_strategy import (
    ...     CustomExpectationSuiteStrategy,
    ... )
    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import SkipExpectationAddition
    >>> # Create and configure expectation suite beforehand
    >>> suite = data_context.add_or_update_expectation_suite(expectation_suite_name="sales_data_suite")
    >>> # Add custom expectations to the suite here
    >>> # ... (expectation configuration)
    >>> sales_df = pd.DataFrame({"revenue": [100.0, 200.0, 300.0], "date": ["2024-01-01", "2024-01-02", "2024-01-03"]})
    >>> validated_sales = validate_dataset(
    ...     name="sales_data",
    ...     data=sales_df,
    ...     data_context=data_context,
    ...     expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy,
    ...     expectation_addition_strategy=SkipExpectationAddition(),
    ... )

    Handling validation failures with detailed error inspection:

    >>> from adc_toolkit.utils.exceptions import ValidationError
    >>> # Create data that violates schema expectations
    >>> df_with_schema = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    >>> validate_dataset(
    ...     name="schema_test",
    ...     data=df_with_schema,
    ...     data_context=data_context,
    ...     expectation_suite_lookup_strategy=AutoExpectationSuiteCreation,
    ...     expectation_addition_strategy=SchemaExpectationAddition(),
    ... )
    >>> # Now try with different schema
    >>> df_invalid_schema = pd.DataFrame({"col1": [1, 2, 3], "col3": ["x", "y", "z"]})  # col3 instead of col2
    >>> try:
    ...     validate_dataset(
    ...         name="schema_test",
    ...         data=df_invalid_schema,
    ...         data_context=data_context,
    ...         expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy,
    ...         expectation_addition_strategy=SkipExpectationAddition(),
    ...     )
    ... except ValidationError as e:
    ...     checkpoint_result = e.args[0]
    ...     print(f"Validation failed: {checkpoint_result['success']}")
    ...     # Inspect specific expectation failures
    ...     for validation_result in checkpoint_result.list_validation_results():
    ...         for result in validation_result.results:
    ...             if not result.success:
    ...                 print(f"Failed expectation: {result.expectation_config.expectation_type}")

    Validation pipeline for multiple datasets:

    >>> datasets = {
    ...     "customers": pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]}),
    ...     "orders": pd.DataFrame({"order_id": [101, 102], "customer_id": [1, 2]}),
    ...     "products": pd.DataFrame({"product_id": [1, 2], "price": [10.0, 20.0]}),
    ... }
    >>> validated_datasets = {}
    >>> for dataset_name, dataset in datasets.items():
    ...     validated_datasets[dataset_name] = validate_dataset(
    ...         name=dataset_name,
    ...         data=dataset,
    ...         data_context=data_context,
    ...         expectation_suite_lookup_strategy=AutoExpectationSuiteCreation,
    ...         expectation_addition_strategy=SchemaExpectationAddition(),
    ...     )
    >>> print(f"Validated {len(validated_datasets)} datasets successfully")
    Validated 3 datasets successfully

    Using in a batch processing pipeline:

    >>> def process_batch(batch_data: pd.DataFrame, batch_name: str) -> pd.DataFrame:
    ...     # Validate before processing
    ...     validated = validate_dataset(
    ...         name=batch_name,
    ...         data=batch_data,
    ...         data_context=data_context,
    ...         expectation_suite_lookup_strategy=CustomExpectationSuiteStrategy,
    ...         expectation_addition_strategy=SkipExpectationAddition(),
    ...     )
    ...     # Process validated data
    ...     processed = validated.copy()
    ...     # ... (processing logic)
    ...     return processed

    Integration with ValidatedDataCatalog workflow:

    >>> # While this function isn't used directly in ValidatedDataCatalog,
    >>> # it demonstrates the same validation principles in a batch context
    >>> from adc_toolkit.data.catalogs.validated_catalog import ValidatedDataCatalog
    >>> # ValidatedDataCatalog uses similar coordination internally for load/save operations
    """
    expectation_suite_lookup_strategy.lookup_expectation_suite(name, data_context)
    batch_manager = BatchManager(name, data, data_context)
    expectation_addition_strategy.add_expectations(batch_manager)
    CheckpointManager(batch_manager).run_checkpoint_and_evaluate()
    return data
