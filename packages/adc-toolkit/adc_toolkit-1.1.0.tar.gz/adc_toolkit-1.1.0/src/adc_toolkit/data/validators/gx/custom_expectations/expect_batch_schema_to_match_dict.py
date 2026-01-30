"""
Custom Great Expectations expectation for schema validation.

This module provides a custom Great Expectations (GX) expectation that validates
whether a DataFrame's schema (column names and data types) matches a provided
dictionary specification. It supports both Pandas and Spark execution engines.

The module contains two main classes:

- `BatchSchemaMatchesDict` : MetricProvider that extracts schema information
- `ExpectBatchSchemaToMatchDict` : BatchExpectation that validates schema compliance

This expectation is useful for ensuring data type consistency across pipeline
stages, validating data contracts, and catching schema drift in production
data workflows.

Examples
--------
Basic usage with Great Expectations:

>>> import pandas as pd
>>> import great_expectations as gx
>>> from adc_toolkit.data.validators.gx.custom_expectations import ExpectBatchSchemaToMatchDict
>>>
>>> # Create a sample DataFrame
>>> df = pd.DataFrame({"id": [1, 2, 3], "value": [1.5, 2.5, 3.5], "name": ["a", "b", "c"]})
>>>
>>> # Define expected schema
>>> expected_schema = {"id": "int64", "value": "float64", "name": "object"}
>>>
>>> # Create a GX context and batch
>>> context = gx.get_context()
>>> batch = (
...     context.sources.add_pandas("my_source")
...     .add_dataframe_asset("my_asset")
...     .add_batch_definition("my_batch")
...     .build_batch_request(dataframe=df)
...     .get_batch_list()[0]
... )
>>>
>>> # Apply the expectation
>>> result = batch.expect_batch_schema_to_match_dict(schema=expected_schema)
>>> print(result.success)
True

Notes
-----
This custom expectation extends Great Expectations' BatchExpectation framework.
It requires GX version 0.15.0 or later.

For Spark DataFrames, the data type strings should match Spark SQL types
(e.g., "bigint", "double", "string") rather than Pandas types.

See Also
--------
great_expectations.expectations.expectation.BatchExpectation : Base class
great_expectations.expectations.metrics.table_metric_provider.TableMetricProvider : Metric base
"""

from typing import Any, ClassVar

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.execution_engine.execution_engine import ExecutionEngine
from great_expectations.execution_engine.pandas_execution_engine import PandasExecutionEngine
from great_expectations.execution_engine.sparkdf_execution_engine import SparkDFExecutionEngine
from great_expectations.expectations.expectation import BatchExpectation
from great_expectations.expectations.metrics.metric_provider import MetricConfiguration, MetricDomainTypes, metric_value
from great_expectations.expectations.metrics.table_metric_provider import TableMetricProvider


