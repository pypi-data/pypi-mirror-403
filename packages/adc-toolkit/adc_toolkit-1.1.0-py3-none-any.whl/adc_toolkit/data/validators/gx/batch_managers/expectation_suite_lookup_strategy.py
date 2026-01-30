"""
Expectation suite lookup strategies for Great Expectations validation.

This module provides a strategy pattern implementation for handling expectation
suite lookup operations in Great Expectations data contexts. Different strategies
determine how the system behaves when an expectation suite is not found.

The module contains the following classes:

- `ExpectationSuiteLookupStrategy` : Abstract base class defining the strategy interface
- `CustomExpectationSuiteStrategy` : Raises an error if suite is missing (strict mode)
- `AutoExpectationSuiteCreation` : Automatically creates missing suites (lenient mode)

These strategies are used by batch managers during data validation workflows to
control the behavior when a required expectation suite does not exist in the
Great Expectations data context.

Examples
--------
Using the strict strategy (requires suite to exist):

>>> from great_expectations.data_context import EphemeralDataContext
>>> data_context = EphemeralDataContext()
>>> # This will raise ExpectationSuiteNotFoundError if suite doesn't exist
>>> CustomExpectationSuiteStrategy.lookup_expectation_suite("my_dataset", data_context)

Using the auto-creation strategy:

>>> # This will create the suite automatically if it doesn't exist
>>> AutoExpectationSuiteCreation.lookup_expectation_suite("my_dataset", data_context)

See Also
--------
adc_toolkit.data.validators.gx.batch_managers.batch_manager : BatchManager classes that use these strategies
adc_toolkit.data.validators.gx.validator : GXValidator that orchestrates validation

Notes
-----
Expectation suite names follow the convention: `{dataset_name}_suite`
where dataset_name is the name of the dataset being validated.
"""

from abc import ABC, abstractmethod

from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.exceptions import DataContextError

from adc_toolkit.utils.exceptions import ExpectationSuiteNotFoundError


