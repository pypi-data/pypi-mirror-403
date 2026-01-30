"""
Execute Pandera schema validation scripts.

This module provides the core execution engine for Pandera-based data validation
within the adc-toolkit framework. It orchestrates the dynamic loading of Python
schema modules and the execution of validation logic against data objects.

The module handles the complete validation workflow:

1. Dynamic module construction from schema names and paths
2. Module import/reload for schema definitions
3. Validation execution with configurable error handling
4. Exception wrapping with enhanced error context

The validation system uses a file-based approach where each dataset has a
corresponding Python file containing a Pandera schema definition. These schema
files are organized in a hierarchical directory structure, typically with
schema names in the format "schema.table" mapping to "schema/table.py".

Functions
---------
execute_validation
    Execute validation using a loaded schema module against data.
construct_module_name
    Build a Python module name from table name and schema directory path.
validate_data_with_script_from_path
    Complete validation workflow: load schema module, validate data, handle errors.

See Also
--------
adc_toolkit.data.validators.pandera.validator.PanderaValidator : Main validator
    class that uses these functions to validate data from catalogs.
adc_toolkit.data.validators.pandera.parameters.PanderaParameters : Configuration
    parameters controlling validation behavior.
adc_toolkit.data.validators.pandera.exceptions.PanderaValidationError : Enhanced
    exception raised on validation failures.
pandera.DataFrameSchema : Base Pandera schema class expected in schema modules.

Notes
-----
**Module Loading Mechanism**

The module loading system uses Python's import machinery to dynamically load
schema definitions from Python files. This approach offers several advantages:

- Schemas are defined in Python code, enabling programmatic schema generation
- Full access to Pandera's API for complex validation logic
- Schemas can be version controlled and code reviewed
- Type hints and IDE support for schema definitions
- Ability to share common validation components across schemas

The loading process:

1. Convert table name and directory path to a Python module path
2. Import or reload the module using ``importlib``
3. Extract the ``schema`` attribute from the module
4. Execute ``schema.validate()`` on the data

**Schema File Structure**

Each schema file must define a module-level ``schema`` variable containing
a Pandera ``DataFrameSchema`` or compatible schema object:

.. code-block:: python

    # schemas/customers/users.py
    import pandera as pa

    schema = pa.DataFrameSchema(
        {
            "user_id": pa.Column(int, nullable=False, unique=True),
            "email": pa.Column(str, pa.Check.str_matches(r"^[^@]+@[^@]+$")),
            "age": pa.Column(int, pa.Check.in_range(0, 150), nullable=True),
        }
    )

**Error Handling Strategy**

When validation fails, the module catches Pandera's native exceptions
(``SchemaError`` or ``SchemaErrors``) and wraps them in
``PanderaValidationError``, adding:

- Table name for identification
- Schema file path for debugging
- Original Pandera error details

This enhanced exception format simplifies debugging in data pipelines where
multiple datasets are validated.

Examples
--------
Complete validation workflow for a customer dataset:

>>> from pathlib import Path
>>> import pandas as pd
>>> from adc_toolkit.data.validators.pandera import PanderaParameters
>>>
>>> # Prepare data and configuration
>>> data = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
>>> schema_path = Path("config/pandera_schemas")
>>> params = PanderaParameters(lazy=True)
>>>
>>> # Execute validation (assuming schema file exists at config/pandera_schemas/customer/users.py)
>>> validated_data = validate_data_with_script_from_path(
...     name="customer.users", data=data, path=schema_path, parameters=params
... )

Handling validation errors with enhanced context:

>>> from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
>>>
>>> try:
...     validated = validate_data_with_script_from_path("customer.orders", invalid_data, schema_path, params)
... except PanderaValidationError as e:
...     print(f"Validation failed for {e.table_name}")
...     print(f"Schema location: {e.schema_path}")
...     print(f"Error details: {e.original_error}")

Using individual functions for custom workflows:

>>> # Build module name
>>> module_name = construct_module_name("customer.users", Path("config/pandera_schemas"))
>>> print(module_name)
'config.pandera_schemas.customer.users'
>>>
>>> # Import schema module
>>> from adc_toolkit.utils.manage_modules import import_or_reload_module
>>> schema_module = import_or_reload_module(module_name)
>>>
>>> # Execute validation
>>> validated = execute_validation(schema_module, data, params)
"""

