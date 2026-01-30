"""
Validator-based expectation addition for Great Expectations.

This module provides a mechanism for adding expectations to Great Expectations
expectation suites using the GX Validator API. The validator-based approach
allows expectations to be added programmatically through method calls on a
validator object, which can be more intuitive than configuration-based approaches
when building expectations dynamically or interactively.

The key difference between validator-based and configuration-based expectation
addition is in how expectations are created and added:

- **Validator-based**: Calls expectation methods directly on a GX Validator object
  (e.g., ``validator.expect_column_values_to_be_in_set(column="col1", value_set=[1,2,3])``)
- **Configuration-based**: Creates ExpectationConfiguration objects and adds them
  to the suite directly through the data context

The validator-based approach is particularly useful for:

- Interactive expectation development in notebooks
- Dynamic expectation generation based on data profiling
- Leveraging IDE autocomplete and type hints for expectation parameters
- Immediate validation feedback during expectation creation

See Also
--------
ConfigurationBasedExpectationAddition : Alternative approach using ExpectationConfiguration
parse_expectations_dict : Parser for expectation dictionaries
BatchManager : Manages batch requests and data context

Examples
--------
Create and add expectations using the validator-based approach:

>>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import ValidatorBasedExpectationAddition
>>> expectation_adder = ValidatorBasedExpectationAddition()
>>> expectations = [
...     {
...         "expect_column_values_to_be_in_set": {
...             "column": "status",
...             "value_set": ["active", "inactive", "pending"],
...         }
...     },
...     {
...         "expect_column_values_to_be_between": {
...             "column": "age",
...             "min_value": 0,
...             "max_value": 120,
...         }
...     },
... ]
>>> expectation_adder.add_expectations(batch_manager, expectations)
"""

from great_expectations.validator.validator import Validator

from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition.parse_expectations_dict import (
    parse_expectations_dict,
)


