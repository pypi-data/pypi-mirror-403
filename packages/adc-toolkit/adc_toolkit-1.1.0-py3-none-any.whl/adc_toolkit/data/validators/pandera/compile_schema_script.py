"""
Generate Pandera validation schema code from DataFrames.

This module provides schema compilation functionality that automatically generates
Pandera validation schema code from pandas and Spark DataFrames. The generated
schemas serve as starting templates for data validation, which can be customized
with additional checks and constraints.

The schema compilation process involves three main steps:
1. Extract DataFrame schema (column names and types) from the data object
2. Compile the schema information into Pandera column definitions
3. Insert the column definitions into a complete, executable Python script

This automation reduces boilerplate when setting up data validation and ensures
that generated schemas accurately reflect the actual DataFrame structure.

Classes
-------
SchemaScriptCompiler
    Abstract base class defining the schema compilation interface.
PandasSchemaScriptCompiler
    Generates Pandera schema code for pandas DataFrames.
SparkSchemaScriptCompiler
    Generates Pandera schema code for PySpark DataFrames.

Functions
---------
determine_compiler(df_type)
    Select the appropriate compiler based on DataFrame type.
compile_type_specific_schema_script(data)
    Main entry point for generating schema scripts from data objects.

Examples
--------
Generate a Pandera schema script from a pandas DataFrame:

>>> import pandas as pd
>>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10.5, 20.3, 30.7]})
>>> schema_script = compile_type_specific_schema_script(df)
>>> print(schema_script)
\"\"\"Pandera schema for Pandas.\"\"\"
import pandera.pandas as pa
...

Generate a schema script from a PySpark DataFrame:

>>> from pyspark.sql import SparkSession
>>> spark = SparkSession.builder.getOrCreate()
>>> spark_df = spark.createDataFrame([(1, 10.5), (2, 20.3)], ["id", "value"])
>>> schema_script = compile_type_specific_schema_script(spark_df)
>>> print(schema_script)
\"\"\"Pandera schema for Spark.\"\"\"
import pandera.pyspark as pa
...

See Also
--------
adc_toolkit.data.abs.Data : Protocol defining the Data interface.
adc_toolkit.data.validators.pandera.PanderaValidator : Uses generated schemas for validation.
adc_toolkit.data.validators.table_utils.table_properties : Utilities for extracting DataFrame metadata.

Notes
-----
The generated schema scripts are templates intended for customization. Users
should add specific validation checks, constraints, and business rules to the
`checks` parameter for each column.

Generated schemas include:
- Correct column names and data types from the source DataFrame
- Empty `checks` lists ready for custom validation logic
- Import statements for the appropriate Pandera module (pandas or pyspark)
- Helpful comments with documentation links

The schemas do not include:
- Nullability constraints (must be added manually)
- Value range checks (must be added manually)
- Custom validation logic (must be added manually)
- Index validation (must be added manually)

For complex validation requirements, consider profiling data with Great
Expectations first to understand statistical properties before defining
Pandera checks.
"""

from abc import ABC, abstractmethod

from adc_toolkit.data.abs import Data
from adc_toolkit.data.validators.table_utils.table_properties import (
    extract_dataframe_schema,
    extract_dataframe_schema_spark_native_format,
    extract_dataframe_type,
)


