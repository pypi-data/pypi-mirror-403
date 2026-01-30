"""
Datasource manager for Great Expectations data validation.

This module provides the DatasourceManager class, which creates and manages
Great Expectations (GX) datasources for different DataFrame types. It acts as
an abstraction layer between the adc-toolkit's Data protocol and GX's datasource
system, automatically detecting DataFrame types and configuring the appropriate
datasource (PandasDatasource or SparkDFDatasource).

The DatasourceManager is primarily used internally by the BatchManager to set up
validation infrastructure, but can be used directly when fine-grained control
over datasource configuration is needed.

Classes
-------
DatasourceManager
    Manages GX datasources for pandas and PySpark DataFrames.

See Also
--------
adc_toolkit.data.validators.gx.batch_managers.batch_manager.BatchManager : Uses DatasourceManager.
adc_toolkit.data.validators.gx.gx_validator.GXValidator : Validation orchestrator.
great_expectations.datasource.PandasDatasource : GX datasource for pandas DataFrames.
great_expectations.datasource.SparkDFDatasource : GX datasource for PySpark DataFrames.

Notes
-----
Great Expectations requires datasources to be configured before creating batch
requests and running validations. This manager automates that process by:

1. Detecting the DataFrame type (pandas or pyspark) using module introspection
2. Selecting the appropriate datasource type
3. Adding or updating the datasource in the GX data context
4. Naming datasources consistently for reuse

The manager uses a class-level mapping (`data_reading_methods`) to determine
which GX data context method to call based on the DataFrame type.

Examples
--------
Basic usage with a pandas DataFrame:

>>> import pandas as pd
>>> from great_expectations.data_context import EphemeralDataContext
>>> from adc_toolkit.data.validators.gx.batch_managers import DatasourceManager
>>> df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4.0, 5.0, 6.0]})
>>> context = EphemeralDataContext()
>>> manager = DatasourceManager(data=df, data_context=context)
>>> datasource = manager.add_or_update_datasource()
>>> print(datasource.name)
pandas_datasource

Using with a PySpark DataFrame:

>>> from pyspark.sql import SparkSession
>>> spark = SparkSession.builder.getOrCreate()
>>> spark_df = spark.createDataFrame([(1, 2), (3, 4)], ["a", "b"])
>>> manager = DatasourceManager(data=spark_df, data_context=context)
>>> datasource = manager.add_or_update_datasource()
>>> print(datasource.name)
pyspark_datasource

Integration with BatchManager:

>>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
>>> batch_manager = BatchManager(name="my_dataset", data=df, data_context=context)
>>> # DatasourceManager is used internally by BatchManager to set up datasources
"""

from typing import ClassVar

from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.datasource import PandasDatasource, SparkDFDatasource

from adc_toolkit.data.abs import Data
from adc_toolkit.data.validators.table_utils.table_properties import extract_dataframe_type