class ValidatorBasedExpectationAddition:
    r"""
    Add expectations to GX expectation suites using Validator objects.

    This class implements the ExpectationAddition protocol by leveraging Great
    Expectations' Validator API to add expectations programmatically. Rather than
    creating ExpectationConfiguration objects, this approach calls expectation
    methods directly on a Validator object, which then automatically adds them
    to the associated expectation suite.

    The validator-based approach offers several advantages:

    1. **Natural API**: Expectations are added using method calls that match GX's
       standard expectation API (e.g., ``expect_column_values_to_not_be_null``).
    2. **Immediate Validation**: Each expectation can be validated against the
       batch data as it's added.
    3. **Type Safety**: IDEs can provide autocomplete and type hints for expectation
       parameters.
    4. **Automatic Suite Management**: The validator automatically handles saving
       expectations to the suite after each addition.

    This class is stateless and can be reused across multiple batch managers and
    expectation addition operations.

    Attributes
    ----------
    None
        This class maintains no internal state.

    Methods
    -------
    add_expectations(batch_manager, expectations)
        Add a list of expectations to the batch manager's expectation suite using
        a GX Validator object.

    See Also
    --------
    ConfigurationBasedExpectationAddition : Alternative implementation using ExpectationConfiguration
    ExpectationAddition : Protocol defining the expectation addition interface
    create_batch_validator : Factory function for creating GX Validator objects

    Notes
    -----
    The validator-based approach creates a new Validator object for each call to
    ``add_expectations``. The Validator object is retrieved from the data context
    using the batch manager's batch request and expectation suite name. Each
    expectation is added by calling the corresponding method on the validator
    (e.g., ``validator.expect_column_to_exist(column="col1")``), and the suite
    is saved after each expectation addition.

    This approach differs from configuration-based addition in that it uses the
    GX Validator API rather than directly manipulating ExpectationConfiguration
    objects. The validator-based approach may be slower for adding many expectations
    at once due to the suite save operation after each expectation, but it provides
    better feedback and is more suitable for interactive workflows.

    Performance considerations:

    - Each expectation triggers a save operation on the expectation suite
    - For bulk expectation addition, consider batching or using configuration-based
      approach if performance is critical
    - The validator creation overhead is incurred once per ``add_expectations`` call

    Examples
    --------
    Basic usage with a batch manager:

    >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition import ValidatorBasedExpectationAddition
    >>> adder = ValidatorBasedExpectationAddition()
    >>> expectations = [
    ...     {"expect_column_to_exist": {"column": "user_id"}},
    ...     {"expect_column_values_to_be_unique": {"column": "user_id"}},
    ... ]
    >>> adder.add_expectations(batch_manager, expectations)

    Adding multiple expectations with different types:

    >>> expectations = [
    ...     {
    ...         "expect_column_values_to_be_in_set": {
    ...             "column": "status",
    ...             "value_set": ["active", "inactive"],
    ...         }
    ...     },
    ...     {
    ...         "expect_column_values_to_be_between": {
    ...             "column": "age",
    ...             "min_value": 18,
    ...             "max_value": 100,
    ...         }
    ...     },
    ...     {
    ...         "expect_column_values_to_match_regex": {
    ...             "column": "email",
    ...             "regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
    ...         }
    ...     },
    ... ]
    >>> adder.add_expectations(batch_manager, expectations)

    Using with complex expectation parameters:

    >>> expectations = [
    ...     {
    ...         "expect_column_pair_values_A_to_be_greater_than_B": {
    ...             "column_A": "end_date",
    ...             "column_B": "start_date",
    ...             "or_equal": True,
    ...         }
    ...     },
    ... ]
    >>> adder.add_expectations(batch_manager, expectations)
    """

    def add_expectations(self, batch_manager: BatchManager, expectations: list[dict]) -> None:
        r"""
        Add expectations to the suite using a GX Validator object.

        This method creates a GX Validator object from the batch manager and uses
        it to add expectations programmatically. Each expectation dictionary is
        parsed to extract the expectation type (method name) and its parameters,
        then the corresponding method is called on the validator. After each
        expectation is added, the expectation suite is automatically saved.

        The method processes expectations sequentially, calling the appropriate
        expectation method on the validator for each one. The validator handles
        the creation of ExpectationConfiguration objects internally and adds them
        to the suite.

        Parameters
        ----------
        batch_manager : BatchManager
            The batch manager containing the data context, batch request, and
            dataset name. This is used to create the validator and identify the
            target expectation suite.
        expectations : list of dict
            A list of expectation dictionaries to add to the suite. Each dictionary
            must contain exactly one key-value pair, where:

            - The key is the expectation method name (e.g.,
              ``"expect_column_values_to_be_in_set"``)
            - The value is a dictionary of keyword arguments to pass to that
              expectation method (e.g., ``{"column": "col1", "value_set": [1, 2, 3]}``)

            The expectation method names should match GX's standard expectation API.

        Returns
        -------
        None
            This method modifies the expectation suite in place through the
            validator and does not return a value.

        Raises
        ------
        InvalidExpectationDictionaryError
            If any expectation dictionary does not contain exactly one key-value pair.
        InvalidExpectationNameTypeError
            If any expectation method name is not a string.
        InvalidExpectationKwargsTypeError
            If the parameters for any expectation are not provided as a dictionary.
        AttributeError
            If the expectation method name does not exist on the Validator object
            (i.e., it's not a valid GX expectation).
        TypeError
            If the expectation parameters don't match the expected signature for
            that expectation method.
        GreatExpectationsError
            If the data context or expectation suite cannot be accessed, or if
            there are issues saving the expectation suite.

        See Also
        --------
        create_batch_validator : Creates the GX Validator object used by this method
        parse_expectations_dict : Parses expectation dictionaries into method names and kwargs
        ConfigurationBasedExpectationAddition : Alternative approach using ExpectationConfiguration

        Notes
        -----
        This method performs the following operations for each expectation:

        1. Parse the expectation dictionary to extract the method name and parameters
        2. Call ``getattr(validator, expectation_name)(**kwargs)`` to add the expectation
        3. Call ``validator.save_expectation_suite()`` to persist the change

        The validator is created once at the beginning of the method and reused for
        all expectations in the list. Each expectation triggers an individual save
        operation, which ensures that expectations are persisted even if a later
        expectation fails, but may impact performance when adding many expectations.

        The validator-based approach provides immediate validation feedback and can
        help catch configuration errors early, as the expectation methods perform
        parameter validation when called.

        Performance characteristics:

        - Time complexity: O(n) where n is the number of expectations
        - Each expectation triggers a suite save operation
        - Validator creation overhead is amortized across all expectations

        Examples
        --------
        Add basic column existence and uniqueness expectations:

        >>> adder = ValidatorBasedExpectationAddition()
        >>> adder.add_expectations(
        ...     batch_manager,
        ...     expectations=[
        ...         {"expect_column_to_exist": {"column": "user_id"}},
        ...         {"expect_column_values_to_be_unique": {"column": "user_id"}},
        ...     ],
        ... )

        Add expectations with value constraints:

        >>> adder.add_expectations(
        ...     batch_manager,
        ...     expectations=[
        ...         {
        ...             "expect_column_values_to_be_in_set": {
        ...                 "column": "status",
        ...                 "value_set": ["active", "inactive", "pending"],
        ...             }
        ...         },
        ...         {
        ...             "expect_column_values_to_be_between": {
        ...                 "column": "age",
        ...                 "min_value": 0,
        ...                 "max_value": 150,
        ...             }
        ...         },
        ...     ],
        ... )

        Add regex and pattern-based expectations:

        >>> adder.add_expectations(
        ...     batch_manager,
        ...     expectations=[
        ...         {
        ...             "expect_column_values_to_match_regex": {
        ...                 "column": "email",
        ...                 "regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        ...             }
        ...         },
        ...         {"expect_column_values_to_not_be_null": {"column": "email"}},
        ...     ],
        ... )

        Add expectations with metadata:

        >>> adder.add_expectations(
        ...     batch_manager,
        ...     expectations=[
        ...         {
        ...             "expect_column_mean_to_be_between": {
        ...                 "column": "revenue",
        ...                 "min_value": 1000,
        ...                 "max_value": 100000,
        ...                 "meta": {"notes": "Revenue should be within normal business range"},
        ...             }
        ...         },
        ...     ],
        ... )

        Add multi-column expectations:

        >>> adder.add_expectations(
        ...     batch_manager,
        ...     expectations=[
        ...         {
        ...             "expect_column_pair_values_A_to_be_greater_than_B": {
        ...                 "column_A": "end_date",
        ...                 "column_B": "start_date",
        ...                 "or_equal": True,
        ...             }
        ...         },
        ...     ],
        ... )
        """
        validator = create_batch_validator(batch_manager)
        for expectation in expectations:
            expectation_name, kwargs = parse_expectations_dict(expectation_dictionary=expectation)
            getattr(validator, expectation_name)(**kwargs)
            validator.save_expectation_suite()


