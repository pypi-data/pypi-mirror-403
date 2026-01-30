"""
Expectation dictionary parsing utilities for Great Expectations integration.

This module provides utility functions for parsing and validating expectation
configuration dictionaries used in the adc-toolkit's Great Expectations (GX)
validation framework. The parsed expectations are used to configure data
validation rules that are applied to datasets through the ValidatedDataCatalog.

The module handles the conversion of user-provided expectation configurations
(typically from YAML files) into the format required by Great Expectations'
API, ensuring type safety and structural correctness before expectations are
added to validation suites.

Functions
---------
parse_expectations_dict
    Parse and validate an expectation configuration dictionary.

See Also
--------
adc_toolkit.data.validators.gx.batch_managers.expectation_addition.configuration_based : Configuration-based expectation addition
adc_toolkit.data.validators.gx.batch_managers.expectation_addition.validator_based : Validator-based expectation addition

Notes
-----
Great Expectations uses a specific naming convention for expectations that
follows the pattern ``expect_<subject>_<predicate>``. Common expectations include:

- ``expect_column_values_to_be_in_set``
- ``expect_column_values_to_be_of_type``
- ``expect_column_values_to_not_be_null``
- ``expect_table_row_count_to_be_between``

For a complete list of available expectations, refer to the Great Expectations
documentation: https://docs.greatexpectations.io/
"""

from adc_toolkit.utils.exceptions import (
    InvalidExpectationDictionaryError,
    InvalidExpectationKwargsTypeError,
    InvalidExpectationNameTypeError,
)