class SchemaScriptCompiler(ABC):
    """
    Abstract base class for compiling Pandera validation schema scripts.

    This class defines the interface for schema compilation, providing a
    template method pattern that orchestrates the schema generation process.
    Subclasses implement framework-specific logic for pandas and Spark DataFrames.

    The compilation process follows three steps:
    1. Extract schema metadata (column names and types) from the DataFrame
    2. Compile the schema metadata into Pandera column definition strings
    3. Insert the column definitions into a complete Python script template

    Methods
    -------
    extract_dataframe_schema(data)
        Extract column names and data types from a DataFrame.
    compile_schema_string(df_schema)
        Convert schema dictionary to Pandera column definition strings.
    insert_schema_string_to_script(df_schema_string)
        Insert column definitions into a complete Python script template.
    compile_schema_script(data)
        Orchestrate the full schema compilation process (template method).

    See Also
    --------
    PandasSchemaScriptCompiler : Concrete implementation for pandas DataFrames.
    SparkSchemaScriptCompiler : Concrete implementation for PySpark DataFrames.
    compile_type_specific_schema_script : Factory function that auto-selects compiler.

    Notes
    -----
    This class implements the Template Method design pattern. The
    `compile_schema_script` method defines the algorithm structure, while
    subclasses provide framework-specific implementations of each step.

    The abstract methods must be implemented by all subclasses to ensure
    consistent schema generation across different DataFrame frameworks.

    Generated schemas are intended as starting points. Users should customize
    the schemas by adding validation checks, constraints, and business rules
    appropriate for their data quality requirements.

    Examples
    --------
    Implementing a custom schema compiler:

    >>> class CustomSchemaCompiler(SchemaScriptCompiler):
    ...     def extract_dataframe_schema(self, data):
    ...         return {"col1": "int", "col2": "str"}
    ...
    ...     def compile_schema_string(self, df_schema):
    ...         return "\\n".join(f'"{k}": Column("{v}")' for k, v in df_schema.items())
    ...
    ...     def insert_schema_string_to_script(self, df_schema_string):
    ...         return f"schema = Schema({{\\n{df_schema_string}\\n}})"
    >>> compiler = CustomSchemaCompiler()
    >>> script = compiler.compile_schema_script(data)

    Using the template method:

    >>> compiler = PandasSchemaScriptCompiler()
    >>> # The template method coordinates all steps
    >>> schema_script = compiler.compile_schema_script(df)
    >>> # Equivalent to manually calling each step:
    >>> # schema = compiler.extract_dataframe_schema(df)
    >>> # schema_str = compiler.compile_schema_string(schema)
    >>> # script = compiler.insert_schema_string_to_script(schema_str)
    """

    @abstractmethod
    def extract_dataframe_schema(self, data: Data) -> dict[str, str]:
        """
        Extract DataFrame schema as a dictionary of column names to type strings.

        This method extracts metadata from a DataFrame conforming to the Data
        protocol, returning column names and their corresponding data types.
        The extraction strategy varies by DataFrame framework (pandas vs. Spark).

        Parameters
        ----------
        data : Data
            A DataFrame object conforming to the Data protocol, with `columns`
            and `dtypes` properties. Typically a pandas DataFrame or PySpark
            DataFrame.

        Returns
        -------
        dict of str to str
            A dictionary mapping column names (keys) to data type strings (values).
            The format of type strings depends on the DataFrame framework:
            - pandas: "int64", "float64", "object", etc.
            - Spark: "LongType", "DoubleType", "StringType", etc.

        See Also
        --------
        compile_schema_string : Converts the extracted schema to column definitions.
        adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_schema : Utility for pandas.
        adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_schema_spark_native_format : Utility for Spark.

        Notes
        -----
        Implementations should use the appropriate utility function from
        `table_properties` module to ensure consistent schema extraction
        across the framework.

        The extracted schema represents the DataFrame's current state. If the
        DataFrame structure changes after extraction, the schema will not
        reflect those changes.

        Examples
        --------
        Extract schema from a pandas DataFrame:

        >>> import pandas as pd
        >>> df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        >>> compiler = PandasSchemaScriptCompiler()
        >>> schema = compiler.extract_dataframe_schema(df)
        >>> schema
        {'id': 'int64', 'name': 'object'}

        Extract schema from a Spark DataFrame:

        >>> compiler = SparkSchemaScriptCompiler()
        >>> schema = compiler.extract_dataframe_schema(spark_df)
        >>> schema
        {'id': 'LongType', 'name': 'StringType'}
        """

    @abstractmethod
    def compile_schema_string(self, df_schema: dict) -> str:
        """
        Compile schema dictionary into Pandera column definition strings.

        This method converts a schema dictionary (column names to types) into
        formatted Python code strings that define Pandera Column objects. The
        generated strings are ready to be inserted into a DataFrameSchema
        dictionary.

        Parameters
        ----------
        df_schema : dict
            A dictionary mapping column names (str) to data type strings (str).
            Typically obtained from `extract_dataframe_schema`.

        Returns
        -------
        str
            A multi-line string containing Pandera column definitions, formatted
            with proper indentation and syntax. Each line defines one column in
            the format:
            "\t\"column_name\": pa.Column(\"type\", checks=[]),\\n"

            The string includes trailing newlines and tabs for proper formatting
            when inserted into a schema template.

        See Also
        --------
        extract_dataframe_schema : Generates the input schema dictionary.
        insert_schema_string_to_script : Inserts the compiled string into a template.

        Notes
        -----
        The generated column definitions include:
        - Properly quoted column names (handles special characters)
        - Type specifications appropriate for the DataFrame framework
        - Empty `checks` lists for users to populate with validation logic
        - Consistent indentation (one tab) for readability
        - Trailing commas and newlines for proper Python syntax

        Column names are string-quoted to handle names with spaces, special
        characters, or Python keywords.

        The empty `checks=[]` parameter serves as a placeholder, indicating
        where users should add validation logic such as:
        - Range checks: pa.Check.in_range(0, 100)
        - Regex patterns: pa.Check.str_matches(r"^[A-Z]{3}$")
        - Custom functions: pa.Check(lambda s: s.str.len() > 0)

        Examples
        --------
        Compile a pandas schema dictionary:

        >>> schema_dict = {"id": "int64", "name": "object", "score": "float64"}
        >>> compiler = PandasSchemaScriptCompiler()
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"id": pa.Column("int64", checks=[]),
        \t"name": pa.Column("object", checks=[]),
        \t"score": pa.Column("float64", checks=[]),

        Compile a Spark schema dictionary:

        >>> schema_dict = {"id": "LongType", "name": "StringType"}
        >>> compiler = SparkSchemaScriptCompiler()
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"id": pa.Column(T.LongType(), checks=[]),
        \t"name": pa.Column(T.StringType(), checks=[]),
        """

    @abstractmethod
    def insert_schema_string_to_script(self, df_schema_string: str) -> str:
        """
        Insert column definitions into a complete Python script template.

        This method takes the compiled column definition string and embeds it
        into a complete, executable Python script that defines a Pandera
        DataFrameSchema. The script includes necessary imports, comments, and
        documentation links.

        Parameters
        ----------
        df_schema_string : str
            Multi-line string containing Pandera column definitions, typically
            generated by `compile_schema_string`. Should include proper
            indentation and formatting.

        Returns
        -------
        str
            A complete Python script as a string, ready to be written to a .py
            file. The script includes:
            - Module docstring describing the schema purpose
            - Import statements for Pandera and required dependencies
            - Instructional comments for customization
            - Documentation links for reference
            - The column definitions formatted within a DataFrameSchema
            - Proper Python syntax and formatting

        See Also
        --------
        compile_schema_string : Generates the column definitions to insert.
        compile_schema_script : Orchestrates the full process.

        Notes
        -----
        The generated script is framework-specific:
        - Pandas schemas import `pandera.pandas as pa`
        - Spark schemas import `pandera.pyspark as pa` and `pyspark.sql.types as T`

        Generated scripts include helpful comments that:
        - Explain where to add custom validation checks
        - Provide example check syntax
        - Link to relevant Pandera documentation

        The scripts are intended to be saved as .py files in a schemas directory
        and imported for use with PanderaValidator. Users should customize the
        generated schemas by adding:
        - Validation checks to the `checks` parameter
        - Nullability constraints (nullable=True/False)
        - Index validation
        - Coerce type options
        - Global DataFrameSchema parameters

        The generated schema variable is always named `schema` for consistency
        and ease of import.

        Examples
        --------
        Generate a complete pandas schema script:

        >>> column_defs = '\\t"id": pa.Column("int64", checks=[]),\\n'
        >>> compiler = PandasSchemaScriptCompiler()
        >>> script = compiler.insert_schema_string_to_script(column_defs)
        >>> print(script)
        \"\"\"Pandera schema for Pandas.\"\"\"
        import pandera.pandas as pa
        <BLANKLINE>
        # Insert your additional checks to `checks` list parameter for each column
        ...

        Save generated script to a file:

        >>> script = compiler.insert_schema_string_to_script(column_defs)
        >>> with open("schemas/my_data_schema.py", "w") as f:
        ...     f.write(script)

        Import and use the generated schema:

        >>> # In schemas/my_data_schema.py (after customization):
        >>> # schema = pa.DataFrameSchema({
        >>> #     "id": pa.Column("int64", checks=[pa.Check.greater_than(0)]),
        >>> #     ...
        >>> # })
        >>> from schemas.my_data_schema import schema
        >>> validated_df = schema.validate(df)
        """
        ...

    def compile_schema_script(self, data: Data) -> str:
        """
        Compile a complete Pandera schema script from a DataFrame.

        This is the main template method that orchestrates the entire schema
        compilation process. It coordinates the three steps of schema generation:
        extracting DataFrame schema, compiling column definitions, and inserting
        them into a complete Python script.

        This method should be called by users to generate schemas. It delegates
        to the abstract methods which are implemented by subclasses for specific
        DataFrame frameworks.

        Parameters
        ----------
        data : Data
            A DataFrame object conforming to the Data protocol. Typically a
            pandas DataFrame or PySpark DataFrame with `columns` and `dtypes`
            properties.

        Returns
        -------
        str
            A complete, executable Python script as a string. The script defines
            a Pandera DataFrameSchema that can be saved to a .py file and used
            for data validation. The script includes:
            - All necessary imports
            - Column definitions with correct names and types
            - Placeholder `checks` lists for customization
            - Helpful comments and documentation links

        See Also
        --------
        extract_dataframe_schema : Step 1 - Extract schema from DataFrame.
        compile_schema_string : Step 2 - Compile schema to column definitions.
        insert_schema_string_to_script : Step 3 - Insert definitions into script template.
        compile_type_specific_schema_script : Factory function that auto-selects compiler.

        Notes
        -----
        This method implements the Template Method design pattern, defining
        the algorithm structure while delegating specific steps to abstract
        methods. This ensures consistent behavior across different DataFrame
        frameworks while allowing framework-specific customization.

        The compilation process is stateless and idempotent: calling this
        method multiple times with the same DataFrame will produce the same
        schema script.

        The generated script is a starting template that should be customized
        with validation logic appropriate for your data quality requirements.
        After generation:
        1. Save the script to a .py file
        2. Add validation checks, constraints, and business rules
        3. Test the schema with sample data
        4. Use with PanderaValidator for automated validation

        Error handling is minimal in this method. Errors from underlying
        utility functions will propagate to the caller.

        Examples
        --------
        Generate a schema script from a pandas DataFrame:

        >>> import pandas as pd
        >>> df = pd.DataFrame(
        ...     {"customer_id": [1, 2, 3], "revenue": [100.5, 200.3, 150.7], "status": ["active", "inactive", "active"]}
        ... )
        >>> compiler = PandasSchemaScriptCompiler()
        >>> schema_script = compiler.compile_schema_script(df)
        >>> print(schema_script)
        \"\"\"Pandera schema for Pandas.\"\"\"
        import pandera.pandas as pa
        ...

        Save and customize the generated schema:

        >>> schema_script = compiler.compile_schema_script(df)
        >>> with open("schemas/customer_schema.py", "w") as f:
        ...     f.write(schema_script)
        >>> # Now edit schemas/customer_schema.py to add validation checks:
        >>> # "customer_id": pa.Column("int64", checks=[pa.Check.greater_than(0)]),
        >>> # "revenue": pa.Column("float64", checks=[pa.Check.in_range(0, 1000000)]),
        >>> # "status": pa.Column("object", checks=[pa.Check.isin(["active", "inactive"])]),

        Use in an automated workflow:

        >>> def generate_schema_file(df, output_path):
        ...     compiler = PandasSchemaScriptCompiler()
        ...     script = compiler.compile_schema_script(df)
        ...     with open(output_path, "w") as f:
        ...         f.write(script)
        ...     return output_path
        >>> schema_file = generate_schema_file(df, "schemas/auto_generated.py")

        Generate schemas for multiple DataFrames:

        >>> compiler = PandasSchemaScriptCompiler()
        >>> for name, df in dataframes.items():
        ...     script = compiler.compile_schema_script(df)
        ...     with open(f"schemas/{name}_schema.py", "w") as f:
        ...         f.write(script)
        """
        df_schema = self.extract_dataframe_schema(data)
        df_schema_string = self.compile_schema_string(df_schema)
        schema_script = self.insert_schema_string_to_script(df_schema_string)
        return schema_script