from pathlib import Path
from types import ModuleType

from pandera.errors import SchemaError, SchemaErrors

from adc_toolkit.data.abs import Data
from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
from adc_toolkit.data.validators.pandera.file_manager import FileManager
from adc_toolkit.data.validators.pandera.parameters import PanderaParameters
from adc_toolkit.utils.manage_filesystem import extract_relative_path
from adc_toolkit.utils.manage_modules import import_or_reload_module


def execute_validation(module: ModuleType, data: Data, parameters: PanderaParameters) -> Data:
    """
    Execute Pandera validation using a loaded schema module.

    This function performs the core validation operation by extracting a Pandera
    schema from a dynamically loaded module and executing it against the provided
    data. The validation behavior is controlled by the parameters, particularly
    the lazy flag which determines error collection strategy.

    The function expects the module to contain a module-level attribute named
    ``schema`` that is a Pandera ``DataFrameSchema`` or compatible schema object.
    This schema is then invoked with its ``validate()`` method to check the data
    against the defined constraints.

    Parameters
    ----------
    module : types.ModuleType
        A Python module containing a Pandera schema definition. The module must
        have a ``schema`` attribute that is a Pandera schema object (typically
        ``pandera.DataFrameSchema``). This module is typically loaded dynamically
        using ``importlib.import_module()`` or the toolkit's
        ``import_or_reload_module()`` utility.
    data : Data
        The dataset to validate. Must be a Data protocol-compatible object,
        typically a pandas DataFrame or any object with ``columns`` and ``dtypes``
        properties. The data structure must match the schema definition in the
        module.
    parameters : PanderaParameters
        Configuration parameters controlling validation behavior. The primary
        parameter is ``lazy``, which determines whether to collect all validation
        errors (lazy=True) or fail fast on the first error (lazy=False). This
        parameter is passed directly to Pandera's ``validate()`` method.

    Returns
    -------
    Data
        The validated dataset. If validation succeeds, returns the input data,
        potentially with Pandera metadata attached (depending on Pandera's
        configuration). The returned object is the same type as the input data
        parameter.

    Raises
    ------
    AttributeError
        If the module does not have a ``schema`` attribute. This indicates the
        schema file is malformed or empty.
    pandera.errors.SchemaError
        If validation fails with lazy=False. Contains details about the first
        validation failure encountered, including the failing column, check,
        and observed values.
    pandera.errors.SchemaErrors
        If validation fails with lazy=True. Contains a comprehensive collection
        of all validation failures across all columns and rows, with detailed
        failure cases including row indices and observed values.
    TypeError
        If the data type is incompatible with the schema definition (e.g.,
        trying to validate a Spark DataFrame against a pandas-specific schema).

    See Also
    --------
    validate_data_with_script_from_path : Higher-level function that loads the
        module and handles exception wrapping.
    construct_module_name : Builds module names from table names and paths.
    PanderaParameters : Configuration class for validation behavior.
    pandera.DataFrameSchema.validate : Underlying Pandera validation method.

    Notes
    -----
    **Module Structure Requirements**

    The provided module must define a top-level ``schema`` variable:

    .. code-block:: python

        # Example schema module
        import pandera as pa

        schema = pa.DataFrameSchema(
            {
                "column_name": pa.Column(int, nullable=False),
                # ... more columns
            }
        )

    **Validation Behavior**

    The validation behavior depends on the ``parameters.lazy`` setting:

    - **lazy=True** (default): Pandera collects all validation errors before
      raising. This provides comprehensive error reporting, showing all
      violations in a single validation run. Recommended for production
      pipelines where you want to fix all issues at once.

    - **lazy=False**: Pandera raises immediately on the first validation
      failure. This "fail-fast" mode is useful for debugging or when you
      want to iteratively fix errors one at a time.

    **Return Value Characteristics**

    The returned data object:

    - Is typically the same object instance as the input (validation is
      performed in place)
    - May have Pandera metadata attached if the schema uses ``coerce=True``
      or other transformation features
    - Has the same shape and column structure if validation succeeds
    - Will not be returned if validation fails (an exception is raised instead)

    **Performance Considerations**

    Validation performance depends on:

    - Number of columns and rows in the dataset
    - Complexity of validation checks (regex, custom functions)
    - The lazy parameter (lazy=False may be faster for invalid data)
    - Whether checks can be vectorized by Pandera

    For large datasets, consider:

    - Sampling strategies for expensive checks
    - Profiling to identify slow validation rules
    - Caching schema objects if validating multiple similar datasets

    Examples
    --------
    Basic validation with a schema module:

    >>> import pandas as pd
    >>> import types
    >>> import pandera as pa
    >>> from adc_toolkit.data.validators.pandera import PanderaParameters
    >>>
    >>> # Create a mock schema module
    >>> schema_module = types.ModuleType("mock_schema")
    >>> schema_module.schema = pa.DataFrameSchema(
    ...     {"id": pa.Column(int, nullable=False), "value": pa.Column(float, pa.Check.greater_than(0))}
    ... )
    >>>
    >>> # Valid data
    >>> data = pd.DataFrame({"id": [1, 2, 3], "value": [10.5, 20.3, 30.1]})
    >>> params = PanderaParameters(lazy=True)
    >>> validated = execute_validation(schema_module, data, params)
    >>> validated.equals(data)
    True

    Validation with fail-fast mode (lazy=False):

    >>> params_strict = PanderaParameters(lazy=False)
    >>> invalid_data = pd.DataFrame({"id": [1, 2, None], "value": [10.5, -5.0, 30.1]})
    >>> try:
    ...     execute_validation(schema_module, invalid_data, params_strict)
    ... except pa.errors.SchemaError as e:
    ...     print(f"First error: {e}")  # Will show first validation failure

    Validation with lazy mode to collect all errors:

    >>> params_lazy = PanderaParameters(lazy=True)
    >>> try:
    ...     execute_validation(schema_module, invalid_data, params_lazy)
    ... except pa.errors.SchemaErrors as e:
    ...     print(f"Total failures: {len(e.failure_cases)}")  # Shows all failures
    ...     print(e.failure_cases)  # DataFrame with all validation errors

    Using the function in a validation pipeline:

    >>> from adc_toolkit.utils.manage_modules import import_or_reload_module
    >>>
    >>> # Load schema module dynamically
    >>> module = import_or_reload_module("config.pandera_schemas.customer.users")
    >>>
    >>> # Execute validation
    >>> validated_data = execute_validation(module, user_data, PanderaParameters())
    >>>
    >>> # Continue pipeline with validated data
    >>> process_users(validated_data)
    """
    return module.schema.validate(data, lazy=parameters.lazy)


