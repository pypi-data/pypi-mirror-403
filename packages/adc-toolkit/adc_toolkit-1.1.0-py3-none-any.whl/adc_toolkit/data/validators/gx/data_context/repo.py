"""
Create a repo-based data context.

This module provides the `RepoDataContext` class for creating Great Expectations
data contexts that use local filesystem storage. This is the default and recommended
approach for local development, testing, and repository-based projects where all
GX configuration, expectations, checkpoints, and validation results are stored
directly in the project directory structure.

See Also
--------
adc_toolkit.data.validators.gx.data_context.base.BaseDataContext : Protocol defining the data context interface.
adc_toolkit.data.validators.gx.data_context.aws.S3DataContext : AWS S3-based data context.
adc_toolkit.data.validators.gx.data_context.gcp.GCPDataContext : GCP-based data context.
adc_toolkit.data.validators.gx.data_context.azure.AzureDataContext : Azure-based data context.

Notes
-----
The repo-based data context stores all Great Expectations artifacts (expectations,
checkpoints, validation results, etc.) in a local directory structure. This approach
is ideal for:

- Local development and testing
- Version-controlled projects where GX config is checked into git
- Environments without cloud storage access
- Simple, single-machine deployments

The data context uses Great Expectations' `FileDataContext`, which creates a
standard GX directory structure including `expectations/`, `checkpoints/`,
`uncommitted/`, and other directories as needed.
"""

from pathlib import Path

from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.data_context.data_context.file_data_context import FileDataContext