def parse_expectations_dict(expectation_dictionary: dict) -> tuple[str, dict]:
    """
    Parse and validate an expectation configuration dictionary.

    Extract the expectation type and its associated keyword arguments from a
    configuration dictionary. This function validates the structure and types
    of the input dictionary to ensure it conforms to the expected format for
    Great Expectations integration.

    The expectation dictionary must contain exactly one key-value pair, where
    the key is the Great Expectations expectation type (e.g.,
    ``expect_column_values_to_be_in_set``) and the value is a dictionary
    containing the parameters required by that expectation.

    Parameters
    ----------
    expectation_dictionary : dict
        A dictionary containing a single expectation configuration. The
        dictionary must have exactly one key representing the expectation
        type (as a string), and the corresponding value must be a dictionary
        of keyword arguments that will be passed to the expectation.

        The structure must follow this format::

            {
                "expectation_type_name": {
                    "param1": value1,
                    "param2": value2,
                    ...
                }
            }

    Returns
    -------
    expectation_type : str
        The name of the Great Expectations expectation type. This string
        corresponds to a method name in Great Expectations' Validator or
        ExpectationConfiguration classes (e.g.,
        ``expect_column_values_to_be_in_set``).
    expectation_kwargs : dict
        A dictionary of keyword arguments to be passed to the expectation.
        The contents vary depending on the expectation type but typically
        include parameters like ``column``, ``value_set``, ``type``, etc.

    Raises
    ------
    InvalidExpectationDictionaryError
        If the expectation dictionary does not contain exactly one key.
        This ensures each dictionary represents a single, well-defined
        expectation configuration.
    InvalidExpectationNameTypeError
        If the expectation type (dictionary key) is not a string. The
        expectation type must be a string to be used as a method name or
        configuration identifier.
    InvalidExpectationKwargsTypeError
        If the expectation kwargs (dictionary value) is not a dictionary.
        The kwargs must be a dictionary to be unpacked as keyword arguments
        when creating or invoking expectations.

    See Also
    --------
    adc_toolkit.data.validators.gx.batch_managers.expectation_addition.configuration_based.ConfigurationBasedExpectationAddition : Uses this function to parse expectations from configuration files
    adc_toolkit.data.validators.gx.batch_managers.expectation_addition.validator_based.ValidatorBasedExpectationAddition : Uses this function to parse expectations before applying them via validator

    Notes
    -----
    This function is designed to work with Great Expectations' flexible
    expectation system. Each expectation type has its own set of required
    and optional parameters. The function validates the structure but does
    not validate that the kwargs are appropriate for the specific expectation
    type - that validation is deferred to Great Expectations itself.

    The single-key requirement ensures that each expectation configuration
    is atomic and unambiguous. When multiple expectations are needed, they
    should be provided as a list of dictionaries, with each dictionary
    containing one expectation.

    Examples
    --------
    Parse a simple column value expectation:

    >>> expectation_type, kwargs = parse_expectations_dict(
    ...     {
    ...         "expect_column_values_to_be_in_set": {
    ...             "column": "status",
    ...             "value_set": ["active", "inactive", "pending"],
    ...         }
    ...     }
    ... )
    >>> print(expectation_type)
    expect_column_values_to_be_in_set
    >>> print(kwargs)
    {'column': 'status', 'value_set': ['active', 'inactive', 'pending']}

    Parse a type expectation with additional parameters:

    >>> expectation_type, kwargs = parse_expectations_dict(
    ...     {
    ...         "expect_column_values_to_be_of_type": {
    ...             "column": "age",
    ...             "type_": "int",
    ...         }
    ...     }
    ... )
    >>> print(expectation_type)
    expect_column_values_to_be_of_type
    >>> print(kwargs)
    {'column': 'age', 'type_': 'int'}

    Parse a table-level expectation:

    >>> expectation_type, kwargs = parse_expectations_dict(
    ...     {
    ...         "expect_table_row_count_to_be_between": {
    ...             "min_value": 100,
    ...             "max_value": 10000,
    ...         }
    ...     }
    ... )
    >>> print(expectation_type)
    expect_table_row_count_to_be_between
    >>> print(kwargs)
    {'min_value': 100, 'max_value': 10000}

    Error handling - multiple keys in dictionary:

    >>> try:
    ...     parse_expectations_dict(
    ...         {
    ...             "expect_column_values_to_be_in_set": {"column": "col1"},
    ...             "expect_column_values_to_not_be_null": {"column": "col2"},
    ...         }
    ...     )
    ... except InvalidExpectationDictionaryError as e:
    ...     print(f"Error: {e}")
    Error: Expectation dictionary should have exactly one key, got 2 keys.

    Error handling - invalid expectation type:

    >>> try:
    ...     parse_expectations_dict({123: {"column": "col1", "value_set": [1, 2, 3]}})
    ... except InvalidExpectationNameTypeError as e:
    ...     print(f"Error: {e}")
    Error: Expectation type should be a string, got <class 'int'>.

    Error handling - invalid kwargs type:

    >>> try:
    ...     parse_expectations_dict({"expect_column_values_to_be_in_set": "invalid_kwargs"})
    ... except InvalidExpectationKwargsTypeError as e:
    ...     print(f"Error: {e}")
    Error: Expectation kwargs should be a dictionary, got <class 'str'>.

    Typical usage in a validation workflow:

    >>> expectations_config = [
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
    >>> for exp_dict in expectations_config:
    ...     exp_type, exp_kwargs = parse_expectations_dict(exp_dict)
    ...     print(f"Adding expectation: {exp_type} with {exp_kwargs}")
    Adding expectation: expect_column_values_to_be_in_set with {'column': 'status', 'value_set': ['active', 'inactive']}
    Adding expectation: expect_column_values_to_not_be_null with {'column': 'user_id'}
    """
    if len(expectation_dictionary) != 1:
        raise InvalidExpectationDictionaryError(
            f"Expectation dictionary should have exactly one key, got {len(expectation_dictionary)} keys."
        )
    expectation_type = next(iter(expectation_dictionary.keys()))
    expectation_kwargs = expectation_dictionary[expectation_type]
    if not isinstance(expectation_type, str):
        raise InvalidExpectationNameTypeError(f"Expectation type should be a string, got {type(expectation_type)}.")
    if not isinstance(expectation_kwargs, dict):
        raise InvalidExpectationKwargsTypeError(
            f"Expectation kwargs should be a dictionary, got {type(expectation_kwargs)}."
        )
    return expectation_type, expectation_kwargs
