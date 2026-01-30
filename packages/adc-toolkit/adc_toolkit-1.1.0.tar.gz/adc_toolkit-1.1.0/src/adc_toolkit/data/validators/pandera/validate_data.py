"""
Pandera data validation orchestration module.

This module provides the high-level orchestration functions for Pandera-based
data validation within the adc-toolkit framework. It coordinates the entire
validation workflow, from automatic schema generation to data validation
execution, ensuring seamless integration between schema compilation, file
management, and validation execution components.

The module implements a two-phase validation approach:

1. **Schema Compilation Phase** (via ``create_schema_script_if_not_exists``):
   Automatically generates Pandera schema scripts from data structure if they
   don't already exist. Generated schemas serve as editable templates that
   users can customize with additional validation rules.

2. **Validation Execution Phase** (via ``validate_data``): Loads the schema
   script, executes validation against the provided data, and returns the
   validated result or raises detailed validation errors.

The orchestration functions coordinate interactions between:

- **FileManager**: Manages schema script file I/O and directory structures
- **Schema Compilers**: Generate type-specific schema scripts (Pandas/Spark)
- **Schema Executors**: Load and execute schema scripts for validation
- **PanderaParameters**: Control validation behavior (lazy vs. fail-fast)

This design enables a smooth developer experience where schemas are
automatically created on first use, can be manually refined with custom
validation rules, and are then reused for all subsequent validations of
that dataset.

See Also
--------
compile_schema_script : Schema script generation from data structures.
execute_schema_script : Schema script loading and validation execution.
file_manager.FileManager : File system operations for schema scripts.
parameters.PanderaParameters : Validation configuration parameters.

Notes
-----
The validation workflow follows this sequence:

1. User calls ``validate_data(name, data, config_path, parameters)``
2. Function checks if schema script exists for the dataset name
3. If missing, auto-generates schema from data structure and saves to file
4. Loads schema script as a Python module
5. Executes validation using Pandera's DataFrameSchema.validate()
6. Returns validated data or raises PanderaValidationError with context

Schema scripts are organized in a hierarchical directory structure based on
dataset names. For example, a dataset named "raw.customers" generates a schema
at ``{config_path}/raw/customers.py``.

Examples
--------
Basic validation workflow with auto-generated schema:

>>> from pathlib import Path
>>> import pandas as pd
>>> from adc_toolkit.data.validators.pandera import validate_data, PanderaParameters
>>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
>>> params = PanderaParameters(lazy=True)
>>> validated_df = validate_data(
...     name="raw.customers", data=df, config_path=Path("config/validators"), parameters=params
... )

Manual schema customization after first run:

>>> # First validation auto-generates schema at config/validators/raw/customers.py
>>> validate_data("raw.customers", df, Path("config/validators"), params)
>>> # Edit config/validators/raw/customers.py to add custom checks
>>> # Subsequent validations use the customized schema
>>> validate_data("raw.customers", df, Path("config/validators"), params)

Integration with ValidatedDataCatalog:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> catalog = ValidatedDataCatalog.in_directory("config")
>>> # Internally uses validate_data for all load/save operations
>>> df = catalog.load("raw.customers")  # Validates after loading
"""

from pathlib import Path

from adc_toolkit.data.abs import Data
from adc_toolkit.data.validators.pandera.compile_schema_script import compile_type_specific_schema_script
from adc_toolkit.data.validators.pandera.execute_schema_script import validate_data_with_script_from_path
from adc_toolkit.data.validators.pandera.file_manager import FileManager
from adc_toolkit.data.validators.pandera.parameters import PanderaParameters