class DatasourceManager:
    """
    Manager for Great Expectations datasources supporting pandas and PySpark DataFrames.

    This class provides automated datasource configuration for Great Expectations (GX)
    validation workflows. It detects the DataFrame type from the data object and
    creates or updates the appropriate GX datasource (PandasDatasource for pandas
    DataFrames, SparkDFDatasource for PySpark DataFrames) in the provided data context.

    The manager maintains a consistent naming scheme for datasources based on the
    DataFrame type, enabling datasource reuse across multiple validation runs. If a
    datasource with the expected name already exists in the data context, it is updated
    rather than recreated.

    Parameters
    ----------
    data : Data
        The data object to be validated. Must conform to the Data protocol with
        `columns` and `dtypes` attributes. Typically a pandas DataFrame or PySpark
        DataFrame, though any compatible data structure is supported.
    data_context : AbstractDataContext
        The Great Expectations data context that will manage the datasource. This
        context stores datasource configurations, expectations, and validation results.
        Can be an EphemeralDataContext (for testing), FileDataContext (for persistent
        configurations), or CloudDataContext (for remote storage).

    Attributes
    ----------
    data : Data
        The data object provided during initialization. Stored for DataFrame type
        detection and datasource configuration.
    data_context : AbstractDataContext
        The GX data context where datasources will be added or updated. Used to
        access the `sources` API for datasource management.
    datasource_type : str
        The detected DataFrame type, extracted from the data object's module name.
        Common values are "pandas" for pandas DataFrames and "pyspark" for PySpark
        DataFrames. This value determines which datasource type to create.
    data_reading_methods : ClassVar[dict[str, str]]
        Class-level mapping from DataFrame types to GX data context method names.
        Maps "pandas" to "add_or_update_pandas" and "pyspark" to "add_or_update_spark".
        This mapping is used to dynamically select the correct data context method
        for creating datasources.

    Methods
    -------
    add_or_update_datasource()
        Create or update a GX datasource based on the DataFrame type.

    See Also
    --------
    adc_toolkit.data.abs.Data : Protocol defining the Data interface.
    adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_type : Function for type detection.
    adc_toolkit.data.validators.gx.batch_managers.batch_manager.BatchManager : Higher-level batch management.
    great_expectations.data_context.AbstractDataContext : GX data context interface.
    great_expectations.datasource.PandasDatasource : GX datasource for pandas.
    great_expectations.datasource.SparkDFDatasource : GX datasource for PySpark.

    Notes
    -----
    Datasource Naming Convention
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    Datasources are named using the pattern "{framework}_datasource", where framework
    is "pandas" or "pyspark". This naming convention ensures:

    - Predictable datasource names for debugging and introspection
    - Datasource reuse when validating multiple datasets of the same type
    - Clear identification of the underlying data processing framework

    DataFrame Type Detection
    ^^^^^^^^^^^^^^^^^^^^^^^
    The manager uses `extract_dataframe_type()` from table_utils to determine the
    DataFrame type by inspecting the module name of the data object's type. This
    approach is robust across different versions of pandas and PySpark, as the
    top-level module name remains stable.

    Datasource Lifecycle
    ^^^^^^^^^^^^^^^^^^^
    GX datasources created by this manager are added to the data context's sources
    collection. The "add_or_update" methods ensure that:

    - If no datasource with the target name exists, a new one is created
    - If a datasource with the target name exists, it is updated with the current
      configuration
    - Datasources persist in the data context for the lifetime of the context

    For EphemeralDataContext (commonly used in testing), datasources exist only
    in memory and are discarded when the context is destroyed. For FileDataContext,
    datasource configurations are persisted to YAML files.

    Thread Safety
    ^^^^^^^^^^^^
    The manager itself is not thread-safe. If using in multi-threaded environments,
    ensure that each thread has its own DatasourceManager instance or implement
    external synchronization.

    Examples
    --------
    Create a datasource for a pandas DataFrame:

    >>> import pandas as pd
    >>> from great_expectations.data_context import EphemeralDataContext
    >>> from adc_toolkit.data.validators.gx.batch_managers import DatasourceManager
    >>> df = pd.DataFrame({"x": [1, 2, 3], "y": [4.0, 5.0, 6.0]})
    >>> context = EphemeralDataContext()
    >>> manager = DatasourceManager(data=df, data_context=context)
    >>> manager.datasource_type
    'pandas'
    >>> datasource = manager.add_or_update_datasource()
    >>> datasource.name
    'pandas_datasource'

    Create a datasource for a PySpark DataFrame:

    >>> from pyspark.sql import SparkSession
    >>> spark = SparkSession.builder.appName("test").getOrCreate()
    >>> spark_df = spark.createDataFrame([(1, 2), (3, 4)], ["col_a", "col_b"])
    >>> manager = DatasourceManager(data=spark_df, data_context=context)
    >>> manager.datasource_type
    'pyspark'
    >>> datasource = manager.add_or_update_datasource()
    >>> datasource.name
    'pyspark_datasource'

    Verify datasource was added to context:

    >>> datasources = context.list_datasources()
    >>> len(datasources)
    1
    >>> datasources[0]["name"]
    'pyspark_datasource'

    Reuse datasource across multiple managers:

    >>> df1 = pd.DataFrame({"a": [1, 2]})
    >>> df2 = pd.DataFrame({"b": [3, 4]})
    >>> manager1 = DatasourceManager(data=df1, data_context=context)
    >>> manager2 = DatasourceManager(data=df2, data_context=context)
    >>> ds1 = manager1.add_or_update_datasource()
    >>> ds2 = manager2.add_or_update_datasource()
    >>> ds1.name == ds2.name
    True
    >>> len(context.list_datasources())
    1

    Use with different data context types:

    >>> from great_expectations.data_context import FileDataContext
    >>> from pathlib import Path
    >>> context_path = Path("/path/to/gx/config")
    >>> file_context = FileDataContext(project_root_dir=context_path)
    >>> manager = DatasourceManager(data=df, data_context=file_context)
    >>> datasource = manager.add_or_update_datasource()
    >>> # Datasource configuration is persisted to YAML in the context directory

    Error handling for unsupported DataFrame types:

    >>> unsupported_data = {"a": [1, 2, 3]}  # Plain dict, not a DataFrame
    >>> manager = DatasourceManager(data=unsupported_data, data_context=context)
    >>> manager.datasource_type
    'builtins'
    >>> manager.add_or_update_datasource()
    Traceback (most recent call last):
        ...
    KeyError: 'builtins'
    """

    data_reading_methods: ClassVar[dict[str, str]] = {
        "pandas": "add_or_update_pandas",
        "pyspark": "add_or_update_spark",
    }

    def __init__(self, data: Data, data_context: AbstractDataContext) -> None:
        """
        Initialize the datasource manager with data and GX data context.

        This method sets up the datasource manager by storing references to the
        data object and data context, and automatically detecting the DataFrame
        type. The detected type is used later to determine which GX datasource
        to create (PandasDatasource or SparkDFDatasource).

        The initialization performs DataFrame type detection using module introspection,
        which is a lightweight operation that does not process or validate the data itself.

        Parameters
        ----------
        data : Data
            The data object to be validated. Must conform to the Data protocol with
            `columns` and `dtypes` attributes. Supported types include pandas DataFrame,
            PySpark DataFrame, and other compatible data structures. The object's
            module name is used to determine the appropriate datasource type.
        data_context : AbstractDataContext
            The Great Expectations data context that will store and manage the datasource.
            This context provides the API for adding datasources and must be properly
            initialized before passing to this manager. Common implementations include:
            - EphemeralDataContext: In-memory context for testing
            - FileDataContext: Persists configuration to local filesystem
            - CloudDataContext: Uses remote storage (S3, GCS, Azure Blob)

        Raises
        ------
        AttributeError
            If the data object does not have the required attributes for type detection
            (e.g., if it does not conform to the Data protocol).

        See Also
        --------
        add_or_update_datasource : Create the datasource after initialization.
        adc_toolkit.data.validators.table_utils.table_properties.extract_dataframe_type : Type detection function.

        Notes
        -----
        The initialization process consists of three steps:

        1. **Store Data Reference**: The data object is stored without modification
           or validation. Actual data validation occurs later through GX expectations.

        2. **Store Context Reference**: The data context is stored for later use when
           creating or updating datasources. The context must be compatible with the
           AbstractDataContext interface.

        3. **Detect DataFrame Type**: The `extract_dataframe_type()` function is called
           to determine the data processing framework by inspecting the module name of
           the data object's type. For example:
           - pandas DataFrame returns "pandas"
           - PySpark DataFrame returns "pyspark"

        The detected type is stored in `self.datasource_type` and used by
        `add_or_update_datasource()` to select the appropriate datasource creation
        method from the `data_reading_methods` mapping.

        This method does not create or modify any datasources. The actual datasource
        creation happens when `add_or_update_datasource()` is called.

        Examples
        --------
        Initialize with a pandas DataFrame:

        >>> import pandas as pd
        >>> from great_expectations.data_context import EphemeralDataContext
        >>> from adc_toolkit.data.validators.gx.batch_managers import DatasourceManager
        >>> df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        >>> context = EphemeralDataContext()
        >>> manager = DatasourceManager(data=df, data_context=context)
        >>> manager.datasource_type
        'pandas'
        >>> isinstance(manager.data, pd.DataFrame)
        True

        Initialize with a PySpark DataFrame:

        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.appName("example").getOrCreate()
        >>> spark_df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "value"])
        >>> manager = DatasourceManager(data=spark_df, data_context=context)
        >>> manager.datasource_type
        'pyspark'

        Use different data context types:

        >>> from great_expectations.data_context import FileDataContext
        >>> from pathlib import Path
        >>> config_dir = Path("/path/to/gx/project")
        >>> file_context = FileDataContext(project_root_dir=config_dir)
        >>> manager = DatasourceManager(data=df, data_context=file_context)
        >>> # Datasources created by this manager will be persisted to file_context

        Verify initialization state:

        >>> manager = DatasourceManager(data=df, data_context=context)
        >>> hasattr(manager, "data")
        True
        >>> hasattr(manager, "data_context")
        True
        >>> hasattr(manager, "datasource_type")
        True
        >>> manager.datasource_type in manager.data_reading_methods
        True

        Handle edge cases with type detection:

        >>> # Type detection works even with DataFrame subclasses
        >>> class CustomDataFrame(pd.DataFrame):
        ...     pass
        >>> custom_df = CustomDataFrame({"x": [1, 2, 3]})
        >>> manager = DatasourceManager(data=custom_df, data_context=context)
        >>> manager.datasource_type
        'pandas'
        """
        self.data = data
        self.data_context = data_context
        self.datasource_type = extract_dataframe_type(self.data)

    def add_or_update_datasource(self) -> PandasDatasource | SparkDFDatasource:
        """
        Create or update a GX datasource based on the detected DataFrame type.

        This method dynamically selects and calls the appropriate Great Expectations
        data context method to add or update a datasource. The method selection is
        based on the DataFrame type detected during initialization. For pandas DataFrames,
        it creates a PandasDatasource; for PySpark DataFrames, it creates a
        SparkDFDatasource.

        If a datasource with the target name already exists in the data context, it
        is updated rather than recreated. This ensures idempotency and allows the same
        manager to be called multiple times without creating duplicate datasources.

        The datasource is registered in the data context's sources collection and
        remains available for subsequent operations such as creating data assets and
        batch requests.

        Returns
        -------
        PandasDatasource or SparkDFDatasource
            The created or updated datasource instance. The specific type depends on
            the detected DataFrame type:
            - PandasDatasource for pandas DataFrames
            - SparkDFDatasource for PySpark DataFrames

            The datasource is fully configured and ready to create data assets. Its
            name follows the pattern "{framework}_datasource" (e.g., "pandas_datasource",
            "pyspark_datasource").

        Raises
        ------
        KeyError
            If the detected datasource type is not supported (i.e., not present in
            the `data_reading_methods` mapping). This typically occurs when using a
            data object from an unsupported framework or when the type detection
            fails to identify a known framework.
        AttributeError
            If the data context's sources object does not have the required method
            for adding datasources. This may indicate an incompatible or improperly
            initialized data context.

        See Also
        --------
        __init__ : Initializes the manager and detects DataFrame type.
        adc_toolkit.data.validators.gx.batch_managers.batch_manager.BatchManager : Uses this for batch setup.
        great_expectations.datasource.PandasDatasource : Returned for pandas DataFrames.
        great_expectations.datasource.SparkDFDatasource : Returned for PySpark DataFrames.

        Notes
        -----
        Datasource Creation Process
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^
        The method performs the following steps:

        1. **Method Selection**: Looks up the appropriate data context method name from
           the `data_reading_methods` class variable using the detected datasource type.

        2. **Dynamic Method Call**: Uses `getattr()` to retrieve the method from
           `data_context.sources` and immediately calls it with the datasource name.

        3. **Name Assignment**: The datasource is named using the pattern
           "{framework}_datasource", ensuring consistent and predictable naming across
           all datasource instances of the same type.

        4. **Registration**: The datasource is automatically registered in the data
           context's sources collection, making it available for future operations.

        Idempotency Guarantee
        ^^^^^^^^^^^^^^^^^^^^^
        The "add_or_update" behavior ensures that:

        - First call: Creates a new datasource with the specified name
        - Subsequent calls: Updates the existing datasource with the same name
        - No duplicate datasources are created even if called multiple times

        This is particularly important in workflows where the same manager might be
        instantiated multiple times or where datasource configuration needs to be
        refreshed.

        Datasource Capabilities
        ^^^^^^^^^^^^^^^^^^^^^^^
        The returned datasource provides methods for:

        - Adding data assets (tables, queries, or in-memory DataFrames)
        - Creating batch requests for validation
        - Configuring data connectors and execution engines
        - Managing batch identifiers and partitioning

        After obtaining the datasource, typical next steps include calling
        `datasource.add_dataframe_asset()` to create a data asset and then
        building batch requests for validation.

        Performance Considerations
        ^^^^^^^^^^^^^^^^^^^^^^^^^
        - Datasource creation is lightweight and involves only metadata operations
        - No data is read, copied, or processed during datasource creation
        - The operation is synchronous and completes quickly even for large DataFrames
        - Datasources are reused across validation runs, avoiding repeated setup costs

        Examples
        --------
        Create a datasource for pandas DataFrame:

        >>> import pandas as pd
        >>> from great_expectations.data_context import EphemeralDataContext
        >>> from adc_toolkit.data.validators.gx.batch_managers import DatasourceManager
        >>> df = pd.DataFrame({"x": [1, 2, 3], "y": [4.0, 5.0, 6.0]})
        >>> context = EphemeralDataContext()
        >>> manager = DatasourceManager(data=df, data_context=context)
        >>> datasource = manager.add_or_update_datasource()
        >>> type(datasource).__name__
        'PandasDatasource'
        >>> datasource.name
        'pandas_datasource'

        Create a datasource for PySpark DataFrame:

        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.appName("example").getOrCreate()
        >>> spark_df = spark.createDataFrame([(1, 2.0), (3, 4.0)], ["id", "value"])
        >>> manager = DatasourceManager(data=spark_df, data_context=context)
        >>> datasource = manager.add_or_update_datasource()
        >>> type(datasource).__name__
        'SparkDFDatasource'
        >>> datasource.name
        'pyspark_datasource'

        Verify datasource registration in context:

        >>> datasources = context.list_datasources()
        >>> len(datasources)
        1
        >>> datasources[0]["name"]
        'pyspark_datasource'
        >>> datasources[0]["class_name"]
        'Datasource'

        Demonstrate idempotency:

        >>> df1 = pd.DataFrame({"a": [1, 2]})
        >>> df2 = pd.DataFrame({"b": [3, 4]})
        >>> manager1 = DatasourceManager(data=df1, data_context=context)
        >>> manager2 = DatasourceManager(data=df2, data_context=context)
        >>> ds1 = manager1.add_or_update_datasource()
        >>> initial_count = len(context.list_datasources())
        >>> ds2 = manager2.add_or_update_datasource()
        >>> final_count = len(context.list_datasources())
        >>> initial_count == final_count
        True

        Create data asset from the datasource:

        >>> manager = DatasourceManager(data=df, data_context=context)
        >>> datasource = manager.add_or_update_datasource()
        >>> data_asset = datasource.add_dataframe_asset(name="my_dataset")
        >>> batch_request = data_asset.build_batch_request(dataframe=df)
        >>> # Now ready to run validations on the batch

        Handle unsupported DataFrame type:

        >>> unsupported_data = [1, 2, 3]  # Plain list, not a DataFrame
        >>> manager = DatasourceManager(data=unsupported_data, data_context=context)
        >>> manager.add_or_update_datasource()
        Traceback (most recent call last):
            ...
        KeyError: 'builtins'

        Use with different contexts:

        >>> from great_expectations.data_context import FileDataContext
        >>> from pathlib import Path
        >>> config_path = Path("/path/to/gx/config")
        >>> file_context = FileDataContext(project_root_dir=config_path)
        >>> manager = DatasourceManager(data=df, data_context=file_context)
        >>> datasource = manager.add_or_update_datasource()
        >>> # Datasource configuration is persisted to great_expectations.yml

        Integrate with validation workflow:

        >>> from adc_toolkit.data.validators.gx.batch_managers import BatchManager
        >>> batch_manager = BatchManager(name="my_data", data=df, data_context=context)
        >>> # BatchManager internally calls add_or_update_datasource()
        >>> # to set up the datasource for validation
        """
        datasource = getattr(self.data_context.sources, self.data_reading_methods[self.datasource_type])(
            name=f"{self.datasource_type}_datasource"
        )
        return datasource
