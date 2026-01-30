"""
Utilities for extracting metadata and type information from data objects.

This module provides framework-agnostic utility functions for inspecting DataFrames
and extracting their structural properties. These utilities support both pandas and
PySpark DataFrames, enabling consistent data handling across different execution
engines.

The functions are primarily used internally by validators and data catalogs to:

- Determine which DataFrame framework is being used (pandas, pyspark, etc.)
- Extract schema information for validation and comparison
- Support engine-specific processing strategies
- Enable framework-agnostic data pipeline code

All functions work with data objects conforming to the Data protocol, which requires
``columns`` and ``dtypes`` attributes. This protocol-based approach ensures
compatibility with any DataFrame-like object that implements these attributes.

Functions
---------
extract_dataframe_type
    Determine the DataFrame framework type (pandas, pyspark, etc.) by inspecting
    the module path of the data object's type. Returns the top-level module name
    as a string.
extract_dataframe_schema
    Extract column names and data types as a dictionary mapping column names to
    type strings. Framework-agnostic function that works with both pandas and
    PySpark DataFrames.
extract_dataframe_schema_spark_native_format
    Extract Spark DataFrame schema using native Spark type names (e.g., "LongType",
    "StringType") rather than SQL format (e.g., "bigint", "string"). Specific to
    PySpark DataFrames.

Notes
-----
**Framework Detection**

The ``extract_dataframe_type`` function identifies the DataFrame framework by
examining the module path. This approach is robust across framework versions as
top-level module names remain stable:

- pandas DataFrames: Returns "pandas"
- PySpark DataFrames: Returns "pyspark"
- Other frameworks: Returns their respective module names

**Type String Formats**

Schema extraction functions return type information as strings, but the format
varies by framework:

**Pandas**: numpy/pandas dtype strings
    - Integer types: "int8", "int16", "int32", "int64", "uint8", etc.
    - Float types: "float16", "float32", "float64"
    - String/object: "object"
    - DateTime: "datetime64[ns]", "timedelta64[ns]"
    - Categorical: "category"
    - Boolean: "bool"

**PySpark** (SQL format via ``extract_dataframe_schema``):
    - Integer types: "tinyint", "smallint", "int", "bigint"
    - Float types: "float", "double", "decimal"
    - String: "string"
    - DateTime: "timestamp", "date"
    - Boolean: "boolean"
    - Complex: "array<type>", "map<type,type>", "struct<...>"

**PySpark** (Native format via ``extract_dataframe_schema_spark_native_format``):
    - Type objects: "LongType", "StringType", "DoubleType", "BooleanType", etc.
    - Includes trailing "()" for complex types: "ArrayType(StringType())"

**Use Cases**

These utilities enable several common data engineering patterns:

1. **Conditional Processing**: Apply framework-specific logic based on detected type
2. **Schema Validation**: Compare extracted schemas against expected specifications
3. **Auto-generation**: Generate validation schemas by introspecting data structure
4. **Logging**: Record schema information for debugging and auditing
5. **Type Conversion**: Determine appropriate type mappings between frameworks

**Integration with Validators**

The validator modules use these utilities extensively:

- **Pandera**: ``compile_schema_script`` uses these to generate schema files
- **Great Expectations**: Batch managers use these to select appropriate datasources
- **ValidatedDataCatalog**: Uses these to route data to appropriate validators

See Also
--------
adc_toolkit.data.abs.Data : Protocol defining the Data interface that these utilities work with.
adc_toolkit.data.validators.pandera : Pandera validator that uses these utilities.
adc_toolkit.data.validators.gx.batch_managers : GX batch managers that use framework detection.

Examples
--------
Determine DataFrame framework type:

>>> import pandas as pd
>>> from adc_toolkit.data.validators.table_utils import extract_dataframe_type
>>>
>>> df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
>>> framework = extract_dataframe_type(df)
>>> print(framework)
pandas

Extract schema from pandas DataFrame:

>>> from adc_toolkit.data.validators.table_utils import extract_dataframe_schema
>>>
>>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10.5, 20.3, 30.7], "name": ["Alice", "Bob", "Charlie"]})
>>> schema = extract_dataframe_schema(df)
>>> print(schema)
{'id': 'int64', 'value': 'float64', 'name': 'object'}

Extract schema from PySpark DataFrame:

>>> from pyspark.sql import SparkSession
>>> spark = SparkSession.builder.getOrCreate()
>>> spark_df = spark.createDataFrame([(1, 10.5, "Alice"), (2, 20.3, "Bob")], ["id", "value", "name"])
>>>
>>> # SQL format
>>> sql_schema = extract_dataframe_schema(spark_df)
>>> print(sql_schema)
{'id': 'bigint', 'value': 'double', 'name': 'string'}

Extract Spark schema in native format:

>>> from adc_toolkit.data.validators.table_utils import extract_dataframe_schema_spark_native_format
>>>
>>> native_schema = extract_dataframe_schema_spark_native_format(spark_df)
>>> print(native_schema)
{'id': 'LongType', 'value': 'DoubleType', 'name': 'StringType'}

Conditional processing based on framework type:

>>> def process_data(df):
...     framework = extract_dataframe_type(df)
...
...     if framework == "pandas":
...         # Use pandas-specific operations
...         return df.groupby("category").sum()
...     elif framework == "pyspark":
...         # Use Spark-specific operations
...         return df.groupBy("category").sum()
...     else:
...         raise ValueError(f"Unsupported framework: {framework}")

Schema comparison for validation:

>>> current_schema = extract_dataframe_schema(df)
>>> expected_schema = {"id": "int64", "value": "float64", "name": "object"}
>>>
>>> if current_schema != expected_schema:
...     raise ValueError(f"Schema mismatch.\\nExpected: {expected_schema}\\nGot: {current_schema}")

Logging schema information:

>>> import logging
>>> schema = extract_dataframe_schema(df)
>>> logging.info(f"Processing DataFrame with schema: {schema}")
INFO:root:Processing DataFrame with schema: {'id': 'int64', 'value': 'float64', 'name': 'object'}

Using in validator configuration:

>>> def configure_validator(data):
...     framework = extract_dataframe_type(data)
...
...     if framework == "pandas":
...         return PandasValidator()
...     elif framework == "pyspark":
...         return SparkValidator()
...     else:
...         return GenericValidator()

Schema-based type conversion:

>>> def convert_to_spark_types(pandas_schema):
...     type_mapping = {
...         "int64": "bigint",
...         "float64": "double",
...         "object": "string",
...         "bool": "boolean",
...     }
...     return {col: type_mapping.get(dtype, dtype) for col, dtype in pandas_schema.items()}
>>>
>>> pandas_schema = extract_dataframe_schema(df)
>>> spark_schema = convert_to_spark_types(pandas_schema)
>>> print(spark_schema)
{'id': 'bigint', 'value': 'double', 'name': 'string'}
"""