def create_schema_script_if_not_exists(name: str, data: Data, config_path: Path) -> None:
    """
    Create Pandera schema script file if it does not already exist.

    This function implements the schema auto-generation feature of the Pandera
    validation workflow. It checks whether a schema script exists for the given
    dataset name, and if not, automatically generates one by introspecting the
    data structure. The generated schema serves as an editable template that
    users can customize with additional validation rules and constraints.

    The function orchestrates three main operations:

    1. **File Existence Check**: Uses FileManager to determine if a schema
       script already exists at the expected path for this dataset.
    2. **Schema Compilation**: If the schema is missing, invokes the
       type-specific schema compiler to generate a Python script containing
       a Pandera DataFrameSchema based on the data's column names and types.
    3. **File Persistence**: Writes the compiled schema script to the
       appropriate location in the configuration directory hierarchy.

    Schema scripts are organized hierarchically based on dataset names. For
    example, a dataset named "raw.customers" creates a schema script at
    ``{config_path}/raw/customers.py``. This organization mirrors typical data
    lake or data warehouse naming conventions (e.g., database.table).

    The generated schema includes:

    - Import statements for Pandera and required type libraries
    - Column definitions with inferred data types
    - Empty checks lists for each column (ready for user customization)
    - Helpful comments explaining how to add custom validation rules
    - Links to Pandera documentation for reference

    This function is idempotent: calling it multiple times with the same
    dataset name has no effect after the initial schema creation, preserving
    any manual edits users have made to the schema file.

    Parameters
    ----------
    name : str
        The dataset name/identifier used to determine schema file location.
        Should follow the convention "category.dataset_name" (e.g.,
        "raw.customers", "processed.sales"). The name is split on the first
        dot to create the directory structure: category becomes a subdirectory,
        and dataset_name becomes the filename with .py extension.
    data : Data
        The data object (pandas DataFrame, PySpark DataFrame, etc.) from which
        to infer the schema structure. Must be a protocol-compliant Data object
        with `columns` and `dtypes` attributes. The data's type (pandas vs.
        spark) determines which schema compiler is used.
    config_path : Path
        The root directory path where schema scripts are stored. Schema files
        are organized in subdirectories under this path. For example, if
        config_path is ``Path("config/validators")``, a dataset named
        "raw.customers" creates a schema at
        ``config/validators/raw/customers.py``.

    Returns
    -------
    None
        This function returns nothing. It has the side effect of creating a
        schema script file on disk if one does not already exist.

    Raises
    ------
    ValueError
        If the dataframe type is not supported (neither pandas nor pyspark),
        raised by the schema compiler when attempting to determine which
        compiler to use.
    OSError
        If there are file system permissions issues preventing directory
        creation or file writing operations.
    TypeError
        If the data object does not conform to the Data protocol (missing
        required attributes like columns or dtypes).

    See Also
    --------
    compile_type_specific_schema_script : Generates schema script from data structure.
    FileManager : Manages file operations and path construction.
    validate_data : High-level validation function that calls this function.
    execute_schema_script.validate_data_with_script_from_path : Executes validation
        using the generated or existing schema script.

    Notes
    -----
    **Design Rationale**

    The auto-generation approach balances automation with flexibility:

    - **First-Run Automation**: Eliminates manual schema writing for initial
      validation, reducing setup friction and enabling rapid prototyping.
    - **User Customization**: Generated schemas are human-readable Python files
      that users can edit to add domain-specific validation rules, custom checks,
      and constraints that cannot be inferred from data types alone.
    - **Version Control Friendly**: Schema scripts are plain Python files that
      can be committed to version control, enabling schema evolution tracking
      and team collaboration.

    **Directory Structure**

    The hierarchical organization based on dataset names supports large projects
    with many datasets. For example:

    .. code-block:: text

        config/validators/
        ├── raw/
        │   ├── customers.py
        │   ├── orders.py
        │   └── products.py
        ├── processed/
        │   ├── customer_features.py
        │   └── order_aggregates.py
        └── final/
            └── model_input.py

    **Thread Safety**

    This function is not thread-safe. If multiple threads or processes attempt
    to create the same schema file simultaneously, race conditions may occur.
    For concurrent scenarios, implement external locking mechanisms.

    **Idempotency**

    The function is idempotent with respect to file creation: after the initial
    schema generation, subsequent calls do nothing, even if the data structure
    has changed. To regenerate a schema, manually delete the existing schema
    file first.

    Examples
    --------
    Basic usage with pandas DataFrame:

    >>> import pandas as pd
    >>> from pathlib import Path
    >>> from adc_toolkit.data.validators.pandera import create_schema_script_if_not_exists
    >>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]})
    >>> create_schema_script_if_not_exists(name="raw.customers", data=df, config_path=Path("config/validators"))
    >>> # Schema script created at: config/validators/raw/customers.py
    >>> # The file contains a DataFrameSchema with columns: id, name, age

    Generated schema script content (example):

    .. code-block:: python

        # config/validators/raw/customers.py
        import pandera.pandas as pa

        # Insert your additional checks to `checks` list parameter for each column
        # e.g. checks=[pa.Check(lambda s: s.str.len() > 0, element_wise=True)]
        # refer to https://pandera.readthedocs.io/en/stable/checks.html

        schema = pa.DataFrameSchema(
            {
                "id": pa.Column("int64", checks=[]),
                "name": pa.Column("object", checks=[]),
                "age": pa.Column("int64", checks=[]),
            }
        )

    Idempotency demonstration:

    >>> # First call creates the schema
    >>> create_schema_script_if_not_exists("raw.customers", df, Path("config/validators"))
    >>> # Subsequent calls have no effect (preserves manual edits)
    >>> create_schema_script_if_not_exists("raw.customers", df, Path("config/validators"))
    >>> # Manual edits to config/validators/raw/customers.py are preserved

    Using with PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>> spark_df = spark.createDataFrame([(1, "Alice", 25), (2, "Bob", 30)], ["id", "name", "age"])
    >>> create_schema_script_if_not_exists(
    ...     name="raw.spark_customers", data=spark_df, config_path=Path("config/validators")
    ... )
    >>> # Generates a PySpark-compatible schema with pyspark.sql.types imports
    """
    file_manager = FileManager(name, config_path)

    if not file_manager.check_if_file_exists():
        file_manager.create_directory_and_empty_file()
        schema_script = compile_type_specific_schema_script(data)
        file_manager.write_file(schema_script)