class PandasSchemaScriptCompiler(SchemaScriptCompiler):
    """
    Compile Pandera validation schema scripts for pandas DataFrames.

    This compiler generates Pandera schema code specifically for pandas DataFrames,
    using pandas-compatible data types and the `pandera.pandas` module. It extracts
    schema information from a pandas DataFrame and produces a complete Python script
    that defines a Pandera DataFrameSchema for validation.

    The generated schemas use pandas type strings (e.g., "int64", "float64",
    "object") and support all pandas-specific validation features available in
    Pandera, including element-wise checks, Series-level checks, and custom
    validation functions.

    Methods
    -------
    extract_dataframe_schema(data)
        Extract column names and pandas dtypes from a DataFrame.
    compile_schema_string(df_schema)
        Generate pandas-specific Pandera column definitions.
    insert_schema_string_to_script(df_schema_string)
        Insert column definitions into a pandas schema script template.

    See Also
    --------
    SchemaScriptCompiler : Abstract base class defining the interface.
    SparkSchemaScriptCompiler : Compiler for PySpark DataFrames.
    compile_type_specific_schema_script : Factory function that auto-selects compiler.
    adc_toolkit.data.validators.pandera.PanderaValidator : Uses generated schemas for validation.

    Notes
    -----
    This compiler is designed for pandas DataFrames and uses:
    - pandas type strings: "int64", "float64", "object", "datetime64[ns]", etc.
    - `pandera.pandas` module for pandas-specific functionality
    - Element-wise and Series-level check support

    Generated schemas are templates that require customization. Common checks
    to add include:
    - Value ranges: pa.Check.in_range(0, 100)
    - String patterns: pa.Check.str_matches(r"^[A-Z]{3}$")
    - String length: pa.Check(lambda s: s.str.len() > 0, element_wise=True)
    - Uniqueness: pa.Check(lambda s: ~s.duplicated().any())
    - Non-null: Set nullable=False in Column constructor
    - Custom functions: pa.Check(lambda s: custom_validation(s))

    The compiler preserves all column names and types from the source DataFrame,
    including columns with special characters or non-standard names.

    Examples
    --------
    Generate a schema script from a pandas DataFrame:

    >>> import pandas as pd
    >>> df = pd.DataFrame(
    ...     {
    ...         "user_id": [1, 2, 3, 4, 5],
    ...         "email": ["a@example.com", "b@example.com", "c@example.com", "d@example.com", "e@example.com"],
    ...         "age": [25, 30, 35, 40, 45],
    ...         "score": [85.5, 90.2, 78.9, 92.1, 88.3],
    ...     }
    ... )
    >>> compiler = PandasSchemaScriptCompiler()
    >>> schema_script = compiler.compile_schema_script(df)
    >>> print(schema_script)
    \"\"\"Pandera schema for Pandas.\"\"\"
    import pandera.pandas as pa
    <BLANKLINE>
    # Insert your additional checks to `checks` list parameter for each column
    # e.g. checks=[pa.Check(lambda s: s.str.len() > 0, element_wise=True)]
    # refer to https://pandera.readthedocs.io/en/stable/checks.html for more details.
    <BLANKLINE>
    schema = pa.DataFrameSchema({
    \t"user_id": pa.Column("int64", checks=[]),
    \t"email": pa.Column("object", checks=[]),
    \t"age": pa.Column("int64", checks=[]),
    \t"score": pa.Column("float64", checks=[]),
    })

    Save and customize the generated schema:

    >>> schema_script = compiler.compile_schema_script(df)
    >>> with open("schemas/user_data.py", "w") as f:
    ...     f.write(schema_script)
    >>> # Edit schemas/user_data.py to add validation:
    >>> # "user_id": pa.Column("int64", checks=[pa.Check.greater_than(0)], unique=True),
    >>> # "email": pa.Column("object", checks=[pa.Check.str_matches(r"^[^@]+@[^@]+\\.[^@]+$")]),
    >>> # "age": pa.Column("int64", checks=[pa.Check.in_range(0, 120)]),
    >>> # "score": pa.Column("float64", checks=[pa.Check.in_range(0, 100)]),

    Generate schemas for DataFrames with various pandas types:

    >>> import numpy as np
    >>> df = pd.DataFrame(
    ...     {
    ...         "int_col": [1, 2, 3],
    ...         "float_col": [1.5, 2.5, 3.5],
    ...         "str_col": ["a", "b", "c"],
    ...         "bool_col": [True, False, True],
    ...         "datetime_col": pd.date_range("2024-01-01", periods=3),
    ...         "category_col": pd.Categorical(["cat1", "cat2", "cat1"]),
    ...     }
    ... )
    >>> compiler = PandasSchemaScriptCompiler()
    >>> schema_script = compiler.compile_schema_script(df)
    >>> # Schema includes all column types: int64, float64, object, bool, datetime64[ns], category

    Use in a schema generation workflow:

    >>> def setup_validation_for_dataset(df, dataset_name, output_dir="schemas"):
    ...     compiler = PandasSchemaScriptCompiler()
    ...     script = compiler.compile_schema_script(df)
    ...     output_path = f"{output_dir}/{dataset_name}_schema.py"
    ...     with open(output_path, "w") as f:
    ...         f.write(script)
    ...     print(f"Generated schema template at {output_path}")
    ...     print("Please customize the schema with appropriate validation checks.")
    ...     return output_path
    """

    def extract_dataframe_schema(self, data: Data) -> dict[str, str]:
        """
        Extract pandas DataFrame schema as a column-to-type mapping.

        This method extracts the schema from a pandas DataFrame by reading the
        `dtypes` attribute and converting it to a dictionary. It uses the
        `extract_dataframe_schema` utility function which handles the conversion
        of pandas dtype objects to string representations.

        Parameters
        ----------
        data : Data
            A pandas DataFrame with `columns` and `dtypes` properties. The
            DataFrame can contain any pandas-supported data types including
            numeric types, strings, datetimes, categories, and nullable types.

        Returns
        -------
        dict of str to str
            A dictionary mapping column names to pandas type strings. Common
            type strings include:
            - "int64", "int32", "int16", "int8" for integers
            - "float64", "float32" for floats
            - "object" for strings and mixed types
            - "bool" for booleans
            - "datetime64[ns]" for timestamps
            - "category" for categorical data
            - "Int64", "Float64" for nullable integer/float types
            - "string" for string dtype (pandas >= 1.0)

        See Also
        --------
        compile_schema_string : Uses the extracted schema to generate column definitions.
        adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_schema : Underlying utility function.

        Notes
        -----
        This method delegates to the `extract_dataframe_schema` utility function,
        which handles the conversion of pandas dtype objects to their string
        representations. The resulting dictionary preserves the exact column
        names from the DataFrame, including names with spaces, special characters,
        or Python keywords.

        The string representations match pandas' dtype string format, which may
        differ from the underlying numpy dtype for some types (e.g., nullable
        integer "Int64" vs. "int64").

        Examples
        --------
        Extract schema from a simple DataFrame:

        >>> import pandas as pd
        >>> df = pd.DataFrame({"id": [1, 2, 3], "value": [10.5, 20.3, 30.7], "name": ["Alice", "Bob", "Charlie"]})
        >>> compiler = PandasSchemaScriptCompiler()
        >>> schema = compiler.extract_dataframe_schema(df)
        >>> schema
        {'id': 'int64', 'value': 'float64', 'name': 'object'}

        Extract schema with various pandas types:

        >>> df = pd.DataFrame(
        ...     {
        ...         "int_col": pd.array([1, 2, 3], dtype="Int64"),
        ...         "date_col": pd.date_range("2024-01-01", periods=3),
        ...         "cat_col": pd.Categorical(["A", "B", "A"]),
        ...     }
        ... )
        >>> schema = compiler.extract_dataframe_schema(df)
        >>> schema
        {'int_col': 'Int64', 'date_col': 'datetime64[ns]', 'cat_col': 'category'}

        Handle DataFrames with special column names:

        >>> df = pd.DataFrame(
        ...     {
        ...         "column with spaces": [1, 2, 3],
        ...         "column-with-dashes": [4, 5, 6],
        ...         "class": [7, 8, 9],  # Python keyword
        ...     }
        ... )
        >>> schema = compiler.extract_dataframe_schema(df)
        >>> schema
        {'column with spaces': 'int64', 'column-with-dashes': 'int64', 'class': 'int64'}
        """
        return extract_dataframe_schema(data)

    def compile_schema_string(self, df_schema: dict) -> str:
        """
        Compile pandas schema dictionary into Pandera column definition strings.

        This method converts a schema dictionary into formatted Python code
        strings that define Pandera Column objects for pandas DataFrames. Each
        column is formatted as a pandas-compatible column definition with the
        type string directly passed to the Column constructor.

        Parameters
        ----------
        df_schema : dict
            A dictionary mapping column names (str) to pandas type strings (str).
            Type strings should be valid pandas dtype strings like "int64",
            "float64", "object", "datetime64[ns]", etc.

        Returns
        -------
        str
            A multi-line string containing Pandera column definitions for pandas.
            Each line has the format:
            "\t\"column_name\": pa.Column(\"type_string\", checks=[]),\\n"

            The string includes proper indentation (one tab), quoted column
            names, quoted type strings, empty checks lists, trailing commas,
            and newlines.

        See Also
        --------
        extract_dataframe_schema : Generates the input schema dictionary.
        insert_schema_string_to_script : Inserts the result into a script template.

        Notes
        -----
        The generated column definitions use pandas-specific features:
        - Type strings are quoted and passed directly to pa.Column
        - The format matches pandera.pandas column syntax
        - Empty `checks=[]` parameters are placeholders for validation logic

        Column names are quoted with double quotes to handle:
        - Names containing spaces: "column with spaces"
        - Names with special characters: "column-with-dashes"
        - Python keywords: "class", "def", "return"
        - Unicode characters: "température"

        Type strings are also quoted to match Pandera's pandas API, which
        accepts dtype strings rather than type constructors.

        Users should customize the generated schemas by adding checks such as:
        - pa.Check.greater_than(0)
        - pa.Check.isin(["value1", "value2", "value3"])
        - pa.Check.str_startswith("prefix")
        - pa.Check(lambda s: s.str.len() > 5, element_wise=True)
        - pa.Check(lambda s: custom_validator(s))

        Examples
        --------
        Compile a simple schema dictionary:

        >>> schema_dict = {"id": "int64", "name": "object", "score": "float64"}
        >>> compiler = PandasSchemaScriptCompiler()
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"id": pa.Column("int64", checks=[]),
        \t"name": pa.Column("object", checks=[]),
        \t"score": pa.Column("float64", checks=[]),

        Compile schema with various pandas types:

        >>> schema_dict = {"int_col": "Int64", "date_col": "datetime64[ns]", "cat_col": "category", "bool_col": "bool"}
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"int_col": pa.Column("Int64", checks=[]),
        \t"date_col": pa.Column("datetime64[ns]", checks=[]),
        \t"cat_col": pa.Column("category", checks=[]),
        \t"bool_col": pa.Column("bool", checks=[]),

        Compile schema with special column names:

        >>> schema_dict = {"column with spaces": "int64", "column-with-dashes": "float64", "class": "object"}
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"column with spaces": pa.Column("int64", checks=[]),
        \t"column-with-dashes": pa.Column("float64", checks=[]),
        \t"class": pa.Column("object", checks=[]),
        """
        schema_string = ""
        for col_name, col_type in df_schema.items():
            schema_string += f'\t"{col_name}": pa.Column("{col_type}", checks=[]),\n'
        return schema_string

    def insert_schema_string_to_script(self, df_schema_string: str) -> str:
        """
        Insert pandas column definitions into a complete Python script template.

        This method embeds the compiled column definition string into a complete,
        executable Python script that defines a Pandera DataFrameSchema for
        pandas. The script includes pandas-specific imports, documentation links,
        and helpful comments for customization.

        Parameters
        ----------
        df_schema_string : str
            Multi-line string containing Pandera column definitions for pandas,
            formatted with proper indentation. Typically generated by
            `compile_schema_string`.

        Returns
        -------
        str
            A complete Python script as a string, ready to be saved as a .py
            file. The script includes:
            - Module docstring: "Pandera schema for Pandas."
            - Import statement: `import pandera.pandas as pa`
            - Instructional comments with example check syntax
            - Documentation link: https://pandera.readthedocs.io/en/stable/checks.html
            - DataFrameSchema definition with embedded column definitions
            - Proper Python syntax and formatting

        See Also
        --------
        compile_schema_string : Generates the column definitions to insert.
        compile_schema_script : Orchestrates the full compilation process.

        Notes
        -----
        The generated script is specifically for pandas DataFrames and uses:
        - `pandera.pandas` module (aliased as `pa`)
        - Pandas-compatible type strings
        - Element-wise and Series-level check examples

        The instructional comments include:
        - Where to add custom validation checks
        - An example of element-wise string validation
        - A link to Pandera's check documentation

        The script follows this structure:
        1. Module docstring
        2. Import statements
        3. Blank line
        4. Instructional comments
        5. Blank line
        6. Schema definition with DataFrameSchema and column dict
        7. Closing parenthesis and newline

        Users should customize the generated schema by:
        - Adding validation checks to the `checks` parameter
        - Setting `nullable=True` or `nullable=False` for columns
        - Adding `coerce=True` to enable type coercion
        - Setting `unique=True` for columns requiring unique values
        - Adding `regex=True` for pattern-based column selection
        - Defining custom check functions

        The schema variable is named `schema` to enable easy imports:
        `from schemas.my_schema import schema`

        Examples
        --------
        Generate a complete pandas schema script:

        >>> column_defs = '''\\t"id": pa.Column("int64", checks=[]),
        ... \\t"name": pa.Column("object", checks=[]),
        ... \\t"score": pa.Column("float64", checks=[]),
        ... '''
        >>> compiler = PandasSchemaScriptCompiler()
        >>> script = compiler.insert_schema_string_to_script(column_defs)
        >>> print(script)
        \"\"\"Pandera schema for Pandas.\"\"\"
        import pandera.pandas as pa
        <BLANKLINE>
        # Insert your additional checks to `checks` list parameter for each column
        # e.g. checks=[pa.Check(lambda s: s.str.len() > 0, element_wise=True)]
        # refer to https://pandera.readthedocs.io/en/stable/checks.html for more details.
        <BLANKLINE>
        schema = pa.DataFrameSchema({
        \t"id": pa.Column("int64", checks=[]),
        \t"name": pa.Column("object", checks=[]),
        \t"score": pa.Column("float64", checks=[]),
        })

        Save and use the generated script:

        >>> script = compiler.insert_schema_string_to_script(column_defs)
        >>> with open("schemas/my_data.py", "w") as f:
        ...     f.write(script)
        >>> # Customize schemas/my_data.py with validation checks
        >>> # Then import and use:
        >>> from schemas.my_data import schema
        >>> validated_df = schema.validate(df)

        Example of customized schema after generation:

        >>> # Generated schema (before customization):
        >>> # schema = pa.DataFrameSchema({
        >>> #     "email": pa.Column("object", checks=[]),
        >>> #     "age": pa.Column("int64", checks=[]),
        >>> # })
        >>> #
        >>> # Customized schema (after adding validation):
        >>> # schema = pa.DataFrameSchema({
        >>> #     "email": pa.Column(
        >>> #         "object",
        >>> #         checks=[pa.Check.str_matches(r"^[^@]+@[^@]+\\.[^@]+$")],
        >>> #         nullable=False
        >>> #     ),
        >>> #     "age": pa.Column(
        >>> #         "int64",
        >>> #         checks=[pa.Check.in_range(0, 120)],
        >>> #         nullable=False,
        >>> #         coerce=True
        >>> #     ),
        >>> # })
        """
        schema_script = f'''"""Pandera schema for Pandas."""
import pandera.pandas as pa

# Insert your additional checks to `checks` list parameter for each column
# e.g. checks=[pa.Check(lambda s: s.str.len() > 0, element_wise=True)]
# refer to https://pandera.readthedocs.io/en/stable/checks.html for more details.

schema = pa.DataFrameSchema({{
{df_schema_string}}})
'''
        return schema_script


