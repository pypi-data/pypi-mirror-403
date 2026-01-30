"""
Extract DataFrame properties for validation and catalog operations.

This module provides utility functions for extracting metadata and type information
from data objects conforming to the Data protocol. These utilities support both
pandas and PySpark DataFrames, enabling framework-agnostic data handling.

The functions in this module are primarily used by validators and data catalogs
to inspect DataFrame structure, determine appropriate processing strategies, and
ensure compatibility with validation schemas.

Functions
---------
extract_dataframe_type(data)
    Determine the DataFrame framework type (pandas, pyspark, etc.).
extract_dataframe_schema(data)
    Extract column names and data types as a dictionary.
extract_dataframe_schema_spark_native_format(data)
    Extract Spark DataFrame schema in native Spark format.

Examples
--------
Determine DataFrame type:

>>> import pandas as pd
>>> df = pd.DataFrame({"a": [1, 2, 3]})
>>> extract_dataframe_type(df)
'pandas'

Extract schema from a pandas DataFrame:

>>> df = pd.DataFrame({"col1": [1, 2], "col2": [3.0, 4.0]})
>>> extract_dataframe_schema(df)
{'col1': 'int64', 'col2': 'float64'}

See Also
--------
adc_toolkit.data.abs.Data : Protocol defining the Data interface.
adc_toolkit.data.validators.gx.batch_managers : Uses these utilities for datasource detection.
adc_toolkit.data.validators.pandera : Uses these utilities for schema compilation.
"""

from adc_toolkit.data.abs import Data


def extract_dataframe_type(data: Data) -> str:
    """
    Determine the DataFrame framework type from its module name.

    This function identifies the data processing framework (pandas, PySpark, etc.)
    by inspecting the module path of the data object's type. It extracts the
    top-level module name, which typically indicates the framework being used.

    The function is framework-agnostic and works with any data object conforming
    to the Data protocol. It is commonly used to determine which processing
    strategy or validator to apply to a dataset.

    Parameters
    ----------
    data : Data
        A data object conforming to the Data protocol. Typically a pandas
        DataFrame, Spark DataFrame, or other compatible data structure with
        `columns` and `dtypes` properties.

    Returns
    -------
    str
        The top-level module name identifying the DataFrame framework.
        Common return values include:
        - "pandas" for pandas DataFrames
        - "pyspark" for PySpark DataFrames
        - Other framework names for alternative implementations

    See Also
    --------
    extract_dataframe_schema : Extract column names and types from a DataFrame.
    extract_dataframe_schema_spark_native_format : Extract Spark schema in native format.

    Notes
    -----
    The function operates by:
    1. Getting the type of the data object using `type(data)`
    2. Accessing the `__module__` attribute, which contains the full module path
       (e.g., "pandas.core.frame", "pyspark.sql.dataframe")
    3. Splitting on "." and returning the first component (the framework name)

    This approach is robust across different versions of the same framework, as
    the top-level module name typically remains stable even when internal module
    structure changes.

    The function does not validate that the data object actually conforms to
    the Data protocol. It simply extracts the module name from whatever object
    is passed.

    Examples
    --------
    Identify a pandas DataFrame:

    >>> import pandas as pd
    >>> df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    >>> extract_dataframe_type(df)
    'pandas'

    Identify a PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>> spark_df = spark.createDataFrame([(1, 2), (3, 4)], ["a", "b"])
    >>> extract_dataframe_type(spark_df)
    'pyspark'

    Use in conditional logic to apply framework-specific processing:

    >>> if extract_dataframe_type(df) == "pandas":
    ...     # Apply pandas-specific operations
    ...     result = df.groupby("category").sum()
    ... elif extract_dataframe_type(df) == "pyspark":
    ...     # Apply Spark-specific operations
    ...     result = df.groupBy("category").sum()

    Determine appropriate validator based on DataFrame type:

    >>> framework = extract_dataframe_type(data)
    >>> if framework == "pandas":
    ...     datasource = PandasDatasource(data_context)
    ... elif framework == "pyspark":
    ...     datasource = SparkDFDatasource(data_context)
    """
    return type(data).__module__.split(".")[0]


