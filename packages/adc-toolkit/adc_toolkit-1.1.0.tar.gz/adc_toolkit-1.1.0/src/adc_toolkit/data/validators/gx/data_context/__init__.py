"""
Data context factory implementations for Great Expectations.

This module provides factory classes for creating Great Expectations (GX) data contexts
with different storage backends. A data context in GX is the primary entry point for
managing configuration, expectation suites, validation results, checkpoints, and data
documentation. The factory pattern enables runtime selection of storage backends
(local file system, AWS S3, GCP Cloud Storage, Azure Blob Storage) without changing
client code.

Data contexts serve as the central coordination point for all Great Expectations
operations:

- **Configuration Management**: Store and retrieve GX project configuration
- **Expectation Suite Storage**: Persist and version expectation suites
- **Validation Results**: Store historical validation outcomes
- **Checkpoint Configuration**: Define and manage validation checkpoints
- **Data Documentation**: Generate and serve data docs sites
- **Datasource Management**: Configure connections to data sources

The module implements the BaseDataContext protocol through multiple backend-specific
factory classes, each optimized for a particular storage infrastructure. All factories
return AbstractDataContext instances that provide a consistent API regardless of the
underlying storage mechanism.

Classes
-------
BaseDataContext
    Protocol defining the factory interface for creating GX data contexts. All
    concrete factory implementations must implement the `create()` method that
    returns a configured AbstractDataContext instance.
RepoDataContext
    Factory for creating file system-based data contexts that store configuration
    and artifacts in a local directory structure. Suitable for development,
    single-machine deployments, and version-controlled GX projects.
S3DataContext
    Factory for creating AWS S3-backed data contexts that store all GX artifacts
    in S3 buckets. Suitable for cloud-native deployments on AWS with distributed
    teams and scalable storage requirements.
GCPDataContext
    Factory for creating Google Cloud Storage (GCS)-backed data contexts that
    store artifacts in GCS buckets. Suitable for GCP-based deployments with
    integration into Google Cloud Platform services.
AzureDataContext
    Factory for creating Azure Blob Storage-backed data contexts that store
    artifacts in Azure Storage containers. Suitable for Azure-based deployments
    with integration into Microsoft Azure services.

See Also
--------
adc_toolkit.data.validators.gx.gx_validator : GXValidator that uses data contexts for validation
adc_toolkit.data.validators.gx.batch_managers : Batch managers that operate on data contexts
great_expectations.data_context.AbstractDataContext : GX abstract data context interface
great_expectations.data_context.EphemeralDataContext : In-memory data context for testing
great_expectations.data_context.FileDataContext : File-based data context implementation

Notes
-----
**Factory Pattern Benefits:**

The factory pattern provides several advantages for data context creation:

1. **Decoupling**: Separates data context creation from usage, enabling dependency
   injection and improved testability.

2. **Runtime Configuration**: Allows storage backend selection based on environment
   variables, configuration files, or runtime conditions.

3. **Consistent Interface**: All factories return AbstractDataContext instances,
   ensuring consistent usage patterns across different backends.

4. **Easy Mocking**: Factories can be easily mocked for unit testing without
   requiring actual storage backends.

**Storage Backend Selection:**

Choose a storage backend based on your deployment environment and requirements:

- **RepoDataContext (Local File System)**:
  - Best for: Development, testing, single-machine deployments
  - Advantages: Simple setup, fast access, easy debugging, version control friendly
  - Limitations: Not suitable for distributed teams or cloud-native architectures

- **S3DataContext (AWS S3)**:
  - Best for: AWS cloud deployments, distributed teams, high availability requirements
  - Advantages: Scalable storage, high availability, IAM integration, versioning support
  - Considerations: Requires AWS credentials, network latency for access

- **GCPDataContext (Google Cloud Storage)**:
  - Best for: GCP cloud deployments, integration with GCP services
  - Advantages: Scalable storage, IAM integration, lifecycle management
  - Considerations: Requires GCP credentials, network latency for access

- **AzureDataContext (Azure Blob Storage)**:
  - Best for: Azure cloud deployments, integration with Azure services
  - Advantages: Scalable storage, AAD integration, lifecycle management
  - Considerations: Requires Azure credentials, network latency for access

**Data Context Contents:**

A data context manages several types of artifacts:

1. **great_expectations.yml**: Main configuration file defining datasources, stores,
   and validation operators.

2. **Expectation Suites**: JSON files defining data quality expectations for datasets.

3. **Checkpoints**: YAML files defining validation configurations that bundle batch
   requests and expectation suites.

4. **Validation Results**: JSON files containing outcomes of validation runs.

5. **Data Docs**: HTML documentation generated from expectations and validation results.

**Thread Safety:**

Data context instances are generally not thread-safe, especially file-based contexts
that may have file locking issues. For concurrent validation workflows, consider:

- Using separate data context instances per thread
- Employing cloud-based contexts designed for concurrent access
- Implementing external synchronization mechanisms

**Performance Considerations:**

- **Local File System**: Fastest access, minimal latency, suitable for development
- **Cloud Storage**: Higher latency due to network I/O, suitable for distributed deployments
- **Context Creation Overhead**: Creating contexts involves loading configuration;
  consider caching contexts when possible
- **Suite Operations**: Loading/saving expectation suites incurs storage I/O costs

**Configuration Management:**

All factory implementations support configuration through:

- Constructor parameters (explicit configuration)
- Environment variables (for credentials and paths)
- Configuration files (for complex setups)
- Default values (for common scenarios)

Examples
--------
Creating a local file system-based data context:

>>> from adc_toolkit.data.validators.gx.data_context import RepoDataContext
>>> factory = RepoDataContext(root_directory="./gx_config")
>>> context = factory.create()
>>> context.list_expectation_suite_names()
['customer_suite', 'sales_suite']

Creating an AWS S3-backed data context:

>>> from adc_toolkit.data.validators.gx.data_context import S3DataContext
>>> factory = S3DataContext(
...     bucket_name="my-gx-bucket",
...     prefix="environments/production/gx/",
... )
>>> context = factory.create()
>>> # Configuration and suites are stored in S3
>>> context.run_checkpoint(checkpoint_name="daily_validation")

Creating a GCP Cloud Storage-backed data context:

>>> from adc_toolkit.data.validators.gx.data_context import GCPDataContext
>>> factory = GCPDataContext(
...     bucket_name="my-gx-bucket",
...     prefix="gx/",
...     project="my-gcp-project",
... )
>>> context = factory.create()

Creating an Azure Blob Storage-backed data context:

>>> from adc_toolkit.data.validators.gx.data_context import AzureDataContext
>>> factory = AzureDataContext(
...     container_name="gx-container",
...     account_name="mystorageaccount",
...     prefix="gx/",
... )
>>> context = factory.create()

Using dependency injection with the BaseDataContext protocol:

>>> def validate_data(factory: BaseDataContext, data, suite_name: str):
...     '''Validate data using any data context backend.'''
...     context = factory.create()
...     # Use context for validation
...     validator = context.get_validator(...)
...     return validator.validate()
>>>
>>> # Production with S3
>>> result = validate_data(S3DataContext("prod-bucket"), df, "prod_suite")
>>>
>>> # Development with local files
>>> result = validate_data(RepoDataContext("./gx"), df, "dev_suite")

Environment-based factory selection:

>>> import os
>>> environment = os.getenv("ENVIRONMENT", "development")
>>> if environment == "production":
...     factory = S3DataContext(bucket_name=os.getenv("GX_BUCKET"))
... elif environment == "staging":
...     factory = GCPDataContext(bucket_name=os.getenv("GX_BUCKET"))
... else:
...     factory = RepoDataContext(root_directory="./gx")
>>> context = factory.create()

Testing with mock factory:

>>> from unittest.mock import MagicMock
>>> class MockDataContextFactory:
...     def create(self):
...         return MagicMock(spec=AbstractDataContext)
>>> mock_factory = MockDataContextFactory()
>>> result = validate_data(mock_factory, test_df, "test_suite")
"""

from adc_toolkit.data.validators.gx.data_context.aws import S3DataContext
from adc_toolkit.data.validators.gx.data_context.azure import AzureDataContext
from adc_toolkit.data.validators.gx.data_context.base import BaseDataContext
from adc_toolkit.data.validators.gx.data_context.gcp import GCPDataContext
from adc_toolkit.data.validators.gx.data_context.repo import RepoDataContext


__all__ = [
    "AzureDataContext",
    "BaseDataContext",
    "GCPDataContext",
    "RepoDataContext",
    "S3DataContext",
]