class SparkSchemaScriptCompiler(SchemaScriptCompiler):
    """
    Compile Pandera validation schema scripts for PySpark DataFrames.

    This compiler generates Pandera schema code specifically for PySpark DataFrames,
    using Spark's native data type system and the `pandera.pyspark` module. It
    extracts schema information from a PySpark DataFrame and produces a complete
    Python script that defines a Pandera DataFrameSchema for distributed data
    validation.

    The generated schemas use Spark-native type names (e.g., "LongType",
    "StringType", "DoubleType") from `pyspark.sql.types` and support Spark-specific
    validation features available in Pandera, including distributed checks and
    Spark SQL expressions.

    Methods
    -------
    extract_dataframe_schema(data)
        Extract column names and Spark-native types from a DataFrame.
    compile_schema_string(df_schema)
        Generate Spark-specific Pandera column definitions.
    insert_schema_string_to_script(df_schema_string)
        Insert column definitions into a Spark schema script template.

    See Also
    --------
    SchemaScriptCompiler : Abstract base class defining the interface.
    PandasSchemaScriptCompiler : Compiler for pandas DataFrames.
    compile_type_specific_schema_script : Factory function that auto-selects compiler.
    adc_toolkit.data.validators.pandera.PanderaValidator : Uses generated schemas for validation.

    Notes
    -----
    This compiler is designed for PySpark DataFrames and uses:
    - Spark-native type names: "LongType", "StringType", "DoubleType", etc.
    - `pandera.pyspark` module for Spark-specific functionality
    - `pyspark.sql.types` module (aliased as `T`) for type constructors
    - Distributed validation compatible with Spark's execution model

    Generated schemas are templates that require customization. Common checks
    to add for Spark DataFrames include:
    - Value ranges: pa.Check.greater_than(0)
    - Set membership: pa.Check.isin(["value1", "value2"])
    - Custom SQL expressions: pa.Check(lambda df: df.filter(...))
    - Null checks: Set nullable=False in Column constructor
    - Statistical checks: pa.Check(lambda s: s.mean() > threshold)

    Spark type constructors require parentheses: `T.LongType()` not `T.LongType`.
    The compiler generates type constructors with the required parentheses.

    The compiler uses Spark-native type names rather than SQL type names:
    - "LongType" (not "bigint")
    - "StringType" (not "string")
    - "DoubleType" (not "double")
    - "IntegerType" (not "int")
    - "BooleanType" (not "boolean")

    Validation with Spark DataFrames runs distributedly across the cluster,
    so checks should be designed to work efficiently in a distributed context.

    Examples
    --------
    Generate a schema script from a PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>> df = spark.createDataFrame(
    ...     [(1, "Alice", 85.5), (2, "Bob", 90.2), (3, "Charlie", 78.9)], ["user_id", "name", "score"]
    ... )
    >>> compiler = SparkSchemaScriptCompiler()
    >>> schema_script = compiler.compile_schema_script(df)
    >>> print(schema_script)
    \"\"\"Pandera schema for Spark.\"\"\"
    import pandera.pyspark as pa
    import pyspark.sql.types as T
    <BLANKLINE>
    # Insert your additional checks to `checks` list parameter for each column
    # e.g. checks=[pa.Check.greater_than(0)]
    # refer to https://pandera.readthedocs.io/en/stable/pyspark_sql.html for more details.
    <BLANKLINE>
    schema = pa.DataFrameSchema({
    \t"user_id": pa.Column(T.LongType(), checks=[]),
    \t"name": pa.Column(T.StringType(), checks=[]),
    \t"score": pa.Column(T.DoubleType(), checks=[]),
    })

    Save and customize the generated schema:

    >>> schema_script = compiler.compile_schema_script(df)
    >>> with open("schemas/user_data_spark.py", "w") as f:
    ...     f.write(schema_script)
    >>> # Edit schemas/user_data_spark.py to add validation:
    >>> # "user_id": pa.Column(T.LongType(), checks=[pa.Check.greater_than(0)], unique=True),
    >>> # "name": pa.Column(T.StringType(), checks=[pa.Check.str_length_min(1)]),
    >>> # "score": pa.Column(T.DoubleType(), checks=[pa.Check.in_range(0, 100)]),

    Generate schemas for DataFrames with various Spark types:

    >>> from pyspark.sql.types import StructType, StructField, LongType, StringType, BooleanType, TimestampType
    >>> schema = StructType(
    ...     [
    ...         StructField("id", LongType(), False),
    ...         StructField("name", StringType(), False),
    ...         StructField("active", BooleanType(), True),
    ...         StructField("created_at", TimestampType(), True),
    ...     ]
    ... )
    >>> df = spark.createDataFrame([(1, "Alice", True, None)], schema)
    >>> compiler = SparkSchemaScriptCompiler()
    >>> schema_script = compiler.compile_schema_script(df)
    >>> # Schema includes: LongType, StringType, BooleanType, TimestampType

    Use in a distributed data validation workflow:

    >>> def setup_spark_validation(spark_df, dataset_name, output_dir="schemas"):
    ...     compiler = SparkSchemaScriptCompiler()
    ...     script = compiler.compile_schema_script(spark_df)
    ...     output_path = f"{output_dir}/{dataset_name}_spark_schema.py"
    ...     with open(output_path, "w") as f:
    ...         f.write(script)
    ...     print(f"Generated Spark schema template at {output_path}")
    ...     print("Customize with Spark-compatible validation checks.")
    ...     return output_path
    """

    def extract_dataframe_schema(self, data: Data) -> dict[str, str]:
        """
        Extract PySpark DataFrame schema using Spark-native type names.

        This method extracts the schema from a PySpark DataFrame using Spark's
        native type system. It accesses the DataFrame's `schema` attribute and
        extracts Spark type names (e.g., "LongType", "StringType") rather than
        SQL type names (e.g., "bigint", "string").

        The Spark-native format is required because the generated schema code
        uses `pyspark.sql.types` type constructors, which require the native
        type names.

        Parameters
        ----------
        data : Data
            A PySpark DataFrame with a `schema` attribute (StructType). The
            DataFrame can contain any Spark-supported data types including
            primitive types, complex types (arrays, maps, structs), and
            nested structures.

        Returns
        -------
        dict of str to str
            A dictionary mapping column names to Spark-native type names.
            Common type names include:
            - "LongType" for 64-bit integers
            - "IntegerType" for 32-bit integers
            - "ShortType" for 16-bit integers
            - "ByteType" for 8-bit integers
            - "DoubleType" for double-precision floats
            - "FloatType" for single-precision floats
            - "StringType" for strings
            - "BooleanType" for booleans
            - "TimestampType" for timestamps
            - "DateType" for dates
            - "DecimalType(p,s)" for decimal numbers
            - "ArrayType(ElementType)" for arrays
            - "MapType(KeyType,ValueType)" for maps
            - "StructType" for nested structures

        Raises
        ------
        AttributeError
            If the data object does not have a `schema` attribute, indicating
            it is not a PySpark DataFrame.

        See Also
        --------
        compile_schema_string : Uses the extracted schema to generate column definitions.
        adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_schema_spark_native_format : Underlying utility.

        Notes
        -----
        This method delegates to the `extract_dataframe_schema_spark_native_format`
        utility function, which accesses the `schema` attribute (a StructType
        object) from PySpark DataFrames and extracts native type names.

        The native format differs from the SQL format returned by `data.dtypes`:
        - SQL format: [("col", "bigint"), ...] (from data.dtypes)
        - Native format: {"col": "LongType"} (from this method)

        The native format is necessary because generated schema code uses type
        constructors like `T.LongType()` which require the native type names
        from the `pyspark.sql.types` module.

        Complex types (arrays, maps, structs) include their element/key/value
        types in the string representation:
        - Arrays: "ArrayType(StringType())"
        - Maps: "MapType(StringType(), IntegerType())"
        - Structs: "StructType(...)"

        Examples
        --------
        Extract schema from a simple Spark DataFrame:

        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.getOrCreate()
        >>> df = spark.createDataFrame([(1, 10.5, "Alice"), (2, 20.3, "Bob")], ["id", "value", "name"])
        >>> compiler = SparkSchemaScriptCompiler()
        >>> schema = compiler.extract_dataframe_schema(df)
        >>> schema
        {'id': 'LongType', 'value': 'DoubleType', 'name': 'StringType'}

        Extract schema with various Spark types:

        >>> from pyspark.sql.types import StructType, StructField, IntegerType, BooleanType, TimestampType
        >>> schema = StructType(
        ...     [
        ...         StructField("count", IntegerType(), False),
        ...         StructField("active", BooleanType(), True),
        ...         StructField("timestamp", TimestampType(), True),
        ...     ]
        ... )
        >>> df = spark.createDataFrame([(42, True, None)], schema)
        >>> schema = compiler.extract_dataframe_schema(df)
        >>> schema
        {'count': 'IntegerType', 'active': 'BooleanType', 'timestamp': 'TimestampType'}

        Compare with SQL format:

        >>> sql_format = {col: dtype for col, dtype in df.dtypes}
        >>> sql_format
        {'count': 'int', 'active': 'boolean', 'timestamp': 'timestamp'}
        >>> native_format = compiler.extract_dataframe_schema(df)
        >>> native_format
        {'count': 'IntegerType', 'active': 'BooleanType', 'timestamp': 'TimestampType'}

        Extract schema with complex types:

        >>> from pyspark.sql.types import ArrayType, StringType
        >>> schema = StructType([StructField("name", StringType()), StructField("tags", ArrayType(StringType()))])
        >>> df = spark.createDataFrame([("Alice", ["tag1", "tag2"])], schema)
        >>> schema = compiler.extract_dataframe_schema(df)
        >>> schema
        {'name': 'StringType', 'tags': 'ArrayType(StringType())'}
        """
        return extract_dataframe_schema_spark_native_format(data)

    def compile_schema_string(self, df_schema: dict) -> str:
        """
        Compile Spark schema dictionary into Pandera column definition strings.

        This method converts a schema dictionary into formatted Python code
        strings that define Pandera Column objects for PySpark DataFrames. Each
        column is formatted as a Spark-compatible column definition with type
        constructors from `pyspark.sql.types` (aliased as `T`).

        Parameters
        ----------
        df_schema : dict
            A dictionary mapping column names (str) to Spark-native type names
            (str). Type names should be valid Spark type names like "LongType",
            "StringType", "DoubleType", etc.

        Returns
        -------
        str
            A multi-line string containing Pandera column definitions for Spark.
            Each line has the format:
            "\t\"column_name\": pa.Column(T.TypeName(), checks=[]),\\n"

            The string includes proper indentation (one tab), quoted column
            names, type constructor calls with `T.` prefix and `()` parentheses,
            empty checks lists, trailing commas, and newlines.

        See Also
        --------
        extract_dataframe_schema : Generates the input schema dictionary.
        insert_schema_string_to_script : Inserts the result into a script template.

        Notes
        -----
        The generated column definitions use Spark-specific features:
        - Type constructors are called with `T.TypeName()` syntax
        - The `T` alias refers to `pyspark.sql.types` module
        - Parentheses are required to instantiate type objects
        - The format matches pandera.pyspark column syntax

        Column names are quoted with double quotes to handle:
        - Names containing spaces: "column with spaces"
        - Names with special characters: "column-with-dashes"
        - Python keywords: "class", "def", "return"
        - Backtick-escaped names from Spark SQL: "`column.name`"

        Type constructors are generated with the `T.` prefix to reference the
        imported `pyspark.sql.types` module. Complex types may include
        parameters in their string representation.

        Users should customize the generated schemas by adding checks such as:
        - pa.Check.greater_than(0)
        - pa.Check.less_than(100)
        - pa.Check.isin(["cat1", "cat2", "cat3"])
        - pa.Check.str_length_min(1)
        - pa.Check.str_length_max(255)
        - pa.Check(lambda df: custom_spark_validation(df))

        Spark validation checks run distributedly across the cluster, so they
        should be designed for efficient distributed execution. Avoid checks
        that require collecting data to the driver or performing expensive
        cross-partition operations.

        Examples
        --------
        Compile a simple Spark schema dictionary:

        >>> schema_dict = {"id": "LongType", "name": "StringType", "score": "DoubleType"}
        >>> compiler = SparkSchemaScriptCompiler()
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"id": pa.Column(T.LongType(), checks=[]),
        \t"name": pa.Column(T.StringType(), checks=[]),
        \t"score": pa.Column(T.DoubleType(), checks=[]),

        Compile schema with various Spark types:

        >>> schema_dict = {
        ...     "int_col": "IntegerType",
        ...     "bool_col": "BooleanType",
        ...     "timestamp_col": "TimestampType",
        ...     "date_col": "DateType",
        ... }
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"int_col": pa.Column(T.IntegerType(), checks=[]),
        \t"bool_col": pa.Column(T.BooleanType(), checks=[]),
        \t"timestamp_col": pa.Column(T.TimestampType(), checks=[]),
        \t"date_col": pa.Column(T.DateType(), checks=[]),

        Compile schema with special column names:

        >>> schema_dict = {"column with spaces": "LongType", "column-with-dashes": "StringType", "class": "DoubleType"}
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"column with spaces": pa.Column(T.LongType(), checks=[]),
        \t"column-with-dashes": pa.Column(T.StringType(), checks=[]),
        \t"class": pa.Column(T.DoubleType(), checks=[]),

        Compile schema with simple types (note: complex parameterized types
        like ArrayType and MapType require manual adjustment after generation):

        >>> schema_dict = {
        ...     "simple": "StringType",
        ...     "float_col": "FloatType",
        ...     "binary_col": "BinaryType",
        ... }
        >>> schema_string = compiler.compile_schema_string(schema_dict)
        >>> print(schema_string)
        \t"simple": pa.Column(T.StringType(), checks=[]),
        \t"float_col": pa.Column(T.FloatType(), checks=[]),
        \t"binary_col": pa.Column(T.BinaryType(), checks=[]),
        """
        schema_string = ""
        for col_name, col_type in df_schema.items():
            schema_string += f'\t"{col_name}": pa.Column(T.{col_type}(), checks=[]),\n'
        return schema_string

    def insert_schema_string_to_script(self, df_schema_string: str) -> str:
        """
        Insert Spark column definitions into a complete Python script template.

        This method embeds the compiled column definition string into a complete,
        executable Python script that defines a Pandera DataFrameSchema for
        PySpark. The script includes Spark-specific imports, documentation links,
        and helpful comments for customization in a distributed context.

        Parameters
        ----------
        df_schema_string : str
            Multi-line string containing Pandera column definitions for Spark,
            formatted with proper indentation. Typically generated by
            `compile_schema_string`.

        Returns
        -------
        str
            A complete Python script as a string, ready to be saved as a .py
            file. The script includes:
            - Module docstring: "Pandera schema for Spark."
            - Import statements: `pandera.pyspark as pa` and `pyspark.sql.types as T`
            - Instructional comments with example check syntax
            - Documentation link: https://pandera.readthedocs.io/en/stable/pyspark_sql.html
            - DataFrameSchema definition with embedded column definitions
            - Proper Python syntax and formatting

        See Also
        --------
        compile_schema_string : Generates the column definitions to insert.
        compile_schema_script : Orchestrates the full compilation process.

        Notes
        -----
        The generated script is specifically for PySpark DataFrames and uses:
        - `pandera.pyspark` module (aliased as `pa`)
        - `pyspark.sql.types` module (aliased as `T`) for type constructors
        - Spark-compatible type names and check examples
        - Distributed validation considerations

        The instructional comments include:
        - Where to add custom validation checks
        - An example of a simple numeric check (greater_than)
        - A link to Pandera's PySpark documentation

        The script follows this structure:
        1. Module docstring
        2. Import statements (pandera.pyspark and pyspark.sql.types)
        3. Blank line
        4. Instructional comments
        5. Blank line
        6. Schema definition with DataFrameSchema and column dict
        7. Closing parenthesis and newline

        Users should customize the generated schema by:
        - Adding validation checks to the `checks` parameter
        - Setting `nullable=True` or `nullable=False` for columns
        - Adding `coerce=True` to enable type coercion
        - Setting `unique=True` for columns requiring unique values
        - Defining custom validation functions compatible with distributed execution
        - Considering Spark's lazy evaluation and distributed nature

        Important considerations for Spark validation:
        - Checks run distributedly across the Spark cluster
        - Avoid collecting data to driver for validation
        - Use Spark-native operations for efficiency
        - Consider data skew and partition distribution
        - Test validation logic on representative data volumes

        The schema variable is named `schema` to enable easy imports:
        `from schemas.my_spark_schema import schema`

        Examples
        --------
        Generate a complete Spark schema script:

        >>> column_defs = '''\\t"id": pa.Column(T.LongType(), checks=[]),
        ... \\t"name": pa.Column(T.StringType(), checks=[]),
        ... \\t"score": pa.Column(T.DoubleType(), checks=[]),
        ... '''
        >>> compiler = SparkSchemaScriptCompiler()
        >>> script = compiler.insert_schema_string_to_script(column_defs)
        >>> print(script)
        \"\"\"Pandera schema for Spark.\"\"\"
        import pandera.pyspark as pa
        import pyspark.sql.types as T
        <BLANKLINE>
        # Insert your additional checks to `checks` list parameter for each column
        # e.g. checks=[pa.Check.greater_than(0)]
        # refer to https://pandera.readthedocs.io/en/stable/pyspark_sql.html for more details.
        <BLANKLINE>
        schema = pa.DataFrameSchema({
        \t"id": pa.Column(T.LongType(), checks=[]),
        \t"name": pa.Column(T.StringType(), checks=[]),
        \t"score": pa.Column(T.DoubleType(), checks=[]),
        })

        Save and use the generated script:

        >>> script = compiler.insert_schema_string_to_script(column_defs)
        >>> with open("schemas/spark_data.py", "w") as f:
        ...     f.write(script)
        >>> # Customize schemas/spark_data.py with Spark-compatible checks
        >>> # Then import and use:
        >>> from schemas.spark_data import schema
        >>> validated_df = schema.validate(spark_df)

        Example of customized Spark schema after generation:

        >>> # Generated schema (before customization):
        >>> # schema = pa.DataFrameSchema({
        >>> #     "user_id": pa.Column(T.LongType(), checks=[]),
        >>> #     "email": pa.Column(T.StringType(), checks=[]),
        >>> #     "age": pa.Column(T.IntegerType(), checks=[]),
        >>> # })
        >>> #
        >>> # Customized schema (after adding Spark-compatible validation):
        >>> # from pyspark.sql.functions import col
        >>> # schema = pa.DataFrameSchema({
        >>> #     "user_id": pa.Column(
        >>> #         T.LongType(),
        >>> #         checks=[pa.Check.greater_than(0)],
        >>> #         nullable=False,
        >>> #         unique=True
        >>> #     ),
        >>> #     "email": pa.Column(
        >>> #         T.StringType(),
        >>> #         checks=[
        >>> #             pa.Check.str_length_min(5),
        >>> #             pa.Check.str_contains("@")
        >>> #         ],
        >>> #         nullable=False
        >>> #     ),
        >>> #     "age": pa.Column(
        >>> #         T.IntegerType(),
        >>> #         checks=[pa.Check.in_range(0, 120)],
        >>> #         nullable=False,
        >>> #         coerce=True
        >>> #     ),
        >>> # })

        Use in a Spark data pipeline:

        >>> # Generate and save schema
        >>> compiler = SparkSchemaScriptCompiler()
        >>> script = compiler.compile_schema_script(spark_df)
        >>> with open("schemas/pipeline_schema.py", "w") as f:
        ...     f.write(script)
        >>> # After customization, use in pipeline:
        >>> from schemas.pipeline_schema import schema
        >>> def validate_stage(df):
        ...     return schema.validate(df, lazy=True)  # Lazy for better Spark performance
        >>> cleaned_df = extract_data()
        >>> validated_df = validate_stage(cleaned_df)
        >>> transformed_df = transform_data(validated_df)
        """
        schema_script = f'''"""Pandera schema for Spark."""
import pandera.pyspark as pa
import pyspark.sql.types as T

# Insert your additional checks to `checks` list parameter for each column
# e.g. checks=[pa.Check.greater_than(0)]
# refer to https://pandera.readthedocs.io/en/stable/pyspark_sql.html for more details.

schema = pa.DataFrameSchema({{
{df_schema_string}}})
'''
        return schema_script


