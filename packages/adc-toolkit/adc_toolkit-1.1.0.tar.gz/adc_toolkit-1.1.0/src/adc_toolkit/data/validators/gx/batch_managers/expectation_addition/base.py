"""
Expectation addition protocol for Great Expectations integration.

This module defines the Protocol interface for adding expectations to Great
Expectations expectation suites. Implementations of this protocol provide
different strategies for managing expectations (configuration-based vs.
validator-based approaches).

The primary class in this module is:

- `ExpectationAddition` : Protocol defining the interface for expectation addition

Notes
-----
This protocol enables dependency injection of different expectation management
strategies into the GX validator, supporting both configuration-based and
validator-based approaches to expectation suite management.

See Also
--------
adc_toolkit.data.validators.gx.batch_managers.expectation_addition.configuration_based : Configuration-based implementation.
adc_toolkit.data.validators.gx.batch_managers.expectation_addition.validator_based : Validator-based implementation.

Examples
--------
Import the protocol to define type annotations:

>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import ExpectationAddition
>>> def process_expectations(
...     addition: ExpectationAddition, batch_manager: BatchManager, expectations: list[dict]
... ) -> None:
...     addition.add_expectations(batch_manager, expectations)
"""

from typing import Protocol

from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager


class ExpectationAddition(Protocol):
    """
    Define interface for adding expectations to GX expectation suites.

    This protocol establishes a contract for expectation addition strategies
    used in the Great Expectations (GX) validation workflow. Implementations
    must provide a method to add expectations to a suite associated with a
    specific batch of data.

    The protocol supports two primary implementation strategies:

    1. **Configuration-based**: Creates ExpectationConfiguration objects and adds
       them to the suite through the data context's API. This approach provides
       direct control over the suite structure without creating a validator.

    2. **Validator-based**: Creates a GX Validator instance and uses its fluent
       API (e.g., `validator.expect_column_values_to_be_in_set()`) to add
       expectations. The validator automatically manages the suite lifecycle.

    Attributes
    ----------
    add_expectations : method
        Method to add expectations to an expectation suite for a batch.

    Methods
    -------
    add_expectations(batch_manager, expectations)
        Add expectations to the expectation suite associated with a batch.

    Notes
    -----
    Implementations of this protocol are used as dependency injection points
    in the GX validator to enable flexible expectation management strategies.
    The choice of strategy affects performance, API ergonomics, and the level
    of control over the expectation suite structure.

    The protocol operates on BatchManager objects, which encapsulate the data
    context, batch request, and dataset metadata required for expectation
    suite operations.

    **Expectation Addition Workflow:**

    1. Receive BatchManager and list of expectation dictionaries
    2. Parse and validate each expectation dictionary structure
    3. Retrieve or create the expectation suite from the data context
    4. Add expectations using the implementation's chosen strategy
    5. Save or update the expectation suite in the data context

    **Strategy Comparison:**

    Configuration-based approach:
        - Direct control over ExpectationConfiguration objects
        - Lower overhead (no validator instantiation)
        - Suitable for programmatic suite generation
        - Requires manual suite lifecycle management

    Validator-based approach:
        - Fluent API for ergonomic expectation definition
        - Automatic suite lifecycle management
        - Built-in validation and error checking
        - Higher overhead due to validator instantiation

    See Also
    --------
    ConfigurationBasedExpectationAddition : Adds expectations via configuration objects.
    ValidatorBasedExpectationAddition : Adds expectations via validator fluent API.
    BatchManager : Manages GX batch requests and data context integration.

    Examples
    --------
    Implementing a custom expectation addition strategy:

    >>> class CustomExpectationAddition:
    ...     '''Custom implementation of ExpectationAddition protocol.'''
    ...
    ...     def add_expectations(self, batch_manager: BatchManager, expectations: list[dict]) -> None:
    ...         '''Add expectations using custom logic.'''
    ...         suite = batch_manager.data_context.get_expectation_suite(
    ...             expectation_suite_name=f"{batch_manager.name}_suite"
    ...         )
    ...         # Custom logic to process and add expectations
    ...         for exp in expectations:
    ...             # Process and add each expectation
    ...             pass
    ...         batch_manager.data_context.update_expectation_suite(suite)

    Using an implementation with a BatchManager:

    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import (
    ...     ConfigurationBasedExpectationAddition,
    ... )
    >>> addition = ConfigurationBasedExpectationAddition()
    >>> expectations = [
    ...     {"expect_column_values_to_be_in_set": {"column": "status", "value_set": ["active", "inactive", "pending"]}},
    ...     {"expect_column_values_to_not_be_null": {"column": "user_id"}},
    ... ]
    >>> addition.add_expectations(batch_manager, expectations)
    """

    def add_expectations(self, batch_manager: BatchManager, expectations: list[dict]) -> None:
        """
        Add expectations to the expectation suite associated with a batch.

        Process a list of expectation definitions and add them to the Great
        Expectations suite corresponding to the batch managed by the provided
        BatchManager. The exact mechanism of addition depends on the
        implementation strategy (configuration-based or validator-based).

        Parameters
        ----------
        batch_manager : BatchManager
            The batch manager containing the data context, batch request, and
            dataset metadata. The expectation suite name is derived from the
            batch manager's name attribute (formatted as "{name}_suite").
            This object provides access to the GX data context and all
            necessary metadata for suite retrieval and manipulation.
        expectations : list of dict
            List of expectation definitions to add to the suite. Each dictionary
            must contain exactly one key-value pair where:

            - Key (str): The expectation type name (e.g.,
              "expect_column_values_to_be_in_set",
              "expect_table_row_count_to_equal")
            - Value (dict): Keyword arguments for the expectation, including
              required parameters like column names, thresholds, or value sets

            The dictionary format follows the structure:

            .. code-block:: python

                {
                    "expectation_type_name": {
                        "param1": value1,
                        "param2": value2,
                        ...
                    }
                }

        Returns
        -------
        None
            This method modifies the expectation suite in place through the
            data context and does not return a value.

        Raises
        ------
        InvalidExpectationDictionaryError
            If an expectation dictionary does not contain exactly one key-value
            pair. Each expectation must specify exactly one expectation type.
        InvalidExpectationNameTypeError
            If the expectation type (dictionary key) is not a string. All
            expectation type names must be strings matching GX expectation
            method names.
        InvalidExpectationKwargsTypeError
            If the expectation kwargs (dictionary value) is not a dictionary.
            Parameters for each expectation must be provided as a dict.
        great_expectations.exceptions.GreatExpectationsError
            If the Great Expectations data context or suite operations fail.
            This includes errors from suite retrieval, expectation creation,
            or suite persistence operations.

        Notes
        -----
        **Expectation Dictionary Format:**

        The expectation dictionary structure mirrors the GX expectation API.
        For example, to call `validator.expect_column_values_to_be_in_set(
        column="status", value_set=["active", "inactive"])`, the dictionary
        would be:

        .. code-block:: python

            {"expect_column_values_to_be_in_set": {"column": "status", "value_set": ["active", "inactive"]}}

        **Common Expectation Types:**

        Column-level expectations:
            - expect_column_values_to_be_in_set
            - expect_column_values_to_not_be_null
            - expect_column_values_to_be_between
            - expect_column_values_to_match_regex
            - expect_column_mean_to_be_between
            - expect_column_sum_to_be_between

        Table-level expectations:
            - expect_table_row_count_to_equal
            - expect_table_row_count_to_be_between
            - expect_table_column_count_to_equal
            - expect_table_columns_to_match_ordered_list

        For a complete list of available expectations, refer to the Great
        Expectations documentation at https://docs.greatexpectations.io/.

        **Implementation Requirements:**

        All implementations of this protocol must ensure that:

        1. The expectation suite exists or is created before adding expectations
        2. Expectation dictionaries are parsed and validated correctly (typically
           using the `parse_expectations_dict` utility function)
        3. Each expectation is added to the suite with all specified parameters
        4. The suite is properly saved or updated in the data context after
           all expectations have been added
        5. Any GX API errors are allowed to propagate with meaningful context

        **Performance Considerations:**

        Configuration-based implementations generally have lower overhead as
        they avoid creating a Validator instance. Validator-based implementations
        provide better ergonomics and automatic validation but incur the cost
        of validator instantiation for each batch.

        See Also
        --------
        ConfigurationBasedExpectationAddition : Configuration-based implementation.
        ValidatorBasedExpectationAddition : Validator-based implementation.
        parse_expectations_dict : Utility for parsing expectation dictionaries.
        BatchManager : Batch management for GX data contexts.

        Examples
        --------
        Adding column value expectations:

        >>> expectations = [
        ...     {
        ...         "expect_column_values_to_be_in_set": {
        ...             "column": "product_category",
        ...             "value_set": ["electronics", "furniture", "clothing"],
        ...         }
        ...     },
        ...     {"expect_column_values_to_be_between": {"column": "price", "min_value": 0.0, "max_value": 10000.0}},
        ... ]
        >>> expectation_addition.add_expectations(batch_manager, expectations)

        Adding table-level expectations:

        >>> expectations = [
        ...     {"expect_table_row_count_to_equal": {"value": 1000}},
        ...     {"expect_table_column_count_to_equal": {"value": 15}},
        ... ]
        >>> expectation_addition.add_expectations(batch_manager, expectations)

        Adding expectations with custom result format specifications:

        >>> expectations = [
        ...     {
        ...         "expect_column_values_to_not_be_null": {
        ...             "column": "email",
        ...             "result_format": {"result_format": "COMPLETE", "unexpected_index_column_names": ["user_id"]},
        ...         }
        ...     }
        ... ]
        >>> expectation_addition.add_expectations(batch_manager, expectations)

        Adding multiple expectations with metadata:

        >>> expectations = [
        ...     {
        ...         "expect_column_values_to_be_unique": {
        ...             "column": "transaction_id",
        ...             "meta": {"notes": "Transaction IDs must be globally unique"},
        ...         }
        ...     },
        ...     {
        ...         "expect_column_values_to_match_regex": {
        ...             "column": "email",
        ...             "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
        ...             "meta": {"notes": "Email addresses must follow standard format"},
        ...         }
        ...     },
        ... ]
        >>> expectation_addition.add_expectations(batch_manager, expectations)
        """
        ...