def construct_module_name(name: str, path: Path) -> str:
    """
    Construct a Python module name from table name and schema directory path.

    This function builds a fully qualified Python module path by combining the
    relative path to the schema directory with the table name. The resulting
    module name can be used with Python's import machinery to dynamically load
    the corresponding schema definition.

    The function handles platform-specific path separators (forward slashes on
    Unix/macOS, backslashes on Windows) and converts them to Python's dot
    notation for module names. This ensures consistent module naming across
    different operating systems.

    The table name is expected to use dot notation for hierarchical organization
    (e.g., "schema.table"), which maps to a directory structure (e.g.,
    "schema/table.py"). Each component of the table name becomes a package or
    module level in the Python import path.

    Parameters
    ----------
    name : str
        Name of the table or dataset, typically in dot notation for hierarchical
        organization. For example, "customer.users" indicates a schema in the
        "customer" namespace for the "users" table. The last component should
        correspond to a Python file name (without the .py extension).

        Common naming conventions:
        - "schema_name.table_name" → maps to schema_name/table_name.py
        - "database.schema.table" → maps to database/schema/table.py
        - "simple_table" → maps to simple_table.py (flat structure)
    path : pathlib.Path
        Path to the root directory where schema scripts are stored. This path
        is converted to a relative path from the project root (determined by
        ``extract_relative_path``), then transformed into Python module notation.

        Examples of valid paths:
        - Path("config/pandera_schemas")
        - Path("/absolute/path/to/schemas")
        - Path("src/adc_toolkit/validators/schemas")

    Returns
    -------
    str
        A fully qualified Python module name that can be passed to
        ``importlib.import_module()`` or similar import functions. The module
        name combines the relative schema directory path and table name,
        separated by dots.

        Format: "{relative_schema_path}.{table_name}"

        Examples:
        - "config.pandera_schemas.customer.users"
        - "src.schemas.database.public.orders"
        - "validations.simple_table"

    See Also
    --------
    validate_data_with_script_from_path : Uses this function to construct module
        names before loading schemas.
    execute_validation : Executes validation with the loaded module.
    adc_toolkit.utils.manage_filesystem.extract_relative_path : Converts absolute
        paths to relative paths from project root.
    adc_toolkit.utils.manage_modules.import_or_reload_module : Imports modules
        using the constructed module names.

    Notes
    -----
    **Path-to-Module Conversion Process**

    The function performs the following transformations:

    1. Extract the relative path from the provided absolute or relative path
       using ``extract_relative_path(path)``
    2. Convert the path to a string representation
    3. Replace forward slashes (/) with dots (.) for Unix/macOS paths
    4. Replace backslashes (\\) with dots (.) for Windows paths
    5. Append the table name using dot notation
    6. Return the complete module path

    **Platform Compatibility**

    The function handles path separators for all platforms:

    - **Unix/macOS**: /path/to/schemas → path.to.schemas
    - **Windows**: \\path\\to\\schemas → path.to.schemas
    - **Mixed** (edge cases): Handles both separator types

    **Module Structure Requirements**

    For the constructed module name to be importable:

    1. Each directory in the path must be a Python package (contains __init__.py)
       or be on ``sys.path``
    2. The final component must be a Python file (.py extension)
    3. The file must be syntactically valid Python code
    4. The file should define a ``schema`` attribute for validation

    **Common Pitfalls**

    - **Missing __init__.py**: If intermediate directories lack __init__.py,
      import may fail on older Python versions (< 3.3) or when not using
      namespace packages
    - **Invalid Python identifiers**: Table names with hyphens or spaces will
      produce invalid module names
    - **Absolute vs relative paths**: The function expects ``extract_relative_path``
      to correctly identify the project root

    Examples
    --------
    Basic usage with a nested table structure:

    >>> from pathlib import Path
    >>> module_name = construct_module_name("customer.users", Path("config/pandera_schemas"))
    >>> print(module_name)
    'config.pandera_schemas.customer.users'

    Single-level table name:

    >>> module_name = construct_module_name("users", Path("schemas"))
    >>> print(module_name)
    'schemas.users'

    Deep nesting with multiple schema levels:

    >>> module_name = construct_module_name("production.public.customer_orders", Path("src/data/validators/pandera"))
    >>> print(module_name)
    'src.data.validators.pandera.production.public.customer_orders'

    Windows path handling (illustrative):

    >>> # On Windows: Path("C:\\Project\\config\\schemas")
    >>> # After extract_relative_path: "config\\schemas"
    >>> # Result: "config.schemas.tablename"
    >>> module_name = construct_module_name("orders", Path("config\\schemas"))
    >>> print(module_name)  # doctest: +SKIP
    'config.schemas.orders'

    Using the constructed name for dynamic import:

    >>> from adc_toolkit.utils.manage_modules import import_or_reload_module
    >>> module_name = construct_module_name("customer.users", Path("config/pandera_schemas"))
    >>> schema_module = import_or_reload_module(module_name)
    >>> # Now schema_module.schema contains the Pandera schema

    Integration with validation workflow:

    >>> from pathlib import Path
    >>> import pandas as pd
    >>> from adc_toolkit.data.validators.pandera import PanderaParameters
    >>> from adc_toolkit.utils.manage_modules import import_or_reload_module
    >>>
    >>> # Construct module name
    >>> table_name = "analytics.daily_reports"
    >>> schema_path = Path("config/validators")
    >>> module_name = construct_module_name(table_name, schema_path)
    >>>
    >>> # Load schema module
    >>> schema_module = import_or_reload_module(module_name)
    >>>
    >>> # Execute validation
    >>> data = pd.DataFrame({"date": ["2024-01-01"], "revenue": [1000.0]})
    >>> validated = execute_validation(schema_module, data, PanderaParameters())
    """
    root_module_path = str(extract_relative_path(path)).replace("/", ".").replace("\\", ".")
    return f"{root_module_path}.{name}"