def determine_compiler(df_type: str) -> SchemaScriptCompiler:
    """
    Select the appropriate schema compiler based on DataFrame framework type.

    This factory function returns the correct SchemaScriptCompiler implementation
    for a given DataFrame framework. It maps framework type strings (e.g., "pandas",
    "pyspark") to their corresponding compiler classes and instantiates the
    appropriate compiler.

    This function implements the Factory pattern, encapsulating the logic for
    compiler selection and instantiation in a single place.

    Parameters
    ----------
    df_type : str
        The DataFrame framework type identifier. Valid values are:
        - "pandas" : For pandas DataFrames
        - "pyspark" : For PySpark DataFrames

        The type string typically comes from
        `extract_dataframe_type(data)` which inspects the data object's
        module name.

    Returns
    -------
    SchemaScriptCompiler
        An instantiated schema compiler appropriate for the specified DataFrame
        type. The returned compiler will be either:
        - PandasSchemaScriptCompiler for "pandas" type
        - SparkSchemaScriptCompiler for "pyspark" type

    Raises
    ------
    ValueError
        If the df_type is not recognized or supported. The error message
        specifies which type was provided and indicates it is not supported.

    See Also
    --------
    compile_type_specific_schema_script : Uses this function to auto-select compiler.
    PandasSchemaScriptCompiler : Compiler for pandas DataFrames.
    SparkSchemaScriptCompiler : Compiler for PySpark DataFrames.
    adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_type : Determines DataFrame type.

    Notes
    -----
    This function uses a dictionary mapping to associate DataFrame types with
    their compiler classes. The mapping currently supports:
    - "pandas" -> PandasSchemaScriptCompiler
    - "pyspark" -> SparkSchemaScriptCompiler

    Adding support for new DataFrame frameworks requires:
    1. Implementing a new SchemaScriptCompiler subclass
    2. Adding the framework type and class to the compiler_dict
    3. Ensuring extract_dataframe_type can identify the new framework

    The function instantiates the compiler class (calling the constructor with
    no arguments), so compiler classes must support zero-argument construction.

    The ValueError is raised before attempting to instantiate a compiler,
    preventing errors from invalid compiler selection.

    Examples
    --------
    Select compiler for pandas:

    >>> compiler = determine_compiler("pandas")
    >>> type(compiler).__name__
    'PandasSchemaScriptCompiler'

    Select compiler for PySpark:

    >>> compiler = determine_compiler("pyspark")
    >>> type(compiler).__name__
    'SparkSchemaScriptCompiler'

    Handle unsupported DataFrame type:

    >>> try:
    ...     compiler = determine_compiler("polars")
    ... except ValueError as e:
    ...     print(e)
    Dataframes of type polars are not supported.

    Use with extracted DataFrame type:

    >>> import pandas as pd
    >>> from adc_toolkit.data.validators.table_utils.table_properties import extract_dataframe_type
    >>> df = pd.DataFrame({"a": [1, 2, 3]})
    >>> df_type = extract_dataframe_type(df)
    >>> df_type
    'pandas'
    >>> compiler = determine_compiler(df_type)
    >>> type(compiler).__name__
    'PandasSchemaScriptCompiler'

    Use in a conditional workflow:

    >>> def get_appropriate_compiler(data):
    ...     df_type = extract_dataframe_type(data)
    ...     try:
    ...         return determine_compiler(df_type)
    ...     except ValueError:
    ...         print(f"Unsupported DataFrame type: {df_type}")
    ...         return None

    Extend with new DataFrame framework:

    >>> # To add support for a new framework:
    >>> # 1. Create a compiler class:
    >>> # class PolarsSchemaScriptCompiler(SchemaScriptCompiler):
    >>> #     ...
    >>> # 2. Update the compiler_dict in determine_compiler:
    >>> # compiler_dict = {
    >>> #     "pandas": PandasSchemaScriptCompiler,
    >>> #     "pyspark": SparkSchemaScriptCompiler,
    >>> #     "polars": PolarsSchemaScriptCompiler,
    >>> # }
    """
    compiler_dict = {
        "pandas": PandasSchemaScriptCompiler,
        "pyspark": SparkSchemaScriptCompiler,
    }
    if df_type not in compiler_dict:
        raise ValueError(f"Dataframes of type {df_type} are not supported.")
    return compiler_dict[df_type]()