def create_batch_validator(batch_manager: BatchManager) -> Validator:
    """
    Create a GX Validator object for programmatic expectation management.

    This function creates a Great Expectations Validator object that provides
    programmatic access to expectation management APIs. The Validator serves as
    the primary interface for adding, modifying, and validating expectations
    against batch data in an interactive manner.

    The Validator object returned by this function is distinct from the validator
    used in the ``validate`` method of the GX data validation workflow. This
    Validator is specifically designed for building and managing expectation suites
    programmatically, rather than executing validation runs against data.

    The Validator is initialized with a specific batch request and expectation
    suite, allowing expectations to be added and immediately tested against the
    batch data. This enables rapid iteration and development of validation rules.

    Parameters
    ----------
    batch_manager : BatchManager
        The batch manager containing the data context, batch request, and dataset
        name. The batch manager encapsulates all necessary information to create
        a properly configured Validator, including:

        - ``data_context``: The GX data context providing access to configuration
          and storage backends
        - ``batch_request``: The batch request specifying which data to validate
        - ``name``: The dataset name used to construct the expectation suite name

    Returns
    -------
    Validator
        A Great Expectations Validator object configured with the specified batch
        request and expectation suite. The Validator provides methods for adding
        expectations (e.g., ``expect_column_values_to_be_in_set``), saving the
        expectation suite, and optionally validating data as expectations are added.

        The Validator is bound to an expectation suite named ``{dataset_name}_suite``,
        where ``dataset_name`` comes from the batch manager's name attribute.

    Raises
    ------
    GreatExpectationsError
        If the data context cannot retrieve a validator, which may occur if:

        - The batch request is invalid or malformed
        - The expectation suite cannot be created or accessed
        - The data context is not properly configured
        - Required GX backend services are unavailable

    DataContextError
        If the data context encounters issues accessing storage backends or
        configuration files.

    See Also
    --------
    ValidatorBasedExpectationAddition : Uses this function to create validators for adding expectations
    BatchManager : Provides the data context and batch request needed to create validators
    great_expectations.validator.validator.Validator : GX Validator class documentation

    Notes
    -----
    The Validator object created by this function is part of Great Expectations'
    fluent API for working with validation rules. It differs from the validation
    execution flow in several important ways:

    1. **Purpose**: This Validator is for *building* expectation suites, not for
       *running* validation checks in production pipelines.

    2. **Expectation Suite Binding**: The Validator is bound to an expectation
       suite named ``{dataset_name}_suite``. All expectations added through this
       Validator are saved to this suite.

    3. **Data Access**: The Validator has access to the batch data specified in
       the batch request, allowing immediate feedback when adding expectations.

    4. **State Management**: The Validator maintains state about the current
       expectation suite and can save changes back to the data context's
       expectation store.

    The naming convention for expectation suites (``{dataset_name}_suite``) ensures
    that each dataset has a clearly identified validation suite. This convention
    is used consistently throughout the adc-toolkit's GX integration.

    Performance considerations:

    - Creating a Validator involves loading the expectation suite from storage
    - The batch data is loaded into memory for validation purposes
    - Each Validator instance maintains its own copy of the expectation suite state

    Examples
    --------
    Create a validator for interactive expectation development:

    >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
    >>> validator = create_batch_validator(batch_manager)
    >>> # Add expectations using the validator's API
    >>> validator.expect_column_to_exist(column="user_id")
    >>> validator.expect_column_values_to_be_unique(column="user_id")
    >>> # Save the expectations to the suite
    >>> validator.save_expectation_suite()

    Use the validator to test expectations against data:

    >>> validator = create_batch_validator(batch_manager)
    >>> # Add an expectation and immediately validate it
    >>> result = validator.expect_column_values_to_be_in_set(
    ...     column="status", value_set=["active", "inactive", "pending"]
    ... )
    >>> print(result.success)
    True

    Create multiple validators for different datasets:

    >>> validator1 = create_batch_validator(batch_manager1)
    >>> validator2 = create_batch_validator(batch_manager2)
    >>> # Each validator manages its own expectation suite
    >>> validator1.expect_column_to_exist(column="col1")
    >>> validator2.expect_column_to_exist(column="col2")

    Inspect the expectation suite associated with a validator:

    >>> validator = create_batch_validator(batch_manager)
    >>> suite = validator.expectation_suite
    >>> print(f"Suite name: {suite.expectation_suite_name}")
    Suite name: my_dataset_suite
    >>> print(f"Number of expectations: {len(suite.expectations)}")
    Number of expectations: 5
    """
    validator = batch_manager.data_context.get_validator(
        batch_request=batch_manager.batch_request,
        expectation_suite_name=f"{batch_manager.name}_suite",
    )
    return validator