def extract_dataframe_schema(data: Data) -> dict[str, str]:
    """
    Extract DataFrame schema as a dictionary mapping column names to type strings.

    This function extracts the complete schema information from a DataFrame by
    converting the `dtypes` attribute into a dictionary with column names as keys
    and string representations of data types as values. This format is
    framework-agnostic and works with both pandas and PySpark DataFrames.

    The resulting dictionary is useful for schema comparison, validation setup,
    logging, and generating schema documentation. It provides a simple,
    serializable representation of the DataFrame's structure.

    Parameters
    ----------
    data : Data
        A data object conforming to the Data protocol with a `dtypes` attribute.
        Typically a pandas DataFrame (with dtypes as a pandas.Series) or a
        PySpark DataFrame (with dtypes as a list of tuples).

    Returns
    -------
    dict of str to str
        A dictionary mapping each column name to its data type as a string.
        For pandas DataFrames, types include "int64", "float64", "object", etc.
        For PySpark DataFrames, types include "bigint", "double", "string", etc.
        The specific type strings depend on the DataFrame framework being used.

    See Also
    --------
    extract_dataframe_type : Determine the DataFrame framework type.
    extract_dataframe_schema_spark_native_format : Extract Spark schema with native type names.

    Notes
    -----
    The function operates differently depending on the DataFrame type:

    For pandas DataFrames:
    - `data.dtypes` returns a pandas.Series with column names as index and
      numpy/pandas dtype objects as values
    - Converting to dict gives {column: dtype_object}
    - String conversion yields familiar type names like "int64", "float64"

    For PySpark DataFrames:
    - `data.dtypes` returns a list of tuples: [(column_name, type_string), ...]
    - Converting to dict gives {column: type_string}
    - Type strings are in Spark SQL format like "bigint", "double", "string"

    The function uses `dict(data.dtypes)` which works for both pandas (Series)
    and PySpark (list of tuples), making it framework-agnostic. The additional
    `str()` conversion ensures type objects are converted to readable strings.

    This function does not validate the data or check for schema consistency.
    It simply extracts and formats whatever schema information is present in
    the data object.

    Examples
    --------
    Extract schema from a pandas DataFrame:

    >>> import pandas as pd
    >>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10.5, 20.3, 30.7], "name": ["Alice", "Bob", "Charlie"]})
    >>> schema = extract_dataframe_schema(df)
    >>> schema
    {'id': 'int64', 'value': 'float64', 'name': 'object'}

    Extract schema from a PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>> spark_df = spark.createDataFrame([(1, 10.5, "Alice"), (2, 20.3, "Bob")], ["id", "value", "name"])
    >>> schema = extract_dataframe_schema(spark_df)
    >>> schema
    {'id': 'bigint', 'value': 'double', 'name': 'string'}

    Compare schemas between DataFrames:

    >>> df1 = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
    >>> df2 = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    >>> schema1 = extract_dataframe_schema(df1)
    >>> schema2 = extract_dataframe_schema(df2)
    >>> schema1 == schema2
    False
    >>> schema1["b"], schema2["b"]
    ('float64', 'object')

    Use for validation schema generation:

    >>> current_schema = extract_dataframe_schema(df)
    >>> expected_schema = {"id": "int64", "value": "float64", "name": "object"}
    >>> if current_schema != expected_schema:
    ...     raise ValueError(f"Schema mismatch: {current_schema} != {expected_schema}")

    Log schema information:

    >>> import logging
    >>> schema = extract_dataframe_schema(df)
    >>> logging.info(f"Processing DataFrame with schema: {schema}")
    INFO:root:Processing DataFrame with schema: {'id': 'int64', 'value': 'float64', 'name': 'object'}
    """
    return {col_name: str(col_type) for col_name, col_type in dict(data.dtypes).items()}