# This class defines a Metric to support your Expectation.
# For most BatchExpectations, the main business logic for calculation will live in this class.
class BatchSchemaMatchesDict(TableMetricProvider):
    """
    Extract schema information from a DataFrame batch.

    This MetricProvider extracts column names and their corresponding data types
    from a DataFrame, returning them as a dictionary. It supports both Pandas
    and Spark DataFrames through their respective execution engines.

    The metric is registered under the name "table.columns.schema" and is used
    by the ExpectBatchSchemaToMatchDict expectation to obtain the actual schema
    for comparison against the expected schema.

    Attributes
    ----------
    metric_name : str
        The unique identifier for this metric: "table.columns.schema".

    Methods
    -------
    _pandas(cls, execution_engine, metric_domain_kwargs, metric_value_kwargs, metrics, runtime_configuration)
        Extract schema from Pandas DataFrame.
    _spark(cls, execution_engine, metric_domain_kwargs, metric_value_kwargs, metrics, runtime_configuration)
        Extract schema from Spark DataFrame.
    _get_evaluation_dependencies(cls, metric, configuration, execution_engine, runtime_configuration)
        Define metric dependencies for evaluation.

    Notes
    -----
    This class follows the Great Expectations MetricProvider pattern, where
    different execution engine implementations are decorated with @metric_value.

    The schema extraction converts native data types to string representations:
    - Pandas: "int64", "float64", "object", "datetime64[ns]", etc.
    - Spark: "bigint", "double", "string", "timestamp", etc.

    See Also
    --------
    ExpectBatchSchemaToMatchDict : The expectation that uses this metric
    great_expectations.expectations.metrics.table_metric_provider.TableMetricProvider : Base class

    Examples
    --------
    This metric is typically not called directly but is used internally by
    the ExpectBatchSchemaToMatchDict expectation. However, it can be accessed
    through the metrics dictionary:

    >>> # In a custom expectation or metric
    >>> schema = metrics["table.columns.schema"]
    >>> print(schema)
    {'id': 'int64', 'value': 'float64', 'name': 'object'}
    """

    # This is the id string that will be used to reference your Metric.
    metric_name = "table.columns.schema"

    # This method implements the core logic for the PandasExecutionEngine
    @metric_value(engine=PandasExecutionEngine)
    def _pandas(
        cls,
        execution_engine: PandasExecutionEngine,
        metric_domain_kwargs: dict[str, Any],
        metric_value_kwargs: dict[str, Any],  # noqa: ARG002
        metrics: dict[str, Any],  # noqa: ARG002
        runtime_configuration: dict,  # noqa: ARG002
    ) -> dict[str, str]:
        """
        Extract schema from a Pandas DataFrame.

        This method retrieves the compute domain (DataFrame) from the Pandas
        execution engine and extracts column names and their data types,
        returning them as a dictionary with string representations.

        Parameters
        ----------
        execution_engine : PandasExecutionEngine
            The Pandas execution engine containing the DataFrame to analyze.
        metric_domain_kwargs : dict of str to any
            Domain-level configuration for the metric, such as row conditions
            or column filters. Used to obtain the compute domain.
        metric_value_kwargs : dict of str to any
            Value-level configuration for the metric. Not used in this implementation.
        metrics : dict of str to any
            Dictionary of previously computed metrics. Not used in this implementation.
        runtime_configuration : dict
            Runtime configuration options. Not used in this implementation.

        Returns
        -------
        dict of str to str
            Dictionary mapping column names to their Pandas data type strings.
            Examples: {"id": "int64", "value": "float64", "name": "object"}

        Notes
        -----
        The data type strings returned are standard Pandas dtype string representations:
        - Integer types: "int8", "int16", "int32", "int64", "uint8", etc.
        - Float types: "float16", "float32", "float64"
        - String/object types: "object"
        - DateTime types: "datetime64[ns]", "timedelta64[ns]"
        - Categorical: "category"
        - Boolean: "bool"

        Examples
        --------
        >>> import pandas as pd
        >>> df = pd.DataFrame({"a": [1, 2], "b": [1.5, 2.5], "c": ["x", "y"]})
        >>> # When called by GX internally:
        >>> # result = {"a": "int64", "b": "float64", "c": "object"}
        """
        df, _, _ = execution_engine.get_compute_domain(metric_domain_kwargs, domain_type=MetricDomainTypes.TABLE)
        types_dict = {col_name: str(col_type) for col_name, col_type in dict(df.dtypes).items()}
        return types_dict

    # @metric_value(engine=SqlAlchemyExecutionEngine)
    # def _sqlalchemy(
    #         cls,
    #         execution_engine,
    #         metric_domain_kwargs,
    #         metric_value_kwargs,
    #         metrics,
    #         runtime_configuration,
    # ):
    #    raise NotImplementedError

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: dict[str, Any],
        metric_value_kwargs: dict[str, Any],  # noqa: ARG002
        metrics: dict[str, Any],  # noqa: ARG002
        runtime_configuration: dict,  # noqa: ARG002
    ) -> dict[str, str]:
        """
        Extract schema from a Spark DataFrame.

        This method retrieves the compute domain (Spark DataFrame) from the
        Spark execution engine and extracts column names and their data types,
        returning them as a dictionary with string representations of Spark SQL types.

        Parameters
        ----------
        execution_engine : SparkDFExecutionEngine
            The Spark execution engine containing the DataFrame to analyze.
        metric_domain_kwargs : dict of str to any
            Domain-level configuration for the metric, such as row conditions
            or column filters. Used to obtain the compute domain.
        metric_value_kwargs : dict of str to any
            Value-level configuration for the metric. Not used in this implementation.
        metrics : dict of str to any
            Dictionary of previously computed metrics. Not used in this implementation.
        runtime_configuration : dict
            Runtime configuration options. Not used in this implementation.

        Returns
        -------
        dict of str to str
            Dictionary mapping column names to their Spark SQL data type strings.
            Examples: {"id": "bigint", "value": "double", "name": "string"}

        Notes
        -----
        The data type strings returned are Spark SQL type representations:
        - Integer types: "tinyint", "smallint", "int", "bigint"
        - Float types: "float", "double", "decimal"
        - String types: "string"
        - DateTime types: "timestamp", "date"
        - Boolean: "boolean"
        - Complex types: "array<type>", "map<type,type>", "struct<...>"

        When comparing schemas between Pandas and Spark, be aware that equivalent
        types have different string representations (e.g., "int64" vs "bigint").

        Examples
        --------
        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.getOrCreate()
        >>> df = spark.createDataFrame([(1, 1.5, "x"), (2, 2.5, "y")], ["a", "b", "c"])
        >>> # When called by GX internally:
        >>> # result = {"a": "bigint", "b": "double", "c": "string"}
        """
        df, _, _ = execution_engine.get_compute_domain(metric_domain_kwargs, domain_type=MetricDomainTypes.TABLE)
        types_dict = {col_name: str(col_type) for col_name, col_type in dict(df.dtypes).items()}
        return types_dict

    @classmethod
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: ExpectationConfiguration | None = None,  # noqa: ARG003
        execution_engine: ExecutionEngine | None = None,  # noqa: ARG003
        runtime_configuration: dict | None = None,  # noqa: ARG003
    ) -> dict[str, MetricConfiguration]:
        """
        Define metric dependencies required for evaluation.

        This method specifies which other metrics must be computed before this
        metric can be evaluated. For schema extraction, we depend on the
        "table.columns" metric to ensure column information is available.

        Parameters
        ----------
        metric : MetricConfiguration
            The metric configuration for which dependencies are being determined.
        configuration : ExpectationConfiguration or None, default=None
            The expectation configuration. Not used in this implementation.
        execution_engine : ExecutionEngine or None, default=None
            The execution engine that will run the metric. Not used in this implementation.
        runtime_configuration : dict or None, default=None
            Runtime configuration options. Not used in this implementation.

        Returns
        -------
        dict of str to MetricConfiguration
            Dictionary mapping dependency names to their MetricConfiguration objects.
            Contains a single dependency: "table.columns".

        Notes
        -----
        The "table.columns" metric provides the list of column names in the table,
        which serves as a foundation for schema extraction. This dependency ensures
        that column information is computed before attempting to extract type information.

        Great Expectations uses this method to build a dependency graph and compute
        metrics in the correct order.

        Examples
        --------
        >>> metric_config = MetricConfiguration(metric_name="table.columns.schema", metric_domain_kwargs={})
        >>> deps = BatchSchemaMatchesDict._get_evaluation_dependencies(metric_config)
        >>> print(deps)
        {'table.columns': MetricConfiguration(metric_name='table.columns', ...)}
        """
        return {
            "table.columns": MetricConfiguration("table.columns", metric.metric_domain_kwargs),
        }


