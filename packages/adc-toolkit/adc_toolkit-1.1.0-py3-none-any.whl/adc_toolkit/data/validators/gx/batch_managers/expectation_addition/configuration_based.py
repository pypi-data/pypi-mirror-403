"""Configuration-based expectation addition for Great Expectations validation."""

from great_expectations.expectations.expectation import ExpectationConfiguration

from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition.parse_expectations_dict import (
    parse_expectations_dict,
)


class ConfigurationBasedExpectationAddition:
    """
    Add Great Expectations to a suite from dictionary-based configuration.

    This class implements the ExpectationAddition protocol to add expectations
    to Great Expectations suites based on structured dictionary configurations.
    It provides a declarative approach to defining data validation rules without
    writing code, making it suitable for configuration-driven validation workflows.

    The class processes expectation dictionaries where each dictionary contains
    a single expectation type as the key and its parameters as the value. It
    leverages the `parse_expectations_dict` function to extract and validate
    the expectation structure before creating ExpectationConfiguration objects
    and adding them to the target suite.

    This implementation is particularly useful for:

    - Loading expectations from YAML or JSON configuration files
    - Dynamically building validation suites from user-defined configurations
    - Separating validation logic from code for better maintainability
    - Enabling non-technical users to define validation rules

    Attributes
    ----------
    None
        This class is stateless and requires no instance attributes.

    See Also
    --------
    parse_expectations_dict : Parses and validates expectation dictionary structure.
    ExpectationAddition : Protocol defining the expectation addition interface.
    BatchManager : Manages Great Expectations batches and data contexts.

    Notes
    -----
    The class expects expectation dictionaries to follow a specific format:

    - Each dictionary must contain exactly one key-value pair
    - The key is the expectation type (e.g., "expect_column_values_to_be_in_set")
    - The value is a dictionary of expectation parameters (kwargs)

    The expectation suite is retrieved using the naming convention
    "{batch_manager.name}_suite" and is automatically updated in the data
    context after all expectations are added.

    This implementation does not validate whether the expectation types exist
    in Great Expectations or whether the provided kwargs are valid for the
    expectation type. Such validation is delegated to Great Expectations itself
    when the expectations are added to the suite.

    Examples
    --------
    Basic usage with column value expectations:

    >>> from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
    >>> adder = ConfigurationBasedExpectationAddition()
    >>> expectations = [
    ...     {
    ...         "expect_column_values_to_be_in_set": {
    ...             "column": "status",
    ...             "value_set": ["active", "inactive", "pending"],
    ...         }
    ...     },
    ...     {
    ...         "expect_column_values_to_not_be_null": {
    ...             "column": "user_id",
    ...         }
    ...     },
    ... ]
    >>> adder.add_expectations(batch_manager, expectations)

    Configuration with multiple expectation types:

    >>> expectations = [
    ...     {
    ...         "expect_table_row_count_to_be_between": {
    ...             "min_value": 100,
    ...             "max_value": 10000,
    ...         }
    ...     },
    ...     {
    ...         "expect_column_mean_to_be_between": {
    ...             "column": "price",
    ...             "min_value": 0.0,
    ...             "max_value": 1000.0,
    ...         }
    ...     },
    ...     {
    ...         "expect_column_unique_value_count_to_be_between": {
    ...             "column": "product_id",
    ...             "min_value": 50,
    ...             "max_value": 500,
    ...         }
    ...     },
    ... ]
    >>> adder.add_expectations(batch_manager, expectations)

    Loading expectations from a configuration file:

    >>> import yaml
    >>> with open("expectations.yaml") as f:
    ...     config = yaml.safe_load(f)
    >>> expectations = config["expectations"]
    >>> adder = ConfigurationBasedExpectationAddition()
    >>> adder.add_expectations(batch_manager, expectations)
    """

    def add_expectations(self, batch_manager: BatchManager, expectations: list[dict]) -> None:
        """
        Add expectations to the expectation suite from configuration dictionaries.

        Parse each expectation dictionary to extract the expectation type and
        parameters, create ExpectationConfiguration objects, and add them to
        the expectation suite associated with the provided batch manager. The
        updated suite is persisted to the data context.

        This method processes expectations sequentially, ensuring each is properly
        validated and added before moving to the next. If any expectation dictionary
        is malformed, the method will raise an exception before adding subsequent
        expectations.

        Parameters
        ----------
        batch_manager : BatchManager
            The batch manager containing the data context and batch information.
            The expectation suite is retrieved using the pattern
            "{batch_manager.name}_suite" from the batch manager's data context.
        expectations : list of dict
            List of expectation dictionaries to add to the suite. Each dictionary
            must contain exactly one key-value pair where the key is the expectation
            type (string) and the value is a dictionary of expectation parameters.

            Expected format for each dictionary:
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
            This method modifies the expectation suite in place and persists
            changes to the data context but does not return a value.

        Raises
        ------
        InvalidExpectationDictionaryError
            If any expectation dictionary does not contain exactly one key-value pair.
        InvalidExpectationNameTypeError
            If the expectation type (dictionary key) is not a string.
        InvalidExpectationKwargsTypeError
            If the expectation parameters (dictionary value) are not a dictionary.

        See Also
        --------
        parse_expectations_dict : Function that validates and extracts expectation
            components from dictionary format.
        ExpectationConfiguration : Great Expectations class representing a single
            expectation with its type and parameters.

        Notes
        -----
        The method performs the following steps for each expectation:

        1. Parse the expectation dictionary using `parse_expectations_dict`
        2. Create an `ExpectationConfiguration` object with the extracted type and kwargs
        3. Add the configuration to the expectation suite
        4. Update the suite in the data context after all expectations are added

        The expectation suite must exist in the data context before calling this
        method. The suite is identified by the naming convention "{batch_manager.name}_suite".

        All expectations are added to the same suite in a single batch. If you need
        to add expectations to multiple suites, call this method separately for each
        batch manager.

        This method does not validate the semantic correctness of expectations
        (e.g., whether column names exist or parameter values are appropriate).
        Such validation occurs when Great Expectations evaluates the expectations
        against actual data.

        Examples
        --------
        Add column validation expectations:

        >>> adder = ConfigurationBasedExpectationAddition()
        >>> expectations = [
        ...     {
        ...         "expect_column_values_to_be_in_set": {
        ...             "column": "status",
        ...             "value_set": ["active", "inactive"],
        ...         }
        ...     },
        ...     {
        ...         "expect_column_values_to_not_be_null": {
        ...             "column": "user_id",
        ...         }
        ...     },
        ... ]
        >>> adder.add_expectations(batch_manager, expectations)

        Add table-level and column-level expectations:

        >>> expectations = [
        ...     {
        ...         "expect_table_row_count_to_be_between": {
        ...             "min_value": 1000,
        ...             "max_value": 100000,
        ...         }
        ...     },
        ...     {
        ...         "expect_column_mean_to_be_between": {
        ...             "column": "temperature",
        ...             "min_value": -50.0,
        ...             "max_value": 150.0,
        ...         }
        ...     },
        ... ]
        >>> adder.add_expectations(batch_manager, expectations)

        Add expectations with complex parameter types:

        >>> expectations = [
        ...     {
        ...         "expect_column_values_to_match_regex": {
        ...             "column": "email",
        ...             "regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$",
        ...         }
        ...     },
        ...     {
        ...         "expect_column_pair_values_to_be_equal": {
        ...             "column_A": "expected_total",
        ...             "column_B": "actual_total",
        ...         }
        ...     },
        ... ]
        >>> adder.add_expectations(batch_manager, expectations)
        """
        suite = batch_manager.data_context.get_expectation_suite(expectation_suite_name=f"{batch_manager.name}_suite")
        for expectation in expectations:
            expectation_type, expectation_kwargs = parse_expectations_dict(expectation_dictionary=expectation)
            expectation_configuration = ExpectationConfiguration(
                expectation_type=expectation_type,
                kwargs=expectation_kwargs,
            )
            suite.add_expectation(expectation_configuration)
        batch_manager.data_context.update_expectation_suite(suite)