def extract_dataframe_schema_spark_native_format(data: Data) -> dict[str, str]:
    """
    Extract Spark DataFrame schema using native Spark type names.

    This function extracts schema information from a PySpark DataFrame using
    Spark's native schema representation. It accesses the `schema` attribute
    (a StructType object) and extracts the type name for each field, removing
    the trailing "()" suffix that Spark type objects include when converted
    to strings.

    This function is specifically designed for PySpark DataFrames and produces
    type names in Spark's native format (e.g., "LongType", "StringType",
    "DoubleType") rather than the SQL format used by `data.dtypes`
    (e.g., "bigint", "string", "double").

    Use this function when you need Spark-native type names for compatibility
    with Great Expectations Spark datasources, custom Spark validation logic,
    or when working with Spark's type system directly.

    Parameters
    ----------
    data : Data
        A PySpark DataFrame with a `schema` attribute. The schema should be
        a StructType object containing StructField objects with name and
        dataType attributes. Using this function with non-Spark data objects
        will raise an AttributeError.

    Returns
    -------
    dict of str to str
        A dictionary mapping each column name to its Spark-native type name.
        Type names follow Spark's naming convention with the "Type" suffix:
        - "LongType" for 64-bit integers
        - "IntegerType" for 32-bit integers
        - "DoubleType" for double-precision floats
        - "StringType" for strings
        - "BooleanType" for booleans
        - And other Spark data types

    Raises
    ------
    AttributeError
        If the data object does not have a `schema` attribute (i.e., it is
        not a PySpark DataFrame or compatible Spark data structure).

    See Also
    --------
    extract_dataframe_schema : Extract schema in a framework-agnostic format.
    extract_dataframe_type : Determine the DataFrame framework type.

    Notes
    -----
    The function operates by:
    1. Accessing `data.schema`, which returns a StructType object for Spark DataFrames
    2. Iterating over the StructField objects in the schema
    3. For each field, extracting the name and converting dataType to string
    4. Removing the trailing "()" from the type string representation
       (e.g., "LongType()" becomes "LongType")

    Spark type names differ from SQL type names:
    - `data.dtypes` returns [("col", "bigint"), ...] (SQL format)
    - This function returns {"col": "LongType"} (native Spark format)

    The SQL format is generally preferred for portability, but the native
    format is needed when:
    - Instantiating Spark DataType objects programmatically
    - Working with Great Expectations Spark expectations
    - Performing type matching with Spark's type system
    - Debugging Spark-specific type issues

    The `# type: ignore` comment suppresses mypy warnings about the `schema`
    attribute, which is not part of the Data protocol but is present in
    PySpark DataFrames.

    Examples
    --------
    Extract schema from a PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>> df = spark.createDataFrame([(1, 10.5, "Alice"), (2, 20.3, "Bob")], ["id", "value", "name"])
    >>> schema = extract_dataframe_schema_spark_native_format(df)
    >>> schema
    {'id': 'LongType', 'value': 'DoubleType', 'name': 'StringType'}

    Compare with SQL-format schema:

    >>> sql_schema = extract_dataframe_schema(df)
    >>> sql_schema
    {'id': 'bigint', 'value': 'double', 'name': 'string'}
    >>> native_schema = extract_dataframe_schema_spark_native_format(df)
    >>> native_schema
    {'id': 'LongType', 'value': 'DoubleType', 'name': 'StringType'}

    Use with Great Expectations Spark datasources:

    >>> native_schema = extract_dataframe_schema_spark_native_format(spark_df)
    >>> # Configure GX expectations using Spark-native type names
    >>> for col, spark_type in native_schema.items():
    ...     if spark_type == "LongType":
    ...         # Add expectations specific to long integer columns
    ...         pass

    Error when used with pandas DataFrame:

    >>> import pandas as pd
    >>> pandas_df = pd.DataFrame({"a": [1, 2, 3]})
    >>> extract_dataframe_schema_spark_native_format(pandas_df)
    Traceback (most recent call last):
        ...
    AttributeError: 'DataFrame' object has no attribute 'schema'

    Extract complex nested types:

    >>> from pyspark.sql.types import StructType, StructField, StringType, ArrayType
    >>> schema = StructType([StructField("name", StringType()), StructField("tags", ArrayType(StringType()))])
    >>> df = spark.createDataFrame([("Alice", ["tag1", "tag2"])], schema)
    >>> extract_dataframe_schema_spark_native_format(df)
    {'name': 'StringType', 'tags': 'ArrayType(StringType())'}
    """
    return {x.name: str(x.dataType)[:-2] for x in list(data.schema)}  # type: ignore