# This class defines the Expectation itself
# The main business logic for calculation lives here.
class ExpectBatchSchemaToMatchDict(BatchExpectation):
    """
    Validate that a DataFrame's schema matches a specified dictionary.

    This custom Great Expectations expectation verifies that a batch (DataFrame)
    has a schema that exactly matches a provided dictionary specification, where
    keys are column names and values are data type strings. The expectation
    succeeds only when both column names and their types match exactly.

    This expectation is particularly useful for:
    - Enforcing data contracts between pipeline stages
    - Validating schema consistency after transformations
    - Detecting schema drift in production data
    - Ensuring type safety before loading data into databases
    - Validating external data sources against internal standards

    Parameters
    ----------
    schema : dict of str to str
        Expected schema specification where keys are column names and values
        are data type strings. Type strings must match the execution engine:
        - Pandas: "int64", "float64", "object", "datetime64[ns]", etc.
        - Spark: "bigint", "double", "string", "timestamp", etc.

    Attributes
    ----------
    examples : list of dict
        Example test cases demonstrating usage for both Pandas and Spark.
    metric_dependencies : tuple of str
        Metrics required for validation: ("table.columns.schema", "table.columns").
    success_keys : tuple
        Keys required for success (empty for this expectation).
    default_kwarg_values : dict
        Default values for keyword arguments (empty for this expectation).
    library_metadata : dict
        Metadata for display in the Great Expectations public gallery.

    Methods
    -------
    validate_configuration(configuration)
        Validate the expectation configuration.
    _validate(configuration, metrics, runtime_configuration, execution_engine)
        Execute the validation logic.

    Returns
    -------
    ExpectationValidationResult
        Validation result containing:
        - success : bool - Whether the schema matches
        - result : dict - Observed schema and expected schema details

    Raises
    ------
    InvalidExpectationConfigurationError
        If the expectation configuration is invalid.

    Notes
    -----
    Schema matching is exact and order-sensitive. All columns must be present
    with exactly matching types. Extra columns or missing columns will cause
    validation failure.

    When working with Spark, ensure schema dictionaries use Spark SQL type
    names, not Pandas dtype names. The type string representations differ
    between engines even for equivalent types.

    This expectation extends Great Expectations' BatchExpectation base class
    and follows the standard expectation lifecycle.

    See Also
    --------
    BatchSchemaMatchesDict : The metric provider that extracts schema information
    great_expectations.expectations.expectation.BatchExpectation : Base class

    Examples
    --------
    Basic usage with Pandas DataFrame:

    >>> import pandas as pd
    >>> import great_expectations as gx
    >>> from adc_toolkit.data.validators.gx.custom_expectations import ExpectBatchSchemaToMatchDict
    >>>
    >>> # Create sample data
    >>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10.5, 20.3, 30.7], "category": ["A", "B", "C"]})
    >>>
    >>> # Define expected schema
    >>> expected_schema = {"id": "int64", "value": "float64", "category": "object"}
    >>>
    >>> # Create GX context and validate
    >>> context = gx.get_context()
    >>> batch = (
    ...     context.sources.add_pandas("source")
    ...     .add_dataframe_asset("asset")
    ...     .add_batch_definition("batch")
    ...     .build_batch_request(dataframe=df)
    ...     .get_batch_list()[0]
    ... )
    >>>
    >>> # Apply expectation
    >>> result = batch.expect_batch_schema_to_match_dict(schema=expected_schema)
    >>> assert result.success

    Usage with Spark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>>
    >>> # Create Spark DataFrame
    >>> df_spark = spark.createDataFrame([(1, 10.5, "A"), (2, 20.3, "B"), (3, 30.7, "C")], ["id", "value", "category"])
    >>>
    >>> # Define expected Spark schema
    >>> spark_schema = {"id": "bigint", "value": "double", "category": "string"}
    >>>
    >>> # Validate with Spark
    >>> result_spark = batch.expect_batch_schema_to_match_dict(schema=spark_schema)
    >>> assert result_spark.success

    Handling validation failures:

    >>> # Schema with wrong types
    >>> wrong_schema = {
    ...     "id": "object",  # Wrong type
    ...     "value": "int64",  # Wrong type
    ...     "category": "float64",  # Wrong type
    ... }
    >>>
    >>> result = batch.expect_batch_schema_to_match_dict(schema=wrong_schema)
    >>> assert not result.success
    >>> print(result.result["observed_value"])
    {'id': 'int64', 'value': 'float64', 'category': 'object'}
    >>> print(result.result["details"]["expected_schema"])
    {'id': 'object', 'value': 'int64', 'category': 'float64'}

    Using in an Expectation Suite:

    >>> # Add to an expectation suite
    >>> suite = context.add_expectation_suite("data_validation_suite")
    >>> suite.add_expectation(
    ...     ExpectationConfiguration(
    ...         expectation_type="expect_batch_schema_to_match_dict", kwargs={"schema": expected_schema}
    ...     )
    ... )
    """

    # These examples will be shown in the public gallery.
    # They will also be executed as unit tests for your Expectation.
    examples: ClassVar[list[dict[str, Any]]] = [
        {
            "dataset_name": "test_dataset",
            "data": {
                "a": [1, 2, 3],
                "b": [1.0, 2.0, 3.0],
                "c": ["aa", "bb", "cc"],
            },
            "only_for": ["pandas"],
            "tests": [
                {
                    "title": "positive_test",
                    "include_in_gallery": True,
                    "in": {"schema": {"a": "int64", "b": "float64", "c": "object"}},
                    "out": {"success": True},
                    "exact_match_out": False,
                },
                {
                    "title": "negative_test",
                    "include_in_gallery": True,
                    "in": {"schema": {"a": "object", "b": "int64", "c": "float64"}},
                    "out": {"success": False},
                    "exact_match_out": False,
                },
            ],
        },
        {
            "dataset_name": "test_dataset",
            "data": {
                "a": [1, 2, 3],
                "b": [1.0, 2.0, 3.0],
                "c": ["aa", "bb", "cc"],
            },
            "only_for": ["spark"],
            "tests": [
                {
                    "title": "positive_test",
                    "include_in_gallery": True,
                    "in": {"schema": {"a": "bigint", "b": "double", "c": "string"}},
                    "out": {"success": True},
                    "exact_match_out": False,
                },
                {
                    "title": "negative_test",
                    "include_in_gallery": True,
                    "in": {"schema": {"a": "string", "b": "bigint", "c": "double"}},
                    "out": {"success": False},
                    "exact_match_out": False,
                },
            ],
        },
    ]

    # This is a tuple consisting of all Metrics necessary to evaluate the Expectation.
    metric_dependencies = ("table.columns.schema", "table.columns")

    success_keys = ()

    # This dictionary contains default values for any parameters that should have default values.
    default_kwarg_values: ClassVar[dict[str, Any]] = {}

    def validate_configuration(self, configuration: ExpectationConfiguration | None) -> None:
        """
        Validate the expectation configuration.

        This method ensures that the expectation configuration is valid and
        contains all necessary parameters. It delegates to the parent class's
        validation and then performs any custom validation specific to this
        expectation.

        Parameters
        ----------
        configuration : ExpectationConfiguration or None
            The expectation configuration to validate. If None, the instance's
            configuration attribute is used.

        Returns
        -------
        None
            The method returns nothing on success.

        Raises
        ------
        InvalidExpectationConfigurationError
            If the configuration is invalid, missing required parameters, or
            contains invalid parameter values.

        Notes
        -----
        The base class validation checks:
        - Configuration is not None
        - Required success_keys are present
        - Metric dependencies are valid

        This method can be extended to add custom validation logic, such as:
        - Validating the 'schema' parameter is a dictionary
        - Ensuring schema keys are valid column names
        - Checking that schema values are valid type strings

        Currently, this implementation relies on the parent class validation
        and does not add additional custom checks beyond what Great Expectations
        provides by default.

        Examples
        --------
        >>> from great_expectations.core.expectation_configuration import ExpectationConfiguration
        >>>
        >>> # Valid configuration
        >>> config = ExpectationConfiguration(
        ...     expectation_type="expect_batch_schema_to_match_dict",
        ...     kwargs={"schema": {"id": "int64", "name": "object"}},
        ... )
        >>> expectation = ExpectBatchSchemaToMatchDict()
        >>> expectation.validate_configuration(config)  # No exception raised
        >>>
        >>> # Invalid configuration (missing schema)
        >>> bad_config = ExpectationConfiguration(expectation_type="expect_batch_schema_to_match_dict", kwargs={})
        >>> # expectation.validate_configuration(bad_config)  # Would raise error
        """
        super().validate_configuration(configuration)
        configuration = configuration or self.configuration

        # # Check other things in configuration.kwargs and raise Exceptions if needed
        # try:
        #     assert (
        #         ...
        #     ), "message"
        #     assert (
        #         ...
        #     ), "message"
        # except AssertionError as e:
        #     raise InvalidExpectationConfigurationError(str(e))

    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: dict,
        runtime_configuration: dict | None = None,  # noqa: ARG002
        execution_engine: ExecutionEngine | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """
        Execute the schema validation logic.

        This method performs the actual validation by comparing the observed
        DataFrame schema (from metrics) against the expected schema (from
        configuration). The validation succeeds only when schemas match exactly.

        Parameters
        ----------
        configuration : ExpectationConfiguration
            The expectation configuration containing the expected schema in
            kwargs["schema"].
        metrics : dict
            Dictionary of computed metrics. Must contain "table.columns.schema"
            with the observed schema as a dictionary.
        runtime_configuration : dict or None, default=None
            Runtime configuration options for this validation run. Not used
            in this implementation.
        execution_engine : ExecutionEngine or None, default=None
            The execution engine running the validation. Not used in this
            implementation.

        Returns
        -------
        dict of str to any
            Validation result dictionary containing:

            - success : bool
                True if observed schema exactly matches expected schema,
                False otherwise.
            - result : dict
                Detailed validation results with:

                - observed_value : dict of str to str
                    The actual schema found in the DataFrame.
                - details : dict
                    Additional information with:

                    - expected_schema : dict of str to str
                        The schema that was expected.

        Notes
        -----
        The validation performs an exact equality check on the schema dictionaries.
        This means:
        - All columns must be present in both schemas
        - Column names must match exactly (case-sensitive)
        - Data types must match exactly (string comparison)
        - Column order doesn't matter (dictionary comparison)

        Missing columns, extra columns, or type mismatches will all cause
        validation failure.

        The observed and expected schemas are both included in the result to
        facilitate debugging when validation fails.

        Examples
        --------
        >>> config = ExpectationConfiguration(
        ...     expectation_type="expect_batch_schema_to_match_dict",
        ...     kwargs={"schema": {"id": "int64", "value": "float64"}},
        ... )
        >>> metrics = {"table.columns.schema": {"id": "int64", "value": "float64"}}
        >>> expectation = ExpectBatchSchemaToMatchDict()
        >>> result = expectation._validate(config, metrics)
        >>> print(result["success"])
        True
        >>> print(result["result"]["observed_value"])
        {'id': 'int64', 'value': 'float64'}

        Example with schema mismatch:

        >>> config = ExpectationConfiguration(
        ...     expectation_type="expect_batch_schema_to_match_dict",
        ...     kwargs={"schema": {"id": "int64", "value": "int64"}},
        ... )
        >>> metrics = {"table.columns.schema": {"id": "int64", "value": "float64"}}
        >>> result = expectation._validate(config, metrics)
        >>> print(result["success"])
        False
        >>> print(result["result"]["details"]["expected_schema"]["value"])
        'int64'
        >>> print(result["result"]["observed_value"]["value"])
        'float64'
        """
        table_schema = metrics["table.columns.schema"]
        expected_schema = configuration.kwargs.get("schema", {})
        success = table_schema == expected_schema
        return {
            "success": success,
            "result": {
                "observed_value": table_schema,
                "details": {
                    "expected_schema": expected_schema,
                },
            },
        }

    # This object contains metadata for display in the public Gallery
    library_metadata: ClassVar[dict[str, Any]] = {
        "tags": [],  # Tags for this Expectation in the Gallery
        "contributors": [  # Github handles for all contributors to this Expectation.
            "ivan-adc",  # Don't forget to add your github handle here!
        ],
    }