def compile_type_specific_schema_script(data: Data) -> str:
    """
    Generate a Pandera schema script from any supported DataFrame type.

    This is the main entry point for automatic schema script generation. It
    inspects the DataFrame to determine its type (pandas or Spark), selects the
    appropriate compiler, and generates a complete Pandera validation schema
    script ready to be saved and customized.

    This function provides a simple, unified interface for schema generation
    that automatically handles framework detection and compiler selection,
    abstracting away the complexity of the compilation process.

    Parameters
    ----------
    data : Data
        A DataFrame object conforming to the Data protocol. Supported types
        include:
        - pandas.DataFrame : Standard pandas DataFrames
        - pyspark.sql.DataFrame : PySpark DataFrames

        The data object must have `columns` and `dtypes` properties as required
        by the Data protocol.

    Returns
    -------
    str
        A complete, executable Python script as a string that defines a Pandera
        DataFrameSchema. The script includes:
        - Module docstring
        - Appropriate import statements (pandas or Spark-specific)
        - Column definitions with correct names and types
        - Empty `checks` lists ready for customization
        - Instructional comments and documentation links

        The script is ready to be written to a .py file and used for validation
        after adding custom validation logic.

    Raises
    ------
    ValueError
        If the DataFrame type is not supported. Currently, only pandas and
        PySpark DataFrames are supported.
    AttributeError
        If the data object does not conform to the Data protocol (missing
        required attributes).

    See Also
    --------
    determine_compiler : Factory function that selects the appropriate compiler.
    PandasSchemaScriptCompiler : Compiler for pandas DataFrames.
    SparkSchemaScriptCompiler : Compiler for PySpark DataFrames.
    adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_type : Determines DataFrame type.

    Notes
    -----
    This function implements a three-step process:
    1. Determine the DataFrame type by inspecting its module
    2. Select the appropriate compiler (pandas or Spark)
    3. Generate the schema script using the compiler

    The function is designed for ease of use and automatically handles the
    complexity of framework detection and compilation. Users don't need to
    know which compiler to use - the function figures it out automatically.

    The generated schema script is a template intended for customization.
    After generation:
    1. Save the script to a Python file in your schemas directory
    2. Add validation checks, nullability constraints, and business rules
    3. Test the schema with representative data
    4. Use the schema with PanderaValidator in your data pipelines

    The function is idempotent: calling it multiple times with the same
    DataFrame will produce the same schema script (assuming the DataFrame
    structure hasn't changed).

    Common workflow:
    1. Load or create a representative DataFrame
    2. Call this function to generate a schema template
    3. Save the template to a file
    4. Customize the template with validation logic
    5. Import and use the schema for ongoing validation

    Performance considerations:
    - Schema extraction is fast for pandas DataFrames
    - For large Spark DataFrames, only the schema metadata is accessed
      (no data is collected to the driver)
    - The function does not validate data, only extracts structure

    Examples
    --------
    Generate a schema script from a pandas DataFrame:

    >>> import pandas as pd
    >>> df = pd.DataFrame(
    ...     {
    ...         "user_id": [1, 2, 3],
    ...         "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
    ...         "age": [25, 30, 35],
    ...     }
    ... )
    >>> schema_script = compile_type_specific_schema_script(df)
    >>> print(schema_script[:50])
    \"\"\"Pandera schema for Pandas.\"\"\"
    import pandera.p

    Save the generated schema to a file:

    >>> schema_script = compile_type_specific_schema_script(df)
    >>> with open("schemas/user_schema.py", "w") as f:
    ...     f.write(schema_script)
    >>> # Now edit schemas/user_schema.py to add validation checks

    Generate a schema script from a PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>> spark_df = spark.createDataFrame([(1, "Alice", 85.5), (2, "Bob", 90.2)], ["id", "name", "score"])
    >>> schema_script = compile_type_specific_schema_script(spark_df)
    >>> print(schema_script[:50])
    \"\"\"Pandera schema for Spark.\"\"\"
    import pandera.py

    Complete workflow for setting up validation:

    >>> import pandas as pd
    >>> from pathlib import Path
    >>>
    >>> # 1. Load a representative sample of your data
    >>> df = pd.read_csv("data/customers.csv")
    >>>
    >>> # 2. Generate schema template
    >>> schema_script = compile_type_specific_schema_script(df)
    >>>
    >>> # 3. Save to schemas directory
    >>> schema_path = Path("schemas/customer_schema.py")
    >>> schema_path.parent.mkdir(exist_ok=True)
    >>> with open(schema_path, "w") as f:
    ...     f.write(schema_script)
    >>>
    >>> # 4. Manually edit schemas/customer_schema.py to add checks:
    >>> # "customer_id": pa.Column("int64", checks=[pa.Check.greater_than(0)], unique=True),
    >>> # "email": pa.Column("object", checks=[pa.Check.str_matches(r"^[^@]+@[^@]+\\.[^@]+$")]),
    >>> # "age": pa.Column("int64", checks=[pa.Check.in_range(18, 120)]),
    >>>
    >>> # 5. Import and use in your pipeline:
    >>> from schemas.customer_schema import schema
    >>> validated_df = schema.validate(df)

    Batch generate schemas for multiple DataFrames:

    >>> dataframes = {"customers": customers_df, "orders": orders_df, "products": products_df}
    >>> for name, df in dataframes.items():
    ...     schema_script = compile_type_specific_schema_script(df)
    ...     with open(f"schemas/{name}_schema.py", "w") as f:
    ...         f.write(schema_script)
    ...     print(f"Generated schema for {name}")

    Handle unsupported DataFrame types:

    >>> try:
    ...     # Hypothetical unsupported DataFrame type
    ...     schema_script = compile_type_specific_schema_script(polars_df)
    ... except ValueError as e:
    ...     print(f"Error: {e}")
    ...     # Fall back to manual schema creation or other approach
    Error: Dataframes of type polars are not supported.

    Use in a schema generation utility:

    >>> def generate_schema_file(data, output_path, overwrite=False):
    ...     \"\"\"Generate and save a Pandera schema template.\"\"\"
    ...     if Path(output_path).exists() and not overwrite:
    ...         raise FileExistsError(f"{output_path} already exists")
    ...
    ...     schema_script = compile_type_specific_schema_script(data)
    ...
    ...     with open(output_path, "w") as f:
    ...         f.write(schema_script)
    ...
    ...     print(f"Schema template saved to {output_path}")
    ...     print("Please customize with validation checks before use.")
    ...     return output_path
    >>>
    >>> generate_schema_file(df, "schemas/new_dataset.py")
    Schema template saved to schemas/new_dataset.py
    Please customize with validation checks before use.
    """
    df_type = extract_dataframe_type(data)
    compiler = determine_compiler(df_type)
    return compiler.compile_schema_script(data)
