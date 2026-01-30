"""
Pandera-based data validation implementation.

This module provides the PanderaValidator class, a concrete implementation of
the DataValidator protocol that uses Pandera for schema-based data validation.
Pandera is a lightweight statistical data validation library with tight pandas
integration and support for both pandas and PySpark DataFrames.

The validator implements an automatic schema generation workflow where schemas
are created on first use by introspecting data structure, then can be manually
customized with domain-specific validation rules. Schema scripts are stored as
editable Python files, enabling version control and team collaboration.

See Also
--------
adc_toolkit.data.abs.DataValidator : Protocol defining the validator interface.
adc_toolkit.data.validators.pandera.validate_data : Core validation orchestration.
adc_toolkit.data.validators.pandera.parameters.PanderaParameters : Configuration.
adc_toolkit.data.validators.gx.GXValidator : Alternative validator using Great Expectations.
adc_toolkit.data.validators.no_validator.NoValidator : No-op validator implementation.

Notes
-----
This implementation is optimized for:

- **Rapid prototyping**: Auto-generated schemas reduce setup friction
- **Incremental refinement**: Generated schemas serve as customizable templates
- **Version control**: Schema scripts are plain Python files suitable for git
- **Type safety**: Full integration with Python type hints and static analysis

The validator uses Pandera's DataFrameSchema.validate() method under the hood,
which provides rich error reporting and flexible validation strategies.

Examples
--------
Basic validator setup and usage:

>>> from pathlib import Path
>>> from adc_toolkit.data.validators.pandera import PanderaValidator
>>> validator = PanderaValidator.in_directory("config/validators")
>>> import pandas as pd
>>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
>>> validated = validator.validate("customers", df)

Using with custom parameters:

>>> from adc_toolkit.data.validators.pandera import PanderaParameters
>>> params = PanderaParameters(lazy=False)  # Fail-fast mode
>>> validator = PanderaValidator(config_path="config/validators", parameters=params)

Integration with ValidatedDataCatalog:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> catalog = ValidatedDataCatalog.in_directory(
...     path="config", validator=PanderaValidator.in_directory("config/validators")
... )
>>> df = catalog.load("customers")  # Automatically validated
"""

from pathlib import Path

from adc_toolkit.data.abs import Data
from adc_toolkit.data.validators.pandera.parameters import PanderaParameters
from adc_toolkit.data.validators.pandera.validate_data import validate_data


