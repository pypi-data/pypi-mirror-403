"""
Batch manager module for Great Expectations validation workflow.

This module provides the BatchManager dataclass, which serves as the central
coordination point for batch-based data validation operations. It encapsulates
batch metadata, data references, and Great Expectations context, and handles
the creation of batch requests for downstream validation operations.
"""

from dataclasses import dataclass, field

from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.datasource.fluent import BatchRequest

from adc_toolkit.data.abs import Data
from adc_toolkit.data.validators.gx.batch_managers.datasource_manager import DatasourceManager


@dataclass
class BatchManager:
    """
    Coordinate batch metadata and operations for Great Expectations validation.

    The BatchManager dataclass serves as a central coordination point in the
    Great Expectations (GX) validation workflow. It encapsulates all essential
    metadata about a validation batch, including the dataset name, the data to
    be validated, and the GX data context. Upon initialization, it automatically
    creates a BatchRequest that can be used by downstream validation components
    (expectation strategies, checkpoint managers) to execute validations.

    This class acts as a bridge between raw data and the Great Expectations
    validation engine. It delegates datasource management to DatasourceManager,
    which handles the details of registering pandas or PySpark datasources with
    the GX context, and constructs the BatchRequest that defines how GX should
    access and validate the data.

    The BatchManager is typically instantiated by the validate_dataset function
    and passed to ExpectationAdditionStrategy implementations (which add
    validation rules) and CheckpointManager (which executes validations and
    evaluates results).

    Parameters
    ----------
    name : str
        The logical name identifying this dataset or validation batch. This
        name is used to identify the data asset within the GX datasource and
        is typically used as the basis for naming expectation suites (e.g.,
        "{name}_suite"). Must be a valid identifier string.
    data : Data
        The dataset to be validated. This can be a pandas DataFrame, PySpark
        DataFrame, or any other data structure conforming to the Data protocol.
        The data will be registered with GX as a dataframe asset for validation.
    data_context : AbstractDataContext
        The Great Expectations data context that manages datasources, expectation
        suites, checkpoints, and validation results. This can be an
        EphemeralDataContext (in-memory, for testing or transient workflows),
        FileDataContext (persistent, file-based), or cloud-backed contexts
        (AWS, GCP, Azure). The context provides the validation infrastructure
        and configuration.

    Attributes
    ----------
    name : str
        The logical name of the dataset being validated.
    data : Data
        The dataset to be validated.
    data_context : AbstractDataContext
        The Great Expectations data context managing validation infrastructure.
    batch_request : BatchRequest
        The Great Expectations BatchRequest object created during initialization.
        This request encapsulates the datasource name, data asset name, and
        dataframe reference needed by GX to access and validate the data.
        Automatically created by __post_init__ via create_batch_request().

    See Also
    --------
    DatasourceManager : Manages GX datasource registration for pandas and PySpark data.
    CheckpointManager : Executes validation checkpoints using BatchManager metadata.
    validate_dataset : Main validation function that instantiates BatchManager.
    ExpectationAdditionStrategy : Adds validation expectations using BatchManager.

    Notes
    -----
    The BatchManager uses a dataclass design with automatic initialization via
    __post_init__. The batch_request field is not part of the constructor
    signature (field(init=False)) but is automatically created after the main
    fields are initialized.

    The workflow is as follows:

    1. User calls validate_dataset() with data, name, and strategies
    2. validate_dataset() creates a BatchManager instance
    3. BatchManager.__post_init__() calls create_batch_request()
    4. create_batch_request() delegates to DatasourceManager to register datasource
    5. A data asset is added to the datasource with the specified name
    6. A BatchRequest is built referencing the dataframe
    7. The BatchManager (with batch_request populated) is passed to strategies
    8. ExpectationAdditionStrategy adds expectations to the suite
    9. CheckpointManager runs validation and evaluates results

    The BatchManager supports both pandas and PySpark DataFrames through the
    DatasourceManager abstraction, which automatically detects the dataframe
    type and registers the appropriate GX datasource (PandasDatasource or
    SparkDFDatasource).

    Examples
    --------
    Create a BatchManager for a pandas DataFrame with an ephemeral context:

    >>> import pandas as pd
    >>> from great_expectations.data_context import EphemeralDataContext
    >>> from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
    >>> data = pd.DataFrame(
    ...     {
    ...         "col1": [1, 2, 3],
    ...         "col2": [4.0, 5.0, 6.0],
    ...         "col3": ["a", "b", "c"],
    ...     }
    ... )
    >>> context = EphemeralDataContext()
    >>> batch_manager = BatchManager(
    ...     name="my_dataset",
    ...     data=data,
    ...     data_context=context,
    ... )
    >>> print(batch_manager.batch_request.data_asset_name)
    my_dataset
    >>> print(batch_manager.batch_request.datasource_name)
    pandas_datasource

    Use BatchManager within the full validation workflow:

    >>> from adc_toolkit.data.validators.gx.batch_managers.batch_validation import validate_dataset
    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_suite_lookup_strategy import (
    ...     AutoExpectationSuiteCreation,
    ... )
    >>> from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
    ...     SchemaExpectationAddition,
    ... )
    >>> validated_data = validate_dataset(
    ...     name="my_dataset",
    ...     data=data,
    ...     data_context=context,
    ...     expectation_suite_lookup_strategy=AutoExpectationSuiteCreation(),
    ...     expectation_addition_strategy=SchemaExpectationAddition(),
    ... )

    Access the batch request for custom validation logic:

    >>> batch_request = batch_manager.batch_request
    >>> validator = context.get_validator(batch_request=batch_request, expectation_suite_name="my_dataset_suite")
    >>> validation_result = validator.validate()
    """

    name: str
    data: Data
    data_context: AbstractDataContext
    batch_request: BatchRequest = field(init=False)

    def __post_init__(self) -> None:
        """
        Initialize computed fields after dataclass initialization.

        This method is automatically called by the dataclass machinery after
        __init__ completes. It creates and populates the batch_request field
        by calling create_batch_request(). This two-stage initialization allows
        the batch_request to be automatically computed from the name, data, and
        data_context fields without requiring explicit initialization by the
        caller.

        The method ensures that every BatchManager instance has a valid
        batch_request immediately after construction, ready to be used by
        downstream validation components.

        Notes
        -----
        This method is called automatically and should not be invoked manually.
        It is part of the dataclass lifecycle and implements the deferred
        initialization pattern for computed fields.

        See Also
        --------
        create_batch_request : Creates the BatchRequest for this batch.
        """
        self.batch_request = self.create_batch_request()

    def create_batch_request(self) -> BatchRequest:
        """
        Create a Great Expectations BatchRequest for this validation batch.

        This method orchestrates the creation of a BatchRequest by delegating
        datasource management to DatasourceManager, adding a dataframe asset to
        the datasource, and building a batch request that references the data.

        The process involves:

        1. Instantiate DatasourceManager with the data and context
        2. Add or update the appropriate datasource (pandas or PySpark) in the
           data context based on the detected dataframe type
        3. Add a dataframe asset to the datasource with the specified name
        4. Build and return a BatchRequest linking the data asset to the
           in-memory dataframe

        The resulting BatchRequest can be used by Great Expectations validators,
        checkpoints, and other components to access and validate the data.

        Returns
        -------
        BatchRequest
            A Great Expectations BatchRequest object containing the datasource
            name (e.g., "pandas_datasource" or "pyspark_datasource"), data
            asset name (same as self.name), and a reference to the dataframe.
            This request can be passed to GX validators and checkpoints to
            execute validations.

        Notes
        -----
        This method is called automatically during __post_init__ and typically
        should not be called manually. It delegates the complexity of datasource
        type detection and registration to DatasourceManager, keeping the
        BatchManager logic clean and focused on coordination.

        The datasource is added or updated (not just retrieved) to ensure it
        exists in the data context. If a datasource with the same name already
        exists, GX updates it; otherwise, it creates a new one.

        The dataframe asset is ephemeral and exists only for the duration of
        this validation batch. Each call to create_batch_request() creates a
        new asset with the specified name, which may overwrite previous assets
        with the same name.

        See Also
        --------
        DatasourceManager.add_or_update_datasource : Registers the datasource with GX.

        Examples
        --------
        The create_batch_request method is called automatically, but its behavior
        can be understood through manual usage:

        >>> import pandas as pd
        >>> from great_expectations.data_context import EphemeralDataContext
        >>> from adc_toolkit.data.validators.gx.batch_managers.batch_manager import BatchManager
        >>> data = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        >>> context = EphemeralDataContext()
        >>> batch_manager = BatchManager(name="test_data", data=data, data_context=context)
        >>> # batch_request is automatically created via __post_init__
        >>> batch_request = batch_manager.batch_request
        >>> print(f"Datasource: {batch_request.datasource_name}")
        Datasource: pandas_datasource
        >>> print(f"Asset: {batch_request.data_asset_name}")
        Asset: test_data

        The batch request can be used to get a validator:

        >>> validator = context.get_validator(batch_request=batch_request, expectation_suite_name="test_suite")
        """
        datasource = DatasourceManager(self.data, self.data_context).add_or_update_datasource()
        data_asset = datasource.add_dataframe_asset(name=self.name)
        return data_asset.build_batch_request(dataframe=self.data)
