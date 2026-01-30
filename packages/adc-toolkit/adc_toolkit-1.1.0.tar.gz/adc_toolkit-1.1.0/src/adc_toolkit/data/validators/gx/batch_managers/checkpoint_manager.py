"""
Great Expectations checkpoint management for data validation.

This module provides the `CheckpointManager` class, which orchestrates the
validation workflow in Great Expectations by managing checkpoint creation,
execution, and result evaluation. Checkpoints are configurable validation
configurations that bundle together batch requests and expectation suites
for streamlined data validation.
"""

from great_expectations.checkpoint import Checkpoint
from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult

from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
from adc_toolkit.utils.exceptions import ValidationError


class CheckpointManager:
    """
    Manage Great Expectations checkpoint lifecycle for data validation.

    The `CheckpointManager` class provides a high-level interface for working
    with Great Expectations checkpoints, which are validation configurations
    that combine batch requests and expectation suites. This manager handles
    checkpoint creation, execution, and result evaluation, providing a
    streamlined workflow for validating data against defined expectations.

    A checkpoint in Great Expectations is a validation configuration that:
    1. References a batch request (specifying what data to validate)
    2. References an expectation suite (specifying validation rules)
    3. Can be executed to validate data and produce structured results
    4. Can be versioned and reused across validation runs

    The manager automatically creates checkpoints with naming conventions
    derived from the associated batch manager, ensuring consistency across
    the validation infrastructure.

    Parameters
    ----------
    batch_manager : BatchManager
        The batch manager instance containing the data context, batch request,
        and data asset information. The checkpoint manager uses this to create
        and configure the checkpoint with the appropriate batch request and
        expectation suite references.

    Attributes
    ----------
    batch_manager : BatchManager
        The associated batch manager providing data context and batch request
        configuration.
    checkpoint : Checkpoint
        The Great Expectations checkpoint instance created during initialization.
        This checkpoint is configured to validate the batch specified in the
        batch manager against the expectation suite named
        "{batch_manager.name}_suite".

    See Also
    --------
    BatchManager : Manages batch request creation and data asset configuration.
    ConfigurationBasedExpectationAddition : Adds expectations to suites from configuration.
    ValidationError : Exception raised when checkpoint validation fails.

    Notes
    -----
    The `CheckpointManager` follows a specific naming convention:
    - Checkpoint name: "{batch_manager.name}_checkpoint"
    - Expectation suite name: "{batch_manager.name}_suite"

    This convention ensures that checkpoints, batch managers, and expectation
    suites are easily associated and identifiable in the Great Expectations
    data context.

    The checkpoint is created or updated during initialization, meaning that
    if a checkpoint with the same name already exists in the data context,
    it will be updated with the new configuration rather than causing an error.

    Examples
    --------
    Basic usage with a batch manager:

    >>> import pandas as pd
    >>> from great_expectations.data_context import EphemeralDataContext
    >>> from adc_toolkit.data.validators.gx import BatchManager
    >>> from adc_toolkit.data.validators.gx.batch_managers import CheckpointManager
    >>>
    >>> # Create a data context and batch manager
    >>> data_context = EphemeralDataContext()
    >>> df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4.0, 5.0, 6.0]})
    >>> batch_manager = BatchManager("my_data", df, data_context)
    >>>
    >>> # Create expectation suite (required before checkpoint execution)
    >>> data_context.add_or_update_expectation_suite("my_data_suite")
    >>>
    >>> # Create checkpoint manager
    >>> checkpoint_manager = CheckpointManager(batch_manager)
    >>> print(checkpoint_manager.checkpoint.name)
    my_data_checkpoint

    Running a checkpoint and handling validation results:

    >>> # Add some expectations to the suite
    >>> validator = data_context.get_validator(
    ...     batch_request=batch_manager.batch_request, expectation_suite_name="my_data_suite"
    ... )
    >>> validator.expect_column_values_to_be_between("col1", min_value=1, max_value=3)
    >>> validator.save_expectation_suite()
    >>>
    >>> # Run checkpoint and evaluate
    >>> try:
    ...     checkpoint_manager.run_checkpoint_and_evaluate()
    ...     print("Validation passed!")
    ... except ValidationError as e:
    ...     print(f"Validation failed: {e}")
    Validation passed!

    Inspecting validation results before evaluation:

    >>> # Run checkpoint without evaluation for detailed inspection
    >>> result = checkpoint_manager.run_checkpoint()
    >>> print(f"Success: {result.success}")
    >>> print(f"Run ID: {result.run_id}")
    >>>
    >>> # Manually evaluate if needed
    >>> CheckpointManager.evaluate_checkpoint_result(result)
    Success: True
    Run ID: ...
    """

    def __init__(self, batch_manager: BatchManager) -> None:
        """
        Initialize checkpoint manager and create associated checkpoint.

        Creates a new `CheckpointManager` instance and automatically creates
        (or updates) a checkpoint in the data context with the configuration
        derived from the provided batch manager.

        Parameters
        ----------
        batch_manager : BatchManager
            The batch manager instance containing the data context, batch request,
            and naming information. The checkpoint will be configured to validate
            this batch manager's data against an expectation suite named
            "{batch_manager.name}_suite".

        Notes
        -----
        The checkpoint is created immediately during initialization by calling
        `create_checkpoint()`. This means the data context must be properly
        initialized and accessible through the batch manager.

        The expectation suite referenced by the checkpoint ("{batch_manager.name}_suite")
        must exist in the data context before the checkpoint can be successfully
        executed. If the suite doesn't exist, checkpoint execution will fail.

        Examples
        --------
        Initialize with an existing batch manager:

        >>> checkpoint_manager = CheckpointManager(batch_manager)
        >>> print(checkpoint_manager.checkpoint.name)
        my_data_checkpoint
        >>> print(checkpoint_manager.batch_manager.name)
        my_data
        """
        self.batch_manager = batch_manager
        self.checkpoint = self.create_checkpoint()

    def create_checkpoint(self) -> Checkpoint:
        """
        Create or update a checkpoint in the data context.

        Creates a new checkpoint or updates an existing one with the same name
        in the Great Expectations data context. The checkpoint is configured
        with a validation that links the batch manager's batch request to the
        corresponding expectation suite.

        Returns
        -------
        Checkpoint
            The created or updated Great Expectations checkpoint instance,
            configured to validate the batch against the expectation suite.
            The checkpoint can be executed to perform validation.

        Notes
        -----
        The checkpoint configuration includes:
        - Name: "{batch_manager.name}_checkpoint"
        - Validation with batch_request from the batch manager
        - Validation with expectation_suite_name: "{batch_manager.name}_suite"

        This method uses the Great Expectations `add_or_update_checkpoint` method,
        which means:
        - If a checkpoint with this name exists, it will be updated
        - If no checkpoint with this name exists, a new one will be created
        - No error is raised for duplicate checkpoint names

        The expectation suite referenced in the checkpoint configuration must
        exist in the data context before the checkpoint can be successfully
        executed, though it does not need to exist at checkpoint creation time.

        Examples
        --------
        Create a checkpoint explicitly:

        >>> checkpoint = checkpoint_manager.create_checkpoint()
        >>> print(checkpoint.name)
        my_data_checkpoint
        >>> print(checkpoint.config.validations[0]["expectation_suite_name"])
        my_data_suite

        Update an existing checkpoint with new configuration:

        >>> # Checkpoint is automatically updated if it already exists
        >>> updated_checkpoint = checkpoint_manager.create_checkpoint()
        >>> assert updated_checkpoint.name == checkpoint.name
        """
        checkpoint = self.batch_manager.data_context.add_or_update_checkpoint(
            name=f"{self.batch_manager.name}_checkpoint",
            validations=[
                {
                    "batch_request": self.batch_manager.batch_request,
                    "expectation_suite_name": f"{self.batch_manager.name}_suite",
                },
            ],
        )
        return checkpoint

    def run_checkpoint(self) -> CheckpointResult:
        """
        Execute the checkpoint to validate data against expectations.

        Runs the configured checkpoint to validate the batch data against all
        expectations defined in the associated expectation suite. The method
        returns a comprehensive result object containing validation outcomes,
        statistics, and metadata.

        Returns
        -------
        CheckpointResult
            A Great Expectations checkpoint result object containing:
            - success : bool
                Whether all expectations passed validation.
            - run_id : str
                Unique identifier for this validation run.
            - run_results : dict
                Detailed results for each validation, including individual
                expectation outcomes, statistics, and metadata.
            - checkpoint_config : dict
                The configuration used for this checkpoint execution.
            - validation_result_identifier : object
                Identifier for accessing validation results in data docs.

        Raises
        ------
        GreatExpectationsError
            If the expectation suite referenced by the checkpoint does not exist
            in the data context, or if there are configuration issues with the
            checkpoint or batch request.

        Notes
        -----
        The checkpoint execution process:
        1. Retrieves the batch data using the configured batch request
        2. Loads the expectation suite from the data context
        3. Executes each expectation against the batch data
        4. Aggregates results into a structured checkpoint result
        5. Optionally updates data docs (if configured in the data context)

        This method does not raise exceptions for validation failures. Instead,
        the failure is indicated by the `success` attribute in the returned
        result object. Use `evaluate_checkpoint_result` or
        `run_checkpoint_and_evaluate` to raise exceptions on validation failure.

        Examples
        --------
        Run a checkpoint and inspect results:

        >>> result = checkpoint_manager.run_checkpoint()
        >>> print(f"Validation passed: {result.success}")
        >>> print(f"Run ID: {result.run_id}")
        >>>
        >>> # Access detailed validation results
        >>> for validation_result in result.run_results.values():
        ...     print(f"Suite: {validation_result['validation_result']['suite_name']}")
        ...     print(f"Statistics: {validation_result['validation_result']['statistics']}")
        Validation passed: True
        Run ID: ...

        Handle execution errors:

        >>> try:
        ...     result = checkpoint_manager.run_checkpoint()
        ... except Exception as e:
        ...     print(f"Checkpoint execution failed: {e}")
        """
        checkpoint_result = self.checkpoint.run()
        return checkpoint_result

    @staticmethod
    def evaluate_checkpoint_result(checkpoint_result: CheckpointResult) -> None:
        """
        Evaluate checkpoint result and raise exception on validation failure.

        Examines the checkpoint result to determine if validation was successful
        and raises a `ValidationError` if any expectations failed. This method
        provides a convenient way to convert validation failures into exceptions
        for error handling and control flow.

        Parameters
        ----------
        checkpoint_result : CheckpointResult
            The checkpoint result object returned by `run_checkpoint()`. This
            object contains the success status, validation details, and metadata
            from the checkpoint execution.

        Raises
        ------
        ValidationError
            Raised when the checkpoint result indicates validation failure
            (i.e., when `checkpoint_result["success"]` is False). The exception
            is constructed with the full checkpoint result object, allowing
            access to detailed failure information including which expectations
            failed and why.

        Notes
        -----
        This is a static method because it performs a generic evaluation that
        doesn't require access to instance state. It can be used independently
        to evaluate any checkpoint result, not just those from this manager's
        checkpoint.

        The method checks the "success" key in the checkpoint result dictionary.
        This key is False if any expectation in any validation failed during
        checkpoint execution.

        The `ValidationError` exception includes the full checkpoint result,
        providing access to:
        - Specific expectations that failed
        - Expected vs. actual values for failed expectations
        - Statistics on success/failure rates
        - Metadata about the validation run

        Examples
        --------
        Evaluate a successful checkpoint result:

        >>> result = checkpoint_manager.run_checkpoint()
        >>> CheckpointManager.evaluate_checkpoint_result(result)
        >>> print("Validation passed!")
        Validation passed!

        Handle validation failure:

        >>> result = checkpoint_manager.run_checkpoint()
        >>> try:
        ...     CheckpointManager.evaluate_checkpoint_result(result)
        ... except ValidationError as e:
        ...     print(f"Validation failed!")
        ...     print(f"Details: {e}")
        ...     # Access checkpoint result from exception
        ...     checkpoint_result = e.args[0]
        ...     print(f"Run ID: {checkpoint_result.run_id}")
        Validation failed!

        Use as a standalone validator:

        >>> from adc_toolkit.data.validators.gx.batch_managers import CheckpointManager
        >>> # Evaluate any checkpoint result, not just from this manager
        >>> CheckpointManager.evaluate_checkpoint_result(any_checkpoint_result)
        """
        if not checkpoint_result["success"]:
            raise ValidationError(checkpoint_result)

    def run_checkpoint_and_evaluate(self) -> None:
        """
        Execute checkpoint and raise exception if validation fails.

        Convenience method that combines checkpoint execution and result
        evaluation in a single call. This is the recommended way to perform
        validation when you want exceptions to be raised for validation
        failures, enabling straightforward error handling and control flow.

        Raises
        ------
        ValidationError
            Raised when checkpoint validation fails (i.e., when one or more
            expectations in the expectation suite are not met by the data).
            The exception contains the full checkpoint result with detailed
            information about which expectations failed and why.
        GreatExpectationsError
            Raised if there are configuration or execution issues with the
            checkpoint, such as a missing expectation suite or invalid batch
            request configuration.

        Notes
        -----
        This method is equivalent to:

        >>> result = checkpoint_manager.run_checkpoint()
        >>> CheckpointManager.evaluate_checkpoint_result(result)

        The method provides a clean interface for validation where failures
        should be treated as exceptions rather than return values. This is
        particularly useful in data pipelines where validation failures should
        halt processing.

        If you need access to the checkpoint result object (e.g., for logging
        or detailed inspection), use `run_checkpoint()` directly followed by
        `evaluate_checkpoint_result()` when appropriate.

        Examples
        --------
        Use in a data validation pipeline:

        >>> try:
        ...     checkpoint_manager.run_checkpoint_and_evaluate()
        ...     print("Data validation passed, continuing pipeline...")
        ... except ValidationError as e:
        ...     print(f"Data validation failed: {e}")
        ...     # Handle validation failure (log, alert, halt, etc.)
        ...     raise
        Data validation passed, continuing pipeline...

        Validate data before saving:

        >>> def save_validated_data(df, batch_manager):
        ...     checkpoint_manager = CheckpointManager(batch_manager)
        ...     # This will raise ValidationError if data is invalid
        ...     checkpoint_manager.run_checkpoint_and_evaluate()
        ...     # Only reached if validation passes
        ...     df.to_parquet("validated_data.parquet")

        Combine with logging:

        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>>
        >>> try:
        ...     checkpoint_manager.run_checkpoint_and_evaluate()
        ...     logger.info("Validation succeeded")
        ... except ValidationError as e:
        ...     logger.error(f"Validation failed: {e}")
        ...     raise
        """
        checkpoint_result = self.run_checkpoint()
        self.evaluate_checkpoint_result(checkpoint_result)