class PanderaValidator:
    """
    Pandera-based data validator with automatic schema generation.

    PanderaValidator is a concrete implementation of the DataValidator protocol
    that uses Pandera (https://pandera.readthedocs.io/) for schema-based data
    validation. It provides a seamless validation workflow that combines automatic
    schema generation with manual customization capabilities.

    The validator orchestrates a two-phase approach to data validation:

    **Phase 1: Schema Management** (Auto-generation)
        On first validation of a dataset, the validator automatically generates
        a Pandera schema script by introspecting the data structure (column names,
        data types). The generated schema is saved as an editable Python file at
        ``{config_path}/pandera_schemas/{category}/{dataset}.py``, where the
        category and dataset name are derived from the validation name (e.g.,
        "raw.customers" creates ``raw/customers.py``).

    **Phase 2: Validation Execution** (Rule Enforcement)
        On all validations (including first use), the validator loads the schema
        script and executes validation against the data using Pandera's
        ``DataFrameSchema.validate()`` method. If validation fails, it raises a
        detailed ``PanderaValidationError`` with comprehensive error information.

    This design enables an iterative workflow:

    1. Run validation immediately without manual schema creation
    2. Review auto-generated schemas and add custom validation rules
    3. Commit schemas to version control for team collaboration
    4. Evolve schemas as data requirements change over time

    The validator integrates seamlessly with ``ValidatedDataCatalog`` to provide
    automatic validation on all data load and save operations, ensuring data
    quality throughout the entire data pipeline.

    Attributes
    ----------
    config_path : Path
        The directory path where Pandera schema scripts are stored and loaded from.
        Schema files are organized in a hierarchical structure under this path,
        specifically at ``{config_path}/pandera_schemas/``. For example, if
        config_path is ``Path("config/validators")``, schemas are stored at
        ``config/validators/pandera_schemas/{category}/{dataset}.py``.
    parameters : PanderaParameters
        Configuration parameters controlling validation behavior. The primary
        parameter is ``lazy``, which determines error collection strategy:

        - ``lazy=True`` (default): Collects all validation errors across the
          entire dataset before raising an exception, providing comprehensive
          error reporting.
        - ``lazy=False``: Raises an exception immediately upon encountering the
          first validation failure, useful for debugging.

        If None is provided during instantiation, defaults to
        ``PanderaParameters()`` with default settings (``lazy=True``).

    Parameters
    ----------
    config_path : str or Path
        Path to the root configuration directory where Pandera schema scripts are
        stored. The validator will create a ``pandera_schemas`` subdirectory under
        this path to organize schema files. Can be provided as either a string or
        pathlib.Path object.
    parameters : PanderaParameters or None, optional
        Configuration parameters for validation behavior. If None (default), uses
        ``PanderaParameters()`` with default settings (``lazy=True`` for
        comprehensive error reporting).

    Raises
    ------
    TypeError
        If config_path cannot be converted to a Path object.
    OSError
        If the config_path directory does not exist and cannot be created during
        schema generation.

    See Also
    --------
    PanderaParameters : Configuration parameters for validation behavior.
    validate_data : Core validation function used internally by this validator.
    adc_toolkit.data.abs.DataValidator : Protocol that this class implements.
    adc_toolkit.data.validators.gx.GXValidator : Alternative validator using Great Expectations.
    adc_toolkit.data.ValidatedDataCatalog : Data catalog with integrated validation.

    Notes
    -----
    **Schema Script Organization**

    Schema scripts are organized hierarchically based on validation names. For
    a validation name like "raw.customers", the schema script is created at:

    .. code-block:: text

        {config_path}/pandera_schemas/raw/customers.py

    This structure mirrors typical data lake or data warehouse naming conventions
    (e.g., database.table) and supports large projects with many datasets.

    **Schema Customization Workflow**

    After first validation, edit the generated schema file to add custom checks:

    .. code-block:: python

        # {config_path}/pandera_schemas/raw/customers.py
        import pandera.pandas as pa

        schema = pa.DataFrameSchema(
            {
                "customer_id": pa.Column(
                    "int64",
                    checks=[
                        pa.Check.greater_than(0),  # Must be positive
                        pa.Check(lambda s: s.is_unique, element_wise=False),  # Must be unique
                    ],
                ),
                "email": pa.Column(
                    "object",
                    checks=[
                        pa.Check(lambda s: s.str.contains("@"), element_wise=True),
                    ],
                ),
                "signup_date": pa.Column(
                    "datetime64[ns]",
                    checks=[
                        pa.Check.less_than_or_equal_to(pd.Timestamp.now()),
                    ],
                ),
            }
        )

    **Supported Data Types**

    The validator supports:

    - **pandas DataFrames**: Primary use case with full feature support
    - **PySpark DataFrames**: Generates PySpark-compatible schemas (requires pyspark)

    **Thread Safety**

    This class is thread-safe for validation operations on existing schemas.
    However, the initial schema auto-generation is not thread-safe. If multiple
    threads validate the same dataset for the first time concurrently, race
    conditions may occur. For concurrent scenarios, pre-generate schemas or
    implement external locking.

    **Performance Considerations**

    - Schema scripts are dynamically imported on each validation call. For
      high-frequency scenarios, consider caching validator instances.
    - The ``lazy=True`` mode has slightly more overhead as it collects all errors,
      but provides significantly better developer experience for fixing issues.
    - Auto-generation only occurs once per dataset, so performance impact is
      negligible after initial schema creation.

    **Comparison with Great Expectations**

    Use PanderaValidator when:

    - You need lightweight, pandas-native validation
    - You prefer Python-based schema definitions over YAML/JSON
    - You want tight integration with type hints and static analysis
    - Your team is comfortable with code-based configuration

    Use GXValidator when:

    - You need profiling and automatic expectation generation
    - You want data documentation websites (Data Docs)
    - You need enterprise features (cloud backends, data quality dashboards)
    - You prefer declarative YAML/JSON configuration

    Examples
    --------
    Create a validator using the factory method:

    >>> from adc_toolkit.data.validators.pandera import PanderaValidator
    >>> validator = PanderaValidator.in_directory("config/validators")

    Create a validator using the constructor:

    >>> from pathlib import Path
    >>> validator = PanderaValidator(config_path=Path("config/validators"))

    Create a validator with custom parameters for fail-fast mode:

    >>> from adc_toolkit.data.validators.pandera import PanderaParameters
    >>> params = PanderaParameters(lazy=False)
    >>> validator = PanderaValidator(config_path="config/validators", parameters=params)

    Basic validation workflow:

    >>> import pandas as pd
    >>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]})
    >>> validator = PanderaValidator.in_directory("config/validators")
    >>> validated_df = validator.validate("raw.customers", df)
    >>> # First run: auto-generates schema at config/validators/pandera_schemas/raw/customers.py
    >>> # Subsequent runs: uses existing schema

    Handle validation failures with comprehensive error reporting:

    >>> df_invalid = pd.DataFrame(
    ...     {
    ...         "id": [1, -2, 3],  # Invalid: negative ID
    ...         "name": ["Alice", "Bob", None],  # Invalid: null name
    ...         "age": [25, 30, 150],  # Invalid: unrealistic age
    ...     }
    ... )
    >>> from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
    >>> try:
    ...     validator.validate("raw.customers", df_invalid)
    ... except PanderaValidationError as e:
    ...     print(f"Validation failed for: {e.table_name}")
    ...     print(f"Schema file: {e.schema_path}")
    ...     print(f"Errors: {e.original_error}")
    ...     # All validation errors are included (lazy=True)

    Integration with ValidatedDataCatalog:

    >>> from adc_toolkit.data import ValidatedDataCatalog
    >>> catalog = ValidatedDataCatalog.in_directory(
    ...     path="config", validator=PanderaValidator.in_directory("config/validators")
    ... )
    >>> df = catalog.load("raw.customers")  # Validates after loading
    >>> catalog.save("processed.customers", df)  # Validates before saving

    Iterative schema customization workflow:

    >>> # Step 1: First validation auto-generates schema
    >>> validator = PanderaValidator.in_directory("config/validators")
    >>> validator.validate("raw.customers", df)
    >>>
    >>> # Step 2: Edit generated schema to add custom checks
    >>> # File: config/validators/pandera_schemas/raw/customers.py
    >>> # Add: pa.Check.greater_than(0) to "id" column
    >>>
    >>> # Step 3: Subsequent validations use customized schema
    >>> validator.validate("raw.customers", df)  # Now enforces custom rules

    Validate PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.getOrCreate()
    >>> spark_df = spark.createDataFrame([(1, "Alice", 25), (2, "Bob", 30)], ["id", "name", "age"])
    >>> validator = PanderaValidator.in_directory("config/validators")
    >>> validated_spark = validator.validate("raw.spark_customers", spark_df)
    >>> # Generates PySpark-compatible schema with pyspark.sql.types imports

    Use in a data quality pipeline:

    >>> def quality_check_pipeline(input_df):
    ...     validator = PanderaValidator.in_directory("config/validators")
    ...
    ...     # Validate raw input
    ...     validated_input = validator.validate("raw.data", input_df)
    ...
    ...     # Transform data
    ...     transformed = transform(validated_input)
    ...
    ...     # Validate transformed output
    ...     validated_output = validator.validate("processed.data", transformed)
    ...
    ...     return validated_output

    Multiple validators for different environments:

    >>> dev_validator = PanderaValidator.in_directory("config/validators/dev")
    >>> prod_validator = PanderaValidator.in_directory("config/validators/prod")
    >>> # Use different validation rules for dev vs. production
    """

    def __init__(self, config_path: str | Path, parameters: PanderaParameters | None = None) -> None:
        """
        Initialize a PanderaValidator instance.

        Constructs a new validator configured to use schema scripts from the
        specified directory. The constructor sets up the schema storage location
        and validation parameters, but does not perform any I/O operations or
        validation at initialization time.

        The validator creates a logical schema directory at
        ``{config_path}/pandera_schemas/`` where all Pandera schema scripts will
        be stored and loaded from. This subdirectory organization keeps Pandera
        schemas separate from other configuration files and validation frameworks
        (e.g., Great Expectations configurations).

        Parameters
        ----------
        config_path : str or Path
            Path to the root configuration directory. The validator will use a
            ``pandera_schemas`` subdirectory under this path for storing and
            loading schema scripts. Can be provided as either a string (which will
            be converted to a Path) or a pathlib.Path object. The path can be
            absolute or relative to the current working directory.

            For example, if config_path is ``"config/validators"``, schema scripts
            will be stored at ``config/validators/pandera_schemas/{category}/{dataset}.py``.
        parameters : PanderaParameters or None, optional
            Configuration parameters controlling validation behavior. If None
            (default), uses ``PanderaParameters()`` with default settings
            (``lazy=True`` for comprehensive error reporting). Provide a custom
            ``PanderaParameters`` instance to configure validation strategy:

            - ``PanderaParameters(lazy=True)``: Collect all errors (recommended)
            - ``PanderaParameters(lazy=False)``: Fail-fast on first error

        Returns
        -------
        None
            Constructor does not return a value.

        Raises
        ------
        TypeError
            If config_path cannot be converted to a Path object (e.g., if an
            invalid type is provided like int or dict).

        See Also
        --------
        in_directory : Alternative factory method for creating validators.
        validate : Perform validation on a dataset.
        PanderaParameters : Configuration parameters for validation behavior.

        Notes
        -----
        **Lazy Initialization**

        The constructor does not create the ``pandera_schemas`` directory at
        initialization time. The directory is created only when the first schema
        script is generated during validation. This lazy approach avoids
        unnecessary file system operations if the validator is created but never
        used.

        **Path Handling**

        The constructor automatically converts string paths to pathlib.Path objects
        and appends the ``pandera_schemas`` subdirectory. This means:

        .. code-block:: python

            validator = PanderaValidator(config_path="config")
            # validator.config_path is Path("config/pandera_schemas")

        **Immutability**

        While the validator instance itself is mutable (standard Python object),
        the ``parameters`` attribute uses a frozen dataclass (PanderaParameters),
        ensuring validation behavior remains consistent throughout the validator's
        lifecycle.

        **No Validation at Initialization**

        This constructor only sets up the validator configuration. No validation
        occurs until the ``validate()`` method is called. This design allows
        validators to be created cheaply and reused across multiple validation
        operations.

        Examples
        --------
        Create a validator with default parameters:

        >>> from adc_toolkit.data.validators.pandera import PanderaValidator
        >>> validator = PanderaValidator(config_path="config/validators")
        >>> validator.config_path
        PosixPath('config/validators/pandera_schemas')
        >>> validator.parameters.lazy
        True

        Create a validator with custom parameters for fail-fast mode:

        >>> from adc_toolkit.data.validators.pandera import PanderaParameters
        >>> params = PanderaParameters(lazy=False)
        >>> validator = PanderaValidator(config_path="config/validators", parameters=params)
        >>> validator.parameters.lazy
        False

        Using pathlib.Path for config_path:

        >>> from pathlib import Path
        >>> config_dir = Path("config") / "validators"
        >>> validator = PanderaValidator(config_path=config_dir)
        >>> validator.config_path
        PosixPath('config/validators/pandera_schemas')

        Create multiple validators for different schema directories:

        >>> dev_validator = PanderaValidator(config_path="config/dev/validators")
        >>> prod_validator = PanderaValidator(config_path="config/prod/validators")
        >>> # Each validator uses a separate schema directory

        Reuse a validator for multiple validations:

        >>> validator = PanderaValidator(config_path="config/validators")
        >>> validated_df1 = validator.validate("dataset1", df1)
        >>> validated_df2 = validator.validate("dataset2", df2)
        >>> # Same validator instance, different datasets
        """
        self.config_path = Path(config_path) / "pandera_schemas"
        self.parameters = parameters or PanderaParameters()

    @classmethod
    def in_directory(cls, path: str | Path, parameters: PanderaParameters | None = None) -> "PanderaValidator":
        """
        Create a PanderaValidator from a configuration directory (factory method).

        This is the recommended factory method for creating PanderaValidator
        instances. It provides a consistent interface with other toolkit components
        (e.g., ``ValidatedDataCatalog.in_directory()``, ``KedroDataCatalog.in_directory()``)
        and follows the factory pattern for object construction from configuration.

        The method is functionally equivalent to calling the constructor directly,
        but provides better semantic clarity in code that uses multiple toolkit
        components with directory-based configuration.

        Parameters
        ----------
        path : str or Path
            Path to the root configuration directory where Pandera schema scripts
            are stored. The validator will use a ``pandera_schemas`` subdirectory
            under this path. Can be provided as either a string or pathlib.Path
            object. The path can be absolute or relative to the current working
            directory.

            For example, if path is ``"config/validators"``, schema scripts will
            be stored at ``config/validators/pandera_schemas/{category}/{dataset}.py``.
        parameters : PanderaParameters or None, optional
            Configuration parameters controlling validation behavior. If None
            (default), uses ``PanderaParameters()`` with default settings
            (``lazy=True`` for comprehensive error reporting). Provide a custom
            ``PanderaParameters`` instance to configure validation strategy:

            - ``PanderaParameters(lazy=True)``: Collect all errors (recommended)
            - ``PanderaParameters(lazy=False)``: Fail-fast on first error

        Returns
        -------
        PanderaValidator
            A new validator instance configured to use schema scripts from the
            specified directory. The returned validator is ready to use for
            validation operations via the ``validate()`` method.

        Raises
        ------
        TypeError
            If path cannot be converted to a Path object (e.g., if an invalid
            type is provided like int or dict).

        See Also
        --------
        __init__ : Alternative constructor for creating validators.
        validate : Perform validation on a dataset.
        PanderaParameters : Configuration parameters for validation behavior.
        adc_toolkit.data.ValidatedDataCatalog.in_directory : Similar factory method
            for creating validated data catalogs.

        Notes
        -----
        **Factory Pattern**

        This method implements the factory pattern, providing a standard interface
        for creating validators from directory-based configuration. The pattern is
        used consistently across the toolkit:

        .. code-block:: python

            # Similar patterns across toolkit components
            catalog = KedroDataCatalog.in_directory("config/")
            validator = PanderaValidator.in_directory("config/validators")
            gx_validator = GXValidator.in_directory("config/gx")

        **Semantic Clarity**

        Using ``in_directory()`` instead of the constructor makes code more
        readable and self-documenting:

        .. code-block:: python

            # Clear intent: validator configured from this directory
            validator = PanderaValidator.in_directory("config/validators")

            # vs. less clear constructor call
            validator = PanderaValidator("config/validators")

        **Design Rationale**

        The factory method pattern is preferred over direct constructor calls in
        the toolkit because:

        1. Provides consistent API across all components
        2. Makes the configuration-from-directory pattern explicit
        3. Allows future extension with additional factory methods
        4. Improves code readability and maintainability

        **Usage in ValidatedDataCatalog**

        This method is commonly used when configuring ``ValidatedDataCatalog``
        with a custom validator:

        .. code-block:: python

            from adc_toolkit.data import ValidatedDataCatalog
            from adc_toolkit.data.validators.pandera import PanderaValidator

            catalog = ValidatedDataCatalog.in_directory(
                path="config", validator=PanderaValidator.in_directory("config/validators")
            )

        Examples
        --------
        Create a validator using the factory method (recommended):

        >>> from adc_toolkit.data.validators.pandera import PanderaValidator
        >>> validator = PanderaValidator.in_directory("config/validators")
        >>> validator.config_path
        PosixPath('config/validators/pandera_schemas')

        Create a validator with custom parameters:

        >>> from adc_toolkit.data.validators.pandera import PanderaParameters
        >>> params = PanderaParameters(lazy=False)
        >>> validator = PanderaValidator.in_directory(path="config/validators", parameters=params)
        >>> validator.parameters.lazy
        False

        Using pathlib.Path:

        >>> from pathlib import Path
        >>> config_dir = Path("config") / "validators"
        >>> validator = PanderaValidator.in_directory(path=config_dir)

        Integration with ValidatedDataCatalog:

        >>> from adc_toolkit.data import ValidatedDataCatalog
        >>> catalog = ValidatedDataCatalog.in_directory(
        ...     path="config", validator=PanderaValidator.in_directory("config/validators")
        ... )
        >>> # ValidatedDataCatalog uses the PanderaValidator for all load/save ops

        Consistent API across different validators:

        >>> from adc_toolkit.data.validators.pandera import PanderaValidator
        >>> from adc_toolkit.data.validators.gx import GXValidator
        >>> pandera_val = PanderaValidator.in_directory("config/pandera")
        >>> gx_val = GXValidator.in_directory("config/gx")
        >>> # Both use the same factory method pattern

        Multiple validators for different environments:

        >>> dev_validator = PanderaValidator.in_directory("config/dev/validators")
        >>> staging_validator = PanderaValidator.in_directory("config/staging/validators")
        >>> prod_validator = PanderaValidator.in_directory("config/prod/validators")
        >>> # Each environment can have different validation rules

        Dependency injection pattern:

        >>> def create_pipeline(validator_path: str):
        ...     validator = PanderaValidator.in_directory(validator_path)
        ...     return DataPipeline(validator=validator)
        >>> # Easy to swap validator configurations
        >>> dev_pipeline = create_pipeline("config/dev/validators")
        >>> prod_pipeline = create_pipeline("config/prod/validators")
        """
        return cls(path, parameters=parameters)

    def validate(self, name: str, data: Data) -> Data:
        """
        Validate a dataset against its Pandera schema.

        This is the primary validation method that implements the DataValidator
        protocol. It orchestrates the complete validation workflow, from automatic
        schema generation (if needed) to validation execution, providing seamless
        data quality checking with minimal setup.

        The method delegates to the ``validate_data`` function, which implements
        a two-phase validation approach:

        **Phase 1: Schema Preparation** (First Use Only)
            If no schema script exists for the dataset name, automatically generate
            one by introspecting the data structure. The generated schema is saved
            at ``{self.config_path}/{category}/{dataset}.py`` and serves as an
            editable template for adding custom validation rules.

        **Phase 2: Validation Execution** (Every Use)
            Load the schema script as a Python module, extract the
            ``DataFrameSchema`` object, and execute validation using Pandera's
            ``schema.validate(data, lazy=self.parameters.lazy)`` method. Return
            validated data if all checks pass, or raise ``PanderaValidationError``
            with comprehensive error details if validation fails.

        This design enables rapid prototyping (no upfront schema creation required)
        while supporting iterative refinement (schemas can be customized after
        auto-generation). Schema scripts are version-controlled Python files,
        facilitating team collaboration and schema evolution tracking.

        Parameters
        ----------
        name : str
            The dataset name/identifier that determines which schema script to use.
            Should follow the convention ``"category.dataset_name"`` (e.g.,
            ``"raw.customers"``, ``"processed.sales"``). The name serves multiple
            purposes:

            - Determines schema file location: ``{config_path}/{category}/{dataset}.py``
            - Provides context in validation error messages
            - Enables logical organization of schemas by data pipeline stage

            Names with a single dot separator create a two-level directory
            structure. For example, ``"raw.customers"`` creates a schema at
            ``{self.config_path}/raw/customers.py``.
        data : Data
            The data object to validate. Must be a protocol-compliant Data object
            (pandas DataFrame, PySpark DataFrame, etc.) with ``columns`` and
            ``dtypes`` attributes. The data structure is validated against the
            schema defined in (or auto-generated for) the corresponding schema
            script.

            Supported types:
            - ``pandas.DataFrame``: Primary use case with full feature support
            - ``pyspark.sql.DataFrame``: Requires pyspark installation

        Returns
        -------
        Data
            The validated data object. If validation passes all checks defined in
            the schema, returns the original data object (potentially with
            Pandera-applied type coercions if configured in the schema). The return
            type matches the input data type (pandas in, pandas out; PySpark in,
            PySpark out).

            The returned data can be used immediately in downstream processing with
            confidence that it meets all defined quality requirements.

        Raises
        ------
        PanderaValidationError
            Raised when data validation fails against the schema. This custom
            exception wraps Pandera's underlying SchemaError or SchemaErrors and
            enriches it with additional context:

            Attributes of PanderaValidationError:
            - ``table_name``: The dataset name that failed validation
            - ``schema_path``: Full filesystem path to the schema script file
            - ``original_error``: The underlying Pandera error with detailed
              validation failure information (row indices, column names, observed
              values, expected constraints)

            With ``lazy=True`` (default), the exception includes all validation
            errors across the entire dataset. With ``lazy=False``, it includes only
            the first error encountered.
        ValueError
            Raised if the dataframe type is not supported (neither pandas nor
            pyspark), originating from the schema compiler during auto-generation.
        ModuleNotFoundError
            Raised if the schema script cannot be imported, typically indicating
            a Python syntax error in a manually edited schema file. Check the
            schema file for syntax errors or import statement issues.
        AttributeError
            Raised if the schema script module does not define a ``schema``
            attribute, indicating the schema file structure is invalid. The schema
            file must contain ``schema = pa.DataFrameSchema(...)`` at module level.
        OSError
            Raised if there are file system permissions issues preventing schema
            file creation (during auto-generation) or reading (during validation).

        See Also
        --------
        validate_data : The underlying validation function called by this method.
        PanderaParameters : Configuration parameters controlling validation behavior.
        PanderaValidationError : Custom exception raised on validation failure.
        in_directory : Factory method for creating validator instances.
        adc_toolkit.data.ValidatedDataCatalog : Data catalog with integrated validation.

        Notes
        -----
        **Validation Workflow**

        The complete sequence executed by this method:

        1. Check if schema file exists at ``{self.config_path}/{category}/{dataset}.py``
        2. If missing, auto-generate schema by introspecting data structure
        3. Load schema file as a Python module using dynamic import
        4. Extract the ``schema`` DataFrameSchema object from the module
        5. Call ``schema.validate(data, lazy=self.parameters.lazy)``
        6. Return validated data if all checks pass
        7. Raise PanderaValidationError with context if validation fails

        **Schema Customization After Auto-Generation**

        After first validation, edit the generated schema file to add domain-specific
        validation rules:

        .. code-block:: python

            # {self.config_path}/raw/customers.py (auto-generated)
            import pandera.pandas as pa

            # Insert your additional checks to `checks` list parameter
            schema = pa.DataFrameSchema(
                {
                    "customer_id": pa.Column(
                        "int64",
                        checks=[
                            pa.Check.greater_than(0),  # Add: IDs must be positive
                            pa.Check(lambda s: s.is_unique, element_wise=False),  # Add: unique
                        ],
                    ),
                    "email": pa.Column(
                        "object",
                        checks=[
                            pa.Check(lambda s: s.str.contains("@")),  # Add: valid email
                        ],
                    ),
                    "age": pa.Column(
                        "int64",
                        checks=[
                            pa.Check.in_range(0, 120),  # Add: realistic age range
                        ],
                    ),
                }
            )

        **Error Reporting: Lazy vs. Fail-Fast**

        The ``parameters.lazy`` setting significantly affects error reporting:

        **Lazy Mode (lazy=True, default)**: Recommended for production
            - Collects all validation errors across entire dataset
            - Provides comprehensive error report in single validation run
            - Higher overhead but better developer experience
            - Example: "Found 47 validation errors in columns 'age', 'email'"

        **Fail-Fast Mode (lazy=False)**: Useful for debugging
            - Raises exception on first validation failure
            - Lower overhead, faster failure detection
            - Requires multiple validation runs to find all errors
            - Example: "Row 23: age value 150 exceeds maximum 120"

        **Performance Considerations**

        - Schema scripts are dynamically imported on each validation call. For
          high-frequency validation scenarios (e.g., streaming data), consider
          caching the validator instance and reusing it across validations.
        - Auto-generation only occurs once per dataset. After initial schema
          creation, there's no performance penalty for the auto-generation feature.
        - Large dataset validation can be expensive. Consider sampling strategies
          for very large datasets if full validation is not required.

        **Thread Safety**

        This method is thread-safe for validation operations on existing schemas
        (multiple threads can call ``validate()`` concurrently on different datasets).
        However, the initial schema auto-generation is not thread-safe. If multiple
        threads validate the same dataset for the first time concurrently, race
        conditions may occur. For concurrent first-time validation, implement
        external locking or pre-generate schemas.

        **Integration with Data Pipelines**

        This method integrates seamlessly with data pipeline workflows:

        .. code-block:: python

            def pipeline_stage(validator, input_data):
                # Validate input from previous stage
                validated_input = validator.validate("stage_input", input_data)

                # Process with confidence that data meets requirements
                processed = transform(validated_input)

                # Validate output before passing to next stage
                validated_output = validator.validate("stage_output", processed)

                return validated_output

        Examples
        --------
        Basic validation with auto-generated schema:

        >>> import pandas as pd
        >>> from adc_toolkit.data.validators.pandera import PanderaValidator
        >>> validator = PanderaValidator.in_directory("config/validators")
        >>> df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]})
        >>> validated = validator.validate("raw.customers", df)
        >>> # First run: auto-generates schema at config/validators/pandera_schemas/raw/customers.py
        >>> # Subsequent runs: uses existing schema
        >>> print(validated)
           id     name  age
        0   1    Alice   25
        1   2      Bob   30
        2   3  Charlie   35

        Validation failure with comprehensive error reporting (lazy=True):

        >>> df_invalid = pd.DataFrame(
        ...     {
        ...         "id": [1, -2, 3],  # Invalid: negative ID (if custom check added)
        ...         "name": ["Alice", "Bob", None],  # Invalid: null name
        ...         "age": [25, 30, 150],  # Invalid: unrealistic age (if custom check added)
        ...     }
        ... )
        >>> from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
        >>> try:
        ...     validator.validate("raw.customers", df_invalid)
        ... except PanderaValidationError as e:
        ...     print(f"Validation failed for table: {e.table_name}")
        ...     print(f"Schema location: {e.schema_path}")
        ...     print(f"Error details: {e.original_error}")
        ...     # All validation errors are reported together (lazy=True)

        Fail-fast validation for debugging:

        >>> from adc_toolkit.data.validators.pandera import PanderaParameters
        >>> validator_debug = PanderaValidator.in_directory(
        ...     path="config/validators", parameters=PanderaParameters(lazy=False)
        ... )
        >>> try:
        ...     validator_debug.validate("raw.customers", df_invalid)
        ... except Exception as e:
        ...     print(f"First error encountered: {e.original_error}")
        ...     # Only the first validation error is reported (lazy=False)

        Validate multiple datasets with same validator:

        >>> validator = PanderaValidator.in_directory("config/validators")
        >>> customers = validator.validate("raw.customers", customers_df)
        >>> orders = validator.validate("raw.orders", orders_df)
        >>> products = validator.validate("raw.products", products_df)
        >>> # Reuse same validator instance for efficiency

        Validation in a data processing pipeline:

        >>> def process_customer_data():
        ...     validator = PanderaValidator.in_directory("config/validators")
        ...
        ...     # Load raw data
        ...     raw_df = load_raw_customers()
        ...
        ...     # Validate input
        ...     validated_input = validator.validate("raw.customers", raw_df)
        ...
        ...     # Process with confidence
        ...     processed_df = transform_customers(validated_input)
        ...
        ...     # Validate output
        ...     validated_output = validator.validate("processed.customers", processed_df)
        ...
        ...     return validated_output

        Using with PySpark DataFrame:

        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.getOrCreate()
        >>> spark_df = spark.createDataFrame([(1, "Alice", 25), (2, "Bob", 30)], ["id", "name", "age"])
        >>> validator = PanderaValidator.in_directory("config/validators")
        >>> validated_spark = validator.validate("raw.spark_customers", spark_df)
        >>> # Returns validated PySpark DataFrame

        Integration with ValidatedDataCatalog (automatic validation):

        >>> from adc_toolkit.data import ValidatedDataCatalog
        >>> catalog = ValidatedDataCatalog.in_directory(
        ...     path="config", validator=PanderaValidator.in_directory("config/validators")
        ... )
        >>> # ValidatedDataCatalog internally calls validator.validate()
        >>> df = catalog.load("raw.customers")  # Validates after loading
        >>> catalog.save("processed.customers", df)  # Validates before saving
        """
        return validate_data(name, data, self.config_path, self.parameters)