class ExpectationSuiteLookupStrategy(ABC):
    """
    Abstract base class for expectation suite lookup strategies.

    This class defines the interface for strategies that handle expectation suite
    lookup operations in Great Expectations data contexts. Concrete implementations
    of this class determine what action to take when a requested expectation suite
    does not exist.

    The strategy pattern allows batch managers to delegate the responsibility of
    handling missing expectation suites to configurable strategy objects, enabling
    flexible validation workflows that can either fail fast or auto-create resources.

    Methods
    -------
    lookup_expectation_suite(name, data_context)
        Look up an expectation suite by name and handle missing suites according
        to the concrete strategy implementation.
    _treat_expectation_suite_not_found(name, data_context)
        Abstract method that must be implemented by subclasses to define the
        behavior when an expectation suite is not found.

    See Also
    --------
    CustomExpectationSuiteStrategy : Strategy that raises an error for missing suites
    AutoExpectationSuiteCreation : Strategy that auto-creates missing suites
    adc_toolkit.data.validators.gx.batch_managers.batch_manager : BatchManager implementations

    Notes
    -----
    This class follows the Strategy design pattern, allowing runtime selection
    of algorithms for handling missing expectation suites. Subclasses must
    implement the `_treat_expectation_suite_not_found` method to define
    concrete behavior.

    The lookup method follows the naming convention where an expectation suite
    for a dataset named "my_data" is expected to be named "my_data_suite".

    Examples
    --------
    Implementing a custom strategy:

    >>> class LogAndContinueStrategy(ExpectationSuiteLookupStrategy):
    ...     def _treat_expectation_suite_not_found(self, name, data_context):
    ...         print(f"Warning: Suite {name}_suite not found")
    ...         # Continue without raising an error

    Using a strategy with a data context:

    >>> from great_expectations.data_context import EphemeralDataContext
    >>> data_context = EphemeralDataContext()
    >>> strategy = CustomExpectationSuiteStrategy()
    >>> # Will raise error if suite doesn't exist
    >>> strategy.lookup_expectation_suite("my_dataset", data_context)
    """

    @abstractmethod
    def _treat_expectation_suite_not_found(self, name: str, data_context: AbstractDataContext) -> None:
        """
        Handle the case when an expectation suite is not found.

        This abstract method must be implemented by concrete strategy classes
        to define what action to take when the requested expectation suite
        does not exist in the data context. Implementations may raise exceptions,
        create new suites, log warnings, or take other appropriate actions.

        Parameters
        ----------
        name : str
            The name of the dataset whose expectation suite was not found.
            The actual suite name searched for is `{name}_suite`.
        data_context : AbstractDataContext
            The Great Expectations data context in which the suite was searched.
            This context can be used to create new suites, access configuration,
            or perform other operations.

        Returns
        -------
        None

        Raises
        ------
        NotImplementedError
            This method is abstract and must be implemented by subclasses.

        See Also
        --------
        lookup_expectation_suite : Public method that calls this handler

        Notes
        -----
        This method is called internally by `lookup_expectation_suite` when
        a `DataContextError` is caught, indicating that the expectation suite
        does not exist in the data context.

        Implementations should carefully consider error handling, logging,
        and side effects (such as creating new resources).

        Examples
        --------
        Strict implementation that raises an error:

        >>> def _treat_expectation_suite_not_found(self, name, data_context):
        ...     raise ValueError(f"Suite {name}_suite is required but not found")

        Lenient implementation that creates a new suite:

        >>> def _treat_expectation_suite_not_found(self, name, data_context):
        ...     data_context.add_or_update_expectation_suite(expectation_suite_name=f"{name}_suite")
        """

    @classmethod
    def lookup_expectation_suite(cls, name: str, data_context: AbstractDataContext) -> None:
        """
        Look up an expectation suite in the data context.

        This method attempts to retrieve an expectation suite from the Great
        Expectations data context. If the suite does not exist, the strategy's
        `_treat_expectation_suite_not_found` method is called to handle the
        missing suite according to the concrete strategy implementation.

        The expectation suite name is constructed by appending "_suite" to the
        provided dataset name. For example, if name="customer_data", the method
        will search for "customer_data_suite".

        Parameters
        ----------
        name : str
            The name of the dataset to be validated. The expectation suite name
            will be constructed as `{name}_suite`. This should match the dataset
            name used in the data catalog configuration.
        data_context : AbstractDataContext
            The Great Expectations data context containing expectation suites.
            This is typically an instance of FileDataContext, EphemeralDataContext,
            or CloudDataContext depending on the deployment configuration.

        Returns
        -------
        None
            This method does not return a value. It either succeeds silently
            (if the suite exists or is successfully created) or raises an
            exception (depending on the strategy implementation).

        Raises
        ------
        ExpectationSuiteNotFoundError
            If using `CustomExpectationSuiteStrategy` and the suite does not exist.
        DataContextError
            If there is an error accessing the data context that is not related
            to a missing expectation suite.

        See Also
        --------
        _treat_expectation_suite_not_found : Strategy-specific handler for missing suites
        great_expectations.data_context.AbstractDataContext.get_expectation_suite : GX method for retrieving suites

        Notes
        -----
        This is a class method that instantiates the strategy class internally
        when handling missing suites. This design allows the strategy to be
        specified as a class rather than requiring instantiation by the caller.

        The method catches `DataContextError` exceptions from Great Expectations,
        which are raised when a requested expectation suite does not exist in
        the data context.

        Examples
        --------
        Using with a strict strategy (will raise if suite is missing):

        >>> from great_expectations.data_context import EphemeralDataContext
        >>> data_context = EphemeralDataContext()
        >>> # First create a suite
        >>> data_context.add_or_update_expectation_suite(expectation_suite_name="sales_data_suite")
        >>> # Now lookup will succeed
        >>> CustomExpectationSuiteStrategy.lookup_expectation_suite("sales_data", data_context)

        Using with auto-creation strategy:

        >>> # This will create the suite if it doesn't exist
        >>> AutoExpectationSuiteCreation.lookup_expectation_suite("new_dataset", data_context)

        Handling missing suites in a validation workflow:

        >>> try:
        ...     CustomExpectationSuiteStrategy.lookup_expectation_suite("my_data", data_context)
        ... except ExpectationSuiteNotFoundError as e:
        ...     print(f"Suite not found: {e}")
        ...     # Handle the error or create the suite manually
        """
        try:
            data_context.get_expectation_suite(expectation_suite_name=f"{name}_suite")
        except DataContextError:
            cls()._treat_expectation_suite_not_found(name, data_context)