class RepoDataContext:
    """
    Repository-based Great Expectations data context using local filesystem storage.

    This class implements the `BaseDataContext` protocol and provides a factory
    for creating Great Expectations `FileDataContext` instances. It stores all
    GX artifacts (expectations, checkpoints, validation results, etc.) in a local
    directory structure within the project repository.

    The repo-based approach is ideal for local development, testing, and projects
    where configuration is version-controlled. All GX configuration files are
    stored on the local filesystem, making them easy to inspect, version, and
    collaborate on through standard git workflows.

    Parameters
    ----------
    project_config_dir : str or pathlib.Path
        Path to the project configuration directory where Great Expectations
        will store its artifacts. This directory will become the root of the
        GX project structure. If the directory does not exist or is not
        initialized as a GX project, calling `create()` will initialize it
        with the standard GX directory structure.

    Attributes
    ----------
    project_config_dir : str or pathlib.Path
        The project configuration directory path provided during initialization.

    See Also
    --------
    BaseDataContext : Protocol defining the data context interface.
    S3DataContext : AWS S3-based data context for cloud storage.
    GCPDataContext : Google Cloud Platform-based data context.
    AzureDataContext : Azure-based data context.
    great_expectations.data_context.FileDataContext : The underlying GX class used for file-based contexts.

    Notes
    -----
    Directory Structure
    ^^^^^^^^^^^^^^^^^^^
    When `create()` is called, Great Expectations will create a directory
    structure similar to::

        project_config_dir/
        ├── great_expectations.yml       # Main GX configuration
        ├── expectations/                # Expectation suites (JSON)
        ├── checkpoints/                 # Checkpoint configurations (YAML)
        ├── plugins/                     # Custom expectations and plugins
        └── uncommitted/                 # Local-only validation results

    Version Control Considerations
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    The `uncommitted/` directory should typically be excluded from version
    control (add to .gitignore) as it contains validation results and data
    samples that may be large or contain sensitive information. The other
    directories should be committed to enable team collaboration.

    Thread Safety
    ^^^^^^^^^^^^^
    This class is thread-safe for read operations but concurrent write
    operations (creating/modifying expectations or checkpoints) should be
    serialized at the application level.

    Examples
    --------
    Basic usage with a local project directory:

    >>> from adc_toolkit.data.validators.gx.data_context import RepoDataContext
    >>> repo_context = RepoDataContext(project_config_dir="./gx_config")
    >>> data_context = repo_context.create()
    >>> type(data_context).__name__
    'FileDataContext'

    Using with the GX validator factory method:

    >>> from adc_toolkit.data.validators.gx import GXValidator
    >>> validator = GXValidator.in_directory("./gx_config")

    Creating a data context for a typical project structure:

    >>> from pathlib import Path
    >>> config_dir = Path.home() / "projects" / "my_project" / "config" / "gx"
    >>> repo_context = RepoDataContext(project_config_dir=config_dir)
    >>> context = repo_context.create()

    Inspecting the created data context:

    >>> context = RepoDataContext("./gx_config").create()
    >>> context.list_expectation_suite_names()
    ['my_suite', 'another_suite']
    >>> context.list_checkpoints()
    ['checkpoint_1', 'checkpoint_2']
    """

    def __init__(self, project_config_dir: str | Path) -> None:
        """
        Initialize a repository-based data context.

        Parameters
        ----------
        project_config_dir : str or pathlib.Path
            Path to the project configuration directory where Great Expectations
            artifacts will be stored. This directory serves as the root of the
            GX project structure. Can be provided as either a string path or
            a `pathlib.Path` object.

        Examples
        --------
        Initialize with a string path:

        >>> repo_context = RepoDataContext("./config/gx")

        Initialize with a Path object:

        >>> from pathlib import Path
        >>> config_path = Path("./config") / "gx"
        >>> repo_context = RepoDataContext(config_path)

        Initialize with an absolute path:

        >>> repo_context = RepoDataContext("/opt/myapp/config/gx")
        """
        self.project_config_dir = project_config_dir

    def create(self) -> AbstractDataContext:
        """
        Create and return a Great Expectations FileDataContext.

        This method instantiates a Great Expectations `FileDataContext` using
        the configured project directory. If the directory is not already
        initialized as a GX project, this will create the necessary directory
        structure and configuration files.

        The created data context provides access to expectations, checkpoints,
        datasources, and validation capabilities through the Great Expectations API.

        Returns
        -------
        AbstractDataContext
            A Great Expectations data context instance (specifically a
            `FileDataContext`) configured to use the project directory for
            storing all GX artifacts. This context can be used to define
            expectations, run validations, and manage data quality checks.

        Raises
        ------
        FileNotFoundError
            If the parent directory of `project_config_dir` does not exist
            and cannot be created.
        PermissionError
            If the process lacks permissions to create or write to the
            project configuration directory.
        great_expectations.exceptions.DataContextError
            If there are issues with the GX configuration files or project
            structure.

        See Also
        --------
        great_expectations.data_context.FileDataContext.create : The underlying GX method.

        Notes
        -----
        First-Time Initialization
        ^^^^^^^^^^^^^^^^^^^^^^^^^
        When calling this method on a directory that has not been initialized
        as a GX project, Great Expectations will:

        1. Create the project directory if it doesn't exist
        2. Generate a `great_expectations.yml` configuration file
        3. Create subdirectories for expectations, checkpoints, and plugins
        4. Set up the uncommitted directory for local validation results

        Subsequent Calls
        ^^^^^^^^^^^^^^^^
        If the directory is already initialized, this method simply loads the
        existing configuration and returns a data context instance pointing
        to that project.

        Performance Considerations
        ^^^^^^^^^^^^^^^^^^^^^^^^^^
        Creating a data context is relatively lightweight but does involve
        filesystem I/O to read configuration files. For applications that
        perform many validations, consider reusing the same data context
        instance rather than creating a new one for each validation.

        Examples
        --------
        Create a data context and use it for validation:

        >>> from adc_toolkit.data.validators.gx.data_context import RepoDataContext
        >>> repo_context = RepoDataContext("./gx_config")
        >>> context = repo_context.create()
        >>> context.list_datasources()
        []

        Create a context and add a datasource:

        >>> context = RepoDataContext("./gx_config").create()
        >>> datasource_config = {
        ...     "name": "my_datasource",
        ...     "class_name": "Datasource",
        ...     "execution_engine": {"class_name": "PandasExecutionEngine"},
        ...     "data_connectors": {},
        ... }
        >>> context.add_datasource(**datasource_config)

        Create and immediately use in a validation workflow:

        >>> import pandas as pd
        >>> context = RepoDataContext("./gx_config").create()
        >>> df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        >>> batch = context.get_batch_list(
        ...     batch_request={"datasource_name": "my_datasource", "data_asset_name": "my_data"}
        ... )
        """
        return FileDataContext.create(project_root_dir=self.project_config_dir)