def validate_data_with_script_from_path(name: str, data: Data, path: Path, parameters: PanderaParameters) -> Data:
    """
    Validate data using a Pandera schema script loaded from a file path.

    This is the primary entry point for file-based Pandera validation in the
    adc-toolkit. It orchestrates the complete validation workflow: constructing
    the module path, dynamically loading the schema module, executing validation,
    and wrapping any validation errors with enhanced debugging context.

    The function combines three key operations:

    1. **Module Construction**: Builds a Python module name from the table name
       and schema directory path using ``construct_module_name()``.
    2. **Module Loading**: Dynamically imports (or reloads) the schema module
       using Python's import machinery via ``import_or_reload_module()``.
    3. **Validation Execution**: Runs the schema's validation logic against the
       data using ``execute_validation()``.

    If validation fails, the function catches Pandera's native exceptions and
    wraps them in ``PanderaValidationError``, adding table name and schema file
    path for easier debugging in data pipelines with multiple datasets.

    Parameters
    ----------
    name : str
        Name of the table or dataset to validate, typically in dot notation for
        hierarchical organization (e.g., "customer.users", "analytics.reports").
        This name determines which schema file is loaded. The naming convention
        typically maps to a file structure where "schema.table" corresponds to
        "schema/table.py" in the schema directory.

        The name must match a schema file that exists in the directory specified
        by the ``path`` parameter.
    data : Data
        The dataset to validate. Must be a Data protocol-compatible object,
        typically a pandas DataFrame or any object with ``columns`` and ``dtypes``
        properties. The data structure must be compatible with the schema
        definition in the loaded module.

        The data is passed to the schema's ``validate()`` method and must match
        the expected schema structure (column names, types, constraints).
    path : pathlib.Path
        Path to the root directory containing Pandera schema scripts. This
        directory should contain Python files organized in a structure that
        matches the table naming convention. For example, if validating
        "customer.users", the directory should contain "customer/users.py".

        The path can be absolute or relative. It will be converted to a Python
        module path using ``extract_relative_path()`` for dynamic imports.

        Common examples:
        - Path("config/pandera_schemas")
        - Path("src/adc_toolkit/validators/schemas")
        - Path("/absolute/path/to/schemas")
    parameters : PanderaParameters
        Configuration parameters controlling validation behavior. The primary
        setting is the ``lazy`` flag:

        - **lazy=True** (default): Collect all validation errors before raising,
          providing comprehensive error reporting.
        - **lazy=False**: Fail immediately on the first validation error,
          useful for debugging.

        These parameters are passed to Pandera's ``validate()`` method.

    Returns
    -------
    Data
        The validated dataset. If validation succeeds, returns the input data,
        potentially with Pandera metadata attached. The returned object is the
        same type as the input data parameter.

        The data is guaranteed to satisfy all validation rules defined in the
        schema. Any data returned from this function has passed all checks for:
        - Column names and types
        - Nullability constraints
        - Value range and pattern checks
        - Custom validation logic
        - Cross-column dependencies

    Raises
    ------
    PanderaValidationError
        If validation fails. This exception wraps Pandera's native
        ``SchemaError`` or ``SchemaErrors`` and enriches them with:

        - **table_name**: The name parameter, identifying which dataset failed
        - **schema_path**: Full path to the schema file that was used
        - **original_error**: The underlying Pandera exception with detailed
          failure information

        The enhanced error message includes all three pieces of information,
        making it easy to identify and debug validation failures in complex
        data pipelines.

        Examples of validation failures:
        - Missing required columns
        - Type mismatches (e.g., string in numeric column)
        - Constraint violations (e.g., negative values, regex mismatches)
        - Null values in non-nullable columns
        - Failed custom validation checks
    ModuleNotFoundError
        If the schema file does not exist at the expected location. This
        indicates the table name doesn't match any schema file, or the schema
        directory structure is incorrect.

        The module path is constructed as:
        "{relative_path}.{name}" → "path/to/schemas/schema_name/table_name.py"
    AttributeError
        If the loaded schema module does not have a ``schema`` attribute. This
        indicates the schema file is malformed or doesn't define the required
        schema object.
    ImportError
        If the schema module cannot be imported due to syntax errors or missing
        dependencies. This indicates the schema file contains invalid Python
        code or imports unavailable packages.
    TypeError
        If the data type is incompatible with the schema definition (e.g.,
        trying to validate a Spark DataFrame against a pandas-specific schema).

    See Also
    --------
    execute_validation : Core validation function that runs the schema.
    construct_module_name : Builds module names from table names and paths.
    PanderaValidator : High-level validator class that uses this function.
    PanderaParameters : Configuration for validation behavior.
    PanderaValidationError : Enhanced exception raised on failures.
    pandera.DataFrameSchema : Pandera's schema class used in schema files.

    Notes
    -----
    **File Structure and Naming Convention**

    The function expects a specific file structure where table names map to
    file paths using dot notation:

    .. code-block:: text

        path/
        ├── customer/
        │   ├── __init__.py
        │   ├── users.py        # Schema for "customer.users"
        │   └── orders.py       # Schema for "customer.orders"
        └── analytics/
            ├── __init__.py
            └── reports.py      # Schema for "analytics.reports"

    Each schema file must define a module-level ``schema`` variable:

    .. code-block:: python

        # customer/users.py
        import pandera as pa

        schema = pa.DataFrameSchema(
            {
                "user_id": pa.Column(int, nullable=False, unique=True),
                "email": pa.Column(str, pa.Check.str_matches(r"^[^@]+@[^@]+$")),
                "created_at": pa.Column("datetime64[ns]"),
            }
        )

    **Dynamic Module Loading**

    The function uses ``import_or_reload_module()`` which:

    - Imports the module if not already loaded
    - Reloads the module if it's already in ``sys.modules``
    - Enables hot-reloading of schema definitions during development
    - Ensures you always get the latest schema version

    This is particularly useful when iterating on schema definitions, as you
    don't need to restart your Python process to pick up changes.

    **Error Handling and Debugging**

    When validation fails, the enhanced error includes:

    1. **Table Name**: Identifies which dataset failed in multi-dataset pipelines
    2. **Schema Path**: Direct link to the schema file for quick navigation
    3. **Original Error**: Complete Pandera error details including:
       - Failing columns and checks
       - Row indices where failures occurred
       - Expected vs actual values
       - Failure counts and percentages

    Example error output:

    .. code-block:: text

        PanderaValidationError: Validation failed for table 'customer.users'
        Schema file: /project/config/pandera_schemas/customer/users.py
        Error details:
        Schema error in column 'age':
        - Check 'greater_than_or_equal_to(0)' failed for 15 rows
        - First failure at row 42: value -5 is not >= 0

    **Performance Characteristics**

    Validation performance depends on several factors:

    - **Module Loading**: First load imports the module; subsequent calls
      reload if already imported. Module caching reduces overhead.
    - **Validation Complexity**: Simple type checks are fast; regex and
      custom functions are slower.
    - **Dataset Size**: Validation time scales linearly with row count for
      most checks.
    - **Lazy vs Eager**: ``lazy=False`` may be faster for invalid data as it
      stops at the first error.

    For large-scale production use:

    - Consider sampling strategies for expensive checks
    - Profile validation to identify bottlenecks
    - Use vectorized Pandera checks when possible
    - Cache schema modules to avoid repeated reloads

    **Integration with ValidatedDataCatalog**

    This function is typically called by ``PanderaValidator`` as part of the
    validated data catalog workflow:

    .. code-block:: python

        catalog = ValidatedDataCatalog.in_directory(
            catalog_path="config/catalog",
            validator=PanderaValidator(config_path="config/pandera_schemas", parameters=PanderaParameters(lazy=True)),
        )

        # Validation happens automatically during load/save
        data = catalog.load("customer.users")  # Validated on load
        catalog.save("customer.users", data)  # Validated on save

    Examples
    --------
    Basic validation workflow:

    >>> from pathlib import Path
    >>> import pandas as pd
    >>> from adc_toolkit.data.validators.pandera import PanderaParameters
    >>>
    >>> # Prepare data
    >>> data = pd.DataFrame(
    ...     {
    ...         "user_id": [1, 2, 3],
    ...         "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
    ...         "age": [25, 30, 35],
    ...     }
    ... )
    >>>
    >>> # Validate with default lazy mode
    >>> validated = validate_data_with_script_from_path(
    ...     name="customer.users", data=data, path=Path("config/pandera_schemas"), parameters=PanderaParameters()
    ... )
    >>> print("Validation successful!")

    Handling validation errors with detailed debugging:

    >>> from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
    >>>
    >>> invalid_data = pd.DataFrame(
    ...     {
    ...         "user_id": [1, 2, None],  # None violates non-nullable constraint
    ...         "email": ["alice@example.com", "invalid-email", "charlie@example.com"],  # Invalid format
    ...         "age": [25, -5, 35],  # Negative age violates constraint
    ...     }
    ... )
    >>>
    >>> try:
    ...     validated = validate_data_with_script_from_path(
    ...         name="customer.users",
    ...         data=invalid_data,
    ...         path=Path("config/pandera_schemas"),
    ...         parameters=PanderaParameters(lazy=True),  # Collect all errors
    ...     )
    ... except PanderaValidationError as e:
    ...     print(f"Validation failed for: {e.table_name}")
    ...     print(f"Schema location: {e.schema_path}")
    ...     print(f"\\nDetailed errors:")
    ...     print(e.original_error)
    ...     # Log to monitoring system, send alerts, etc.

    Fail-fast mode for debugging:

    >>> try:
    ...     validated = validate_data_with_script_from_path(
    ...         name="customer.users",
    ...         data=invalid_data,
    ...         path=Path("config/pandera_schemas"),
    ...         parameters=PanderaParameters(lazy=False),  # Stop at first error
    ...     )
    ... except PanderaValidationError as e:
    ...     print(f"First error encountered: {e.original_error}")
    ...     # Fix this error, then re-run to find the next one

    Production pipeline with comprehensive error handling:

    >>> from pathlib import Path
    >>> import logging
    >>> from adc_toolkit.data.validators.pandera import PanderaParameters, PanderaValidationError
    >>>
    >>> logger = logging.getLogger(__name__)
    >>> schema_path = Path("config/pandera_schemas")
    >>> params = PanderaParameters(lazy=True)
    >>>
    >>> def process_table(table_name: str, data: pd.DataFrame) -> pd.DataFrame:
    ...     try:
    ...         validated = validate_data_with_script_from_path(
    ...             name=table_name, data=data, path=schema_path, parameters=params
    ...         )
    ...         logger.info(f"Validation passed for {table_name}")
    ...         return validated
    ...     except PanderaValidationError as e:
    ...         logger.error(f"Validation failed for {e.table_name}: {e}")
    ...         # Send alert to monitoring system
    ...         alert_system.send(f"Data quality issue in {e.table_name}", severity="HIGH")
    ...         # Re-raise or handle gracefully
    ...         raise
    ...     except ModuleNotFoundError:
    ...         logger.error(f"Schema not found for {table_name}")
    ...         raise ValueError(f"No validation schema configured for {table_name}")

    Multiple datasets in a batch pipeline:

    >>> datasets = ["customer.users", "customer.orders", "analytics.reports"]
    >>> validated_data = {}
    >>>
    >>> for table_name in datasets:
    ...     raw_data = load_raw_data(table_name)  # Your data loading logic
    ...     try:
    ...         validated_data[table_name] = validate_data_with_script_from_path(
    ...             name=table_name,
    ...             data=raw_data,
    ...             path=Path("config/pandera_schemas"),
    ...             parameters=PanderaParameters(lazy=True),
    ...         )
    ...         print(f"✓ {table_name} validated successfully")
    ...     except PanderaValidationError as e:
    ...         print(f"✗ {table_name} validation failed")
    ...         # Log details and continue with other datasets
    ...         log_validation_failure(e)

    Integration with testing frameworks:

    >>> import pytest
    >>> from pathlib import Path
    >>>
    >>> def test_customer_users_validation():
    ...     # Arrange
    ...     test_data = pd.DataFrame({"user_id": [1, 2], "email": ["a@b.com", "c@d.com"], "age": [25, 30]})
    ...
    ...     # Act
    ...     validated = validate_data_with_script_from_path(
    ...         name="customer.users",
    ...         data=test_data,
    ...         path=Path("tests/fixtures/schemas"),
    ...         parameters=PanderaParameters(),
    ...     )
    ...
    ...     # Assert
    ...     assert validated.equals(test_data)
    ...     assert len(validated) == 2
    """
    module_name = construct_module_name(name, path)
    module = import_or_reload_module(module_name)
    try:
        return execute_validation(module, data, parameters)
    except (SchemaError, SchemaErrors) as e:
        schema_path = FileManager(name, path).create_full_path()
        raise PanderaValidationError(
            table_name=name,
            schema_path=schema_path,
            original_error=e,
        ) from e