class CustomExpectationSuiteStrategy(ExpectationSuiteLookupStrategy):
    """
    Strict expectation suite lookup strategy that fails fast on missing suites.

    This strategy implements a strict validation workflow where missing expectation
    suites cause an immediate failure with a detailed error message. This is the
    recommended approach for production environments where all expectation suites
    should be explicitly defined and version-controlled before data validation.

    When an expectation suite is not found, this strategy raises an
    `ExpectationSuiteNotFoundError` with guidance on how to create the missing
    suite, including links to Great Expectations documentation and suggestions
    for alternative validators.

    This strategy is ideal for:

    - Production validation pipelines where suites must be pre-defined
    - Environments where data quality rules are managed through code review
    - Teams that want explicit control over expectation suite creation
    - Preventing accidental validation with empty or default expectation suites

    Attributes
    ----------
    None

    Methods
    -------
    _treat_expectation_suite_not_found(name, data_context)
        Raises ExpectationSuiteNotFoundError with detailed guidance.

    See Also
    --------
    AutoExpectationSuiteCreation : Alternative strategy that auto-creates missing suites
    ExpectationSuiteLookupStrategy : Base class for all lookup strategies
    adc_toolkit.utils.exceptions.ExpectationSuiteNotFoundError : Exception raised by this strategy

    Notes
    -----
    This is the default and recommended strategy for `GXValidator` in production
    environments. It enforces that expectation suites are created deliberately
    and tested before being used in validation workflows.

    The error message provides actionable guidance including:

    - The specific expectation suite name that was not found
    - Link to Great Expectations documentation on creating suites
    - Suggestion to use InstantGXValidator for rapid prototyping

    Examples
    --------
    Using this strategy in a validation workflow:

    >>> from great_expectations.data_context import EphemeralDataContext
    >>> from adc_toolkit.utils.exceptions import ExpectationSuiteNotFoundError
    >>> data_context = EphemeralDataContext()
    >>> try:
    ...     CustomExpectationSuiteStrategy.lookup_expectation_suite("customer_data", data_context)
    ... except ExpectationSuiteNotFoundError as e:
    ...     print("Suite must be created before validation")
    ...     # Create suite manually or fail the pipeline

    Creating the required suite before validation:

    >>> # First create the expectation suite
    >>> suite = data_context.add_or_update_expectation_suite(expectation_suite_name="customer_data_suite")
    >>> # Add expectations to the suite
    >>> # ... (add your expectations here)
    >>> # Now validation will succeed
    >>> CustomExpectationSuiteStrategy.lookup_expectation_suite("customer_data", data_context)

    Recommended workflow for production:

    >>> # 1. Create suite in development
    >>> suite = data_context.add_or_update_expectation_suite(expectation_suite_name="sales_data_suite")
    >>> # 2. Add expectations using interactive tools or code
    >>> # 3. Commit suite to version control
    >>> # 4. In production, use CustomExpectationSuiteStrategy
    >>> #    to ensure suite exists before validation
    """

    def _treat_expectation_suite_not_found(self, name: str, data_context: AbstractDataContext) -> None:  # noqa: ARG002
        """
        Raise an error with detailed guidance when expectation suite is not found.

        This method is called when an expectation suite does not exist in the
        data context. It raises an `ExpectationSuiteNotFoundError` with a
        comprehensive error message that includes:

        - The specific expectation suite name that was not found
        - Instructions to create the suite before validation
        - Link to Great Expectations documentation
        - Suggestion to use InstantGXValidator for easier suite creation

        Parameters
        ----------
        name : str
            The name of the dataset whose expectation suite was not found.
            The suite name is `{name}_suite`.
        data_context : AbstractDataContext
            The Great Expectations data context (not used in this implementation,
            but required by the abstract base class interface).

        Returns
        -------
        None
            This method never returns normally; it always raises an exception.

        Raises
        ------
        ExpectationSuiteNotFoundError
            Always raised with a detailed error message providing guidance on
            how to create the missing expectation suite.

        See Also
        --------
        ExpectationSuiteLookupStrategy.lookup_expectation_suite : Method that calls this handler
        adc_toolkit.utils.exceptions.ExpectationSuiteNotFoundError : Exception type raised

        Notes
        -----
        The `data_context` parameter is not used in this implementation because
        the strategy's purpose is to fail fast rather than modify the context.
        The parameter is kept for interface compatibility with the abstract
        base class.

        The error message intentionally provides extensive guidance to help
        users understand their options:

        1. Create the suite manually using Great Expectations tools
        2. Follow GX documentation for expectation suite creation
        3. Consider using InstantGXValidator for automatic suite generation

        Examples
        --------
        This method is called internally by lookup_expectation_suite:

        >>> from great_expectations.data_context import EphemeralDataContext
        >>> data_context = EphemeralDataContext()
        >>> strategy = CustomExpectationSuiteStrategy()
        >>> try:
        ...     strategy._treat_expectation_suite_not_found("missing_data", data_context)
        ... except ExpectationSuiteNotFoundError as e:
        ...     assert "missing_data_suite does not exist" in str(e)
        ...     assert "InstantGXValidator" in str(e)

        Typical error message format:

        >>> # When "my_dataset_suite" is not found, the error message includes:
        >>> # - "Expectation suite my_dataset_suite does not exist"
        >>> # - Link to GX documentation
        >>> # - Suggestion to use InstantGXValidator
        """
        error_message = f"""
        Expectation suite {name}_suite does not exist. Create it before validating data.
        Please refer to the documentation for more information:
        https://docs.greatexpectations.io/docs/guides/expectations/create_manage_expectations_lp/.
        If you are unfamiliar with Great Expectations and would like
        to easily create an expectation suite,
        consider using `InstantGXValidator` instead of `GXValidator`.
        """
        raise ExpectationSuiteNotFoundError(error_message)


