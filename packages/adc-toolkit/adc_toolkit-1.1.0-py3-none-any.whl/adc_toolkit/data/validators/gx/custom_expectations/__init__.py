"""
Custom Great Expectations (GX) expectations for schema validation.

This module provides custom expectations that extend Great Expectations' validation
capabilities with additional schema-based checks. These expectations are designed to
integrate seamlessly with GX's expectation framework and support both Pandas and
Spark DataFrames.

The primary use case is enforcing data contracts and catching schema drift in data
pipelines by validating that DataFrames conform to expected column structures and
data types.

Classes
-------
ExpectBatchSchemaToMatchDict
    Custom GX expectation that validates a DataFrame's schema (column names and
    data types) against a dictionary specification. Succeeds only when both column
    names and types match exactly.
BatchSchemaMatchesDict
    Metric provider that extracts schema information from a DataFrame batch,
    returning column names and their corresponding data types as a dictionary.
    Supports both Pandas and Spark execution engines.

Notes
-----
These custom expectations follow the Great Expectations extension pattern:

1. **MetricProvider** (BatchSchemaMatchesDict): Defines how to extract the metric
   from the data. Implements engine-specific logic for Pandas and Spark.
2. **Expectation** (ExpectBatchSchemaToMatchDict): Uses the metric to perform
   validation. Defines success criteria and result formatting.

The expectations are registered automatically when imported and can be used in GX
expectation suites like any built-in expectation.

**Version Requirements**

Great Expectations >= 0.15.0 is required for these custom expectations to function
properly.

**Type String Formats**

The schema dictionary must use type strings that match the execution engine:

- **Pandas**: Use numpy/pandas dtype strings like "int64", "float64", "object",
  "datetime64[ns]", "category", "bool"
- **Spark**: Use Spark SQL type strings like "bigint", "double", "string",
  "timestamp", "boolean"

Mixing type formats between engines will cause validation failures even when the
types are semantically equivalent (e.g., pandas "int64" vs Spark "bigint").

See Also
--------
great_expectations.expectations.expectation.BatchExpectation : Base class for batch-level expectations.
great_expectations.expectations.metrics.table_metric_provider.TableMetricProvider : Base metric provider.
adc_toolkit.data.validators.gx.GXValidator : Main GX validator for the toolkit.

Examples
--------
Basic usage with pandas DataFrame:

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
>>> # Create GX context and batch
>>> context = gx.get_context()
>>> batch = (
...     context.sources.add_pandas("source")
...     .add_dataframe_asset("asset")
...     .add_batch_definition("batch")
...     .build_batch_request(dataframe=df)
...     .get_batch_list()[0]
... )
>>>
>>> # Apply the custom expectation
>>> result = batch.expect_batch_schema_to_match_dict(schema=expected_schema)
>>> assert result.success

Using with Spark DataFrame:

>>> from pyspark.sql import SparkSession
>>> spark = SparkSession.builder.getOrCreate()
>>>
>>> # Create Spark DataFrame
>>> spark_df = spark.createDataFrame([(1, 10.5, "A"), (2, 20.3, "B"), (3, 30.7, "C")], ["id", "value", "category"])
>>>
>>> # Define expected Spark schema (note different type strings)
>>> spark_schema = {"id": "bigint", "value": "double", "category": "string"}
>>>
>>> # Validate with Spark
>>> result = batch.expect_batch_schema_to_match_dict(schema=spark_schema)
>>> assert result.success

Integration with GX expectation suite:

>>> from great_expectations.core.expectation_configuration import ExpectationConfiguration
>>>
>>> # Create an expectation suite
>>> suite = context.add_expectation_suite("data_quality_suite")
>>>
>>> # Add the custom expectation to the suite
>>> suite.add_expectation(
...     ExpectationConfiguration(
...         expectation_type="expect_batch_schema_to_match_dict", kwargs={"schema": expected_schema}
...     )
... )
>>>
>>> # Run validation
>>> checkpoint = context.add_checkpoint(
...     name="schema_checkpoint",
...     validations=[{"batch_request": batch_request, "expectation_suite_name": "data_quality_suite"}],
... )
>>> checkpoint_result = checkpoint.run()

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
"""