def validate_data(name: str, data: Data, config_path: Path, parameters: PanderaParameters) -> Data:
    """
    Validate data using Pandera schema with automatic schema generation.

    This is the primary entry point for Pandera-based data validation in the
    adc-toolkit framework. It orchestrates the complete validation workflow,
    from automatic schema generation (if needed) to validation execution,
    providing a seamless developer experience that combines convenience with
    comprehensive data quality checking.

    The function implements a two-phase validation approach:

    **Phase 1: Schema Preparation**
        Ensures a schema script exists for the dataset by calling
        ``create_schema_script_if_not_exists``. On first use with a new dataset,
        this auto-generates a schema file based on the data structure. On
        subsequent uses, it detects the existing schema and skips generation,
        preserving any manual customizations.

    **Phase 2: Validation Execution**
        Loads the schema script as a Python module and executes validation
        against the provided data using Pandera's DataFrameSchema.validate()
        method. Returns the validated data if all checks pass, or raises a
        detailed PanderaValidationError if validation fails.

    This design enables an iterative workflow where developers can:

    1. Run validation immediately without manual schema creation
    2. Review auto-generated schemas and add custom validation rules
    3. Commit schemas to version control for team collaboration
    4. Evolve schemas over time as data requirements change

    The function integrates with the ValidatedDataCatalog to provide automatic
    validation on all data load and save operations, ensuring data quality
    throughout the entire data pipeline.

    Parameters
    ----------
    name : str
        The dataset name/identifier that determines which schema script to use.
        Should follow the convention "category.dataset_name" (e.g.,
        "raw.customers", "processed.sales"). The name is used to:

        - Locate or create the schema script file
        - Construct the module import path for schema loading
        - Provide context in validation error messages

        Names with a single dot separator (e.g., "raw.customers") create a
        two-level directory structure: ``{config_path}/raw/customers.py``.
    data : Data
        The data object to validate. Must be a protocol-compliant Data object
        (pandas DataFrame, PySpark DataFrame, etc.) with `columns` and `dtypes`
        attributes. The data is validated against the schema defined in the
        corresponding schema script. If validation passes, the original data
        object is returned (potentially with Pandera-applied type coercions
        depending on schema configuration).
    config_path : Path
        The root directory path where schema scripts are stored and loaded from.
        This directory should contain subdirectories for each dataset category,
        with schema scripts organized within them. For example:

        .. code-block:: text

            config_path/
            ├── raw/
            │   ├── customers.py
            │   └── orders.py
            └── processed/
                └── features.py

        The path can be absolute or relative to the current working directory.
    parameters : PanderaParameters
        Configuration parameters controlling validation behavior. The primary
        parameter is `lazy`, which determines error collection strategy:

        - ``PanderaParameters(lazy=True)`` (recommended): Collects all
          validation errors across the entire dataset before raising an
          exception, providing comprehensive error reporting.
        - ``PanderaParameters(lazy=False)``: Raises an exception immediately
          upon encountering the first validation failure, useful for debugging.

    Returns
    -------
    Data
        The validated data object. If validation passes all checks defined in
        the schema, returns the original data object (potentially with
        Pandera-applied type coercions if configured in the schema). The
        return type matches the input data type (pandas DataFrame returns
        pandas DataFrame, PySpark DataFrame returns PySpark DataFrame).

    Raises
    ------
    PanderaValidationError
        Raised when data validation fails against the schema. This custom
        exception wraps the underlying Pandera SchemaError or SchemaErrors
        and enriches it with additional context:

        - ``table_name``: The dataset name that failed validation
        - ``schema_path``: Full filesystem path to the schema script file
        - ``original_error``: The underlying Pandera error with detailed
          validation failure information

        The exception message includes all validation errors (when lazy=True)
        or the first error (when lazy=False), along with row indices and
        column names where failures occurred.
    ValueError
        Raised if the dataframe type is not supported (neither pandas nor
        pyspark), originating from the schema compiler during auto-generation.
    ModuleNotFoundError
        Raised if the schema script cannot be imported, typically indicating
        a Python syntax error in a manually edited schema file.
    AttributeError
        Raised if the schema script module does not define a `schema` attribute,
        indicating the schema file structure is invalid.
    OSError
        Raised if there are file system permissions issues preventing schema
        file creation or reading operations.

    See Also
    --------
    create_schema_script_if_not_exists : Creates schema script if missing.
    validate_data_with_script_from_path : Executes validation from schema script.
    PanderaParameters : Configuration parameters for validation behavior.
    PanderaValidationError : Custom exception raised on validation failure.
    PanderaValidator : Validator class that uses this function internally.
    ValidatedDataCatalog : Data catalog with integrated validation using this function.

    Notes
    -----
    **Validation Workflow**

    The complete validation sequence executed by this function:

    1. Check if schema file exists at ``{config_path}/{category}/{dataset}.py``
    2. If missing, auto-generate schema by introspecting data structure
    3. Load schema file as a Python module using dynamic import
    4. Extract the ``schema`` DataFrameSchema object from the module
    5. Call ``schema.validate(data, lazy=parameters.lazy)``
    6. Return validated data if all checks pass
    7. Raise PanderaValidationError with context if validation fails

    **Schema Customization**

    After first run, edit the generated schema file to add custom validation
    rules:

    .. code-block:: python

        # config/validators/raw/customers.py
        import pandera.pandas as pa

        schema = pa.DataFrameSchema(
            {
                "id": pa.Column(
                    "int64",
                    checks=[
                        pa.Check.greater_than(0),  # Custom: IDs must be positive
                    ],
                ),
                "email": pa.Column(
                    "object",
                    checks=[
                        pa.Check(lambda s: s.str.contains("@"), element_wise=True),  # Custom: valid email
                    ],
                ),
                "age": pa.Column(
                    "int64",
                    checks=[
                        pa.Check.in_range(0, 120),  # Custom: realistic age range
                    ],
                ),
            }
        )

    **Performance Considerations**

    - Schema files are dynamically imported on each validation call. For
      high-frequency validation scenarios, consider caching validator instances.
    - The ``lazy=True`` mode has slightly more overhead as it collects all
      errors, but provides significantly better developer experience.
    - Auto-generation only occurs once per dataset, so performance impact is
      negligible after initial schema creation.

    **Integration with ValidatedDataCatalog**

    This function is the validation backend for ValidatedDataCatalog:

    .. code-block:: python

        # ValidatedDataCatalog internally calls validate_data
        catalog = ValidatedDataCatalog.in_directory("config")
        df = catalog.load("raw.customers")  # Validates after loading
        catalog.save("processed.customers", df)  # Validates before saving

    **Thread Safety**

    This function is thread-safe for validation operations on existing schemas.
    However, the initial schema auto-generation (via
    ``create_schema_script_if_not_exists``) is not thread-safe. For concurrent
    first-time validation of the same dataset, implement external locking.

    Examples
    --------
    Basic validation with auto-generated schema:

    >>> import pandas as pd
    >>> from pathlib import Path
    >>> from adc_toolkit.data.validators.pandera import validate_data, PanderaParameters
    >>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]})
    >>> params = PanderaParameters(lazy=True)
    >>> validated_df = validate_data(
    ...     name="raw.customers", data=df, config_path=Path("config/validators"), parameters=params
    ... )
    >>> # First run: auto-generates schema at config/validators/raw/customers.py
    >>> # Subsequent runs: uses existing schema
    >>> print(validated_df)
       id     name  age
    0   1    Alice   25
    1   2      Bob   30
    2   3  Charlie   35

    Validation failure with comprehensive error reporting (lazy=True):

    >>> df_invalid = pd.DataFrame(
    ...     {
    ...         "id": [1, -2, 3],  # Invalid: negative ID
    ...         "name": ["Alice", "Bob", None],  # Invalid: null name
    ...         "age": [25, 30, 150],  # Invalid: unrealistic age (after custom check added)
    ...     }
    ... )
    >>> from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
    >>> try:
    ...     validate_data("raw.customers", df_invalid, Path("config/validators"), params)
    ... except PanderaValidationError as e:
    ...     print(f"Validation failed: {type(e).__name__}")
    ...     print(f"Schema file: {e.schema_path}")
    ...     # All validation errors are reported together

    Fail-fast validation for debugging (lazy=False):

    >>> params_strict = PanderaParameters(lazy=False)
    >>> try:
    ...     validate_data("raw.customers", df_invalid, Path("config/validators"), params_strict)
    ... except PanderaValidationError as e:
    ...     print(f"First error: {type(e).__name__}")
    ...     # Only the first validation error is reported

    Validation after schema customization:

    >>> # After editing config/validators/raw/customers.py to add custom checks:
    >>> # schema = pa.DataFrameSchema({
    >>> #     "id": pa.Column("int64", checks=[pa.Check.greater_than(0)]),
    >>> #     "age": pa.Column("int64", checks=[pa.Check.in_range(0, 120)]),
    >>> # })
    >>> validated_df = validate_data("raw.customers", df, Path("config/validators"), params)
    >>> # Validation now includes custom checks

    Using with PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>> spark_df = spark.createDataFrame([(1, "Alice", 25), (2, "Bob", 30)], ["id", "name", "age"])
    >>> validated_spark_df = validate_data(
    ...     name="raw.spark_customers", data=spark_df, config_path=Path("config/validators"), parameters=params
    ... )
    >>> # Returns validated PySpark DataFrame

    Integration with data pipeline:

    >>> def process_customer_data():
    ...     # Load raw data
    ...     raw_df = load_raw_customers()
    ...
    ...     # Validate input
    ...     validated_input = validate_data(
    ...         "raw.customers", raw_df, Path("config/validators"), PanderaParameters(lazy=True)
    ...     )
    ...
    ...     # Process data
    ...     processed_df = transform_customers(validated_input)
    ...
    ...     # Validate output
    ...     validated_output = validate_data(
    ...         "processed.customers", processed_df, Path("config/validators"), PanderaParameters(lazy=True)
    ...     )
    ...
    ...     return validated_output
    """
    create_schema_script_if_not_exists(name, data, config_path)
    return validate_data_with_script_from_path(name, data, config_path, parameters)