class AutoExpectationSuiteCreation(ExpectationSuiteLookupStrategy):
    """
    Lenient expectation suite lookup strategy that auto-creates missing suites.

    This strategy implements a permissive validation workflow where missing expectation
    suites are automatically created on-demand with no expectations defined. This approach
    is useful for rapid prototyping, development environments, and exploratory data
    analysis where you want to establish a validation framework before defining specific
    expectations.

    When an expectation suite is not found, this strategy automatically creates an empty
    suite with the appropriate name. The suite will have no expectations initially, which
    means validation will pass by default until expectations are added to the suite.

    This strategy is ideal for:

    - Development and prototyping environments where suites are built iteratively
    - Exploratory data analysis workflows where expectations are discovered gradually
    - Automated data pipeline scaffolding that creates validation infrastructure
    - Situations where you want to enable validation without blocking on missing suites
    - Testing scenarios where you need temporary expectation suites

    Attributes
    ----------
    None

    Methods
    -------
    _treat_expectation_suite_not_found(name, data_context)
        Automatically creates an empty expectation suite in the data context.

    See Also
    --------
    CustomExpectationSuiteStrategy : Alternative strategy that raises errors for missing suites
    ExpectationSuiteLookupStrategy : Base class for all lookup strategies
    adc_toolkit.data.validators.gx.instant_gx_validator : Validator designed for auto-creation workflows
    great_expectations.data_context.AbstractDataContext.add_or_update_expectation_suite : GX method for creating suites

    Notes
    -----
    **Important Caveats:**

    - Auto-created suites are initially empty (no expectations)
    - Empty suites will pass validation for any data (no constraints enforced)
    - This can create a false sense of security if expectations are not added later
    - Not recommended for production environments without explicit expectation management

    **Best Practices:**

    1. Use this strategy in development to bootstrap your validation infrastructure
    2. Add expectations to auto-created suites before deploying to production
    3. Consider switching to `CustomExpectationSuiteStrategy` in production
    4. Version control your expectation suites after creation
    5. Document which suites are intentionally empty vs. awaiting expectations

    The auto-created suites follow the naming convention `{dataset_name}_suite` and
    are immediately persisted to the data context's suite store.

    Warnings
    --------
    Using this strategy in production without adding expectations to the created
    suites effectively disables validation for those datasets. Always verify that
    auto-created suites have expectations added before relying on them for data
    quality assurance.

    Examples
    --------
    Using this strategy for development workflows:

    >>> from great_expectations.data_context import EphemeralDataContext
    >>> data_context = EphemeralDataContext()
    >>> # Suite doesn't exist yet
    >>> AutoExpectationSuiteCreation.lookup_expectation_suite("customer_data", data_context)
    >>> # Suite is now created and can be used
    >>> suite = data_context.get_expectation_suite("customer_data_suite")
    >>> print(len(suite.expectations))  # Will be 0
    0

    Building expectations iteratively after auto-creation:

    >>> # Auto-create the suite
    >>> AutoExpectationSuiteCreation.lookup_expectation_suite("sales_data", data_context)
    >>> # Now add expectations to the suite
    >>> suite = data_context.get_expectation_suite("sales_data_suite")
    >>> # Add expectations using GX APIs
    >>> # ... (add your expectations here)

    Comparing with strict strategy:

    >>> # This would raise ExpectationSuiteNotFoundError
    >>> # CustomExpectationSuiteStrategy.lookup_expectation_suite(
    >>> #     "new_dataset", data_context
    >>> # )
    >>> # This creates the suite automatically
    >>> AutoExpectationSuiteCreation.lookup_expectation_suite("new_dataset", data_context)

    Using in a batch manager configuration:

    >>> from adc_toolkit.data.validators.gx.batch_managers.batch_manager import PandasBatchManager
    >>> # Configure batch manager to use auto-creation strategy
    >>> batch_manager = PandasBatchManager(
    ...     data_context=data_context, expectation_suite_lookup_strategy=AutoExpectationSuiteCreation
    ... )
    >>> # Batch manager will auto-create suites as needed
    """

    def _treat_expectation_suite_not_found(self, name: str, data_context: AbstractDataContext) -> None:
        """
        Automatically create an empty expectation suite in the data context.

        This method is called when an expectation suite does not exist in the
        data context. It creates a new, empty expectation suite with the name
        `{name}_suite` and persists it to the data context's expectation suite
        store.

        The created suite will have no expectations defined, which means any
        data validation against this suite will pass by default. Expectations
        should be added to the suite after creation to enforce data quality
        constraints.

        Parameters
        ----------
        name : str
            The name of the dataset whose expectation suite should be created.
            The created suite will be named `{name}_suite`.
        data_context : AbstractDataContext
            The Great Expectations data context where the suite will be created.
            This context must have a configured expectation suite store where
            the new suite can be persisted.

        Returns
        -------
        None
            The method creates the suite as a side effect and returns nothing.

        Raises
        ------
        DataContextError
            If there is an error creating or persisting the expectation suite
            in the data context. This can occur if the suite store is not
            properly configured or if there are permissions issues.
        ValueError
            If the suite name is invalid according to Great Expectations naming
            conventions.

        See Also
        --------
        ExpectationSuiteLookupStrategy.lookup_expectation_suite : Method that calls this handler
        great_expectations.data_context.AbstractDataContext.add_or_update_expectation_suite : GX method used internally
        CustomExpectationSuiteStrategy._treat_expectation_suite_not_found : Alternative implementation that raises errors

        Notes
        -----
        The `add_or_update_expectation_suite` method is idempotent - if called
        multiple times with the same suite name, it will update the existing
        suite rather than failing. However, this implementation is only called
        when the suite does not exist, so it effectively always creates a new
        suite.

        **Suite Creation Details:**

        - Suite is created with no expectations (empty suite)
        - Suite is immediately persisted to the configured expectation suite store
        - Suite metadata includes creation timestamp and GX version information
        - Suite follows GX naming conventions and can be managed with standard GX tools

        **Post-Creation Workflow:**

        After the suite is created, you should:

        1. Retrieve the suite using `data_context.get_expectation_suite()`
        2. Add expectations using GX expectation methods
        3. Validate the suite against sample data
        4. Commit the suite to version control

        Examples
        --------
        This method is called internally by lookup_expectation_suite:

        >>> from great_expectations.data_context import EphemeralDataContext
        >>> data_context = EphemeralDataContext()
        >>> strategy = AutoExpectationSuiteCreation()
        >>> # Create suite for a dataset
        >>> strategy._treat_expectation_suite_not_found("my_dataset", data_context)
        >>> # Verify suite was created
        >>> suite = data_context.get_expectation_suite("my_dataset_suite")
        >>> print(suite.expectation_suite_name)
        my_dataset_suite

        Verifying the created suite is empty:

        >>> # After auto-creation
        >>> suite = data_context.get_expectation_suite("customer_data_suite")
        >>> assert len(suite.expectations) == 0
        >>> # Now add expectations
        >>> # ... (add your expectations)

        Handling multiple datasets:

        >>> datasets = ["sales", "inventory", "customers"]
        >>> for dataset_name in datasets:
        ...     AutoExpectationSuiteCreation.lookup_expectation_suite(dataset_name, data_context)
        >>> # All three suites now exist and can be configured
        """
        data_context.add_or_update_expectation_suite(expectation_suite_name=f"{name}_suite")
