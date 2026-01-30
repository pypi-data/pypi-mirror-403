"""
Kedro catalog folder structure scaffolding utilities.

This module provides utilities for creating and verifying the required folder
structure for Kedro-based data catalogs. It automates the setup of configuration
directories and template files needed by the ValidatedDataCatalog.

The standard catalog structure consists of:

- base/: Contains catalog.yml and globals.yml for catalog definitions
- local/: Contains credentials.yml and .gitignore for local configuration

This scaffolding approach follows Kedro conventions and ensures that sensitive
credentials are properly excluded from version control.

Functions
---------
catalog_structure_exists
    Verify that all required catalog configuration files are present.
create_catalog_folder_structure
    Create the complete Kedro catalog folder structure with templates.
get_template_content
    Retrieve template file contents for configuration files.

Classes
-------
ScaffoldResult
    Data class containing the results of a scaffold operation.

Notes
-----
The scaffolding utilities use package resources to access template files,
ensuring that the correct structure is created regardless of where the
package is installed.

Examples
--------
Create a new catalog configuration directory:

>>> from adc_toolkit.data.catalogs.kedro.scaffold import create_catalog_folder_structure
>>> result = create_catalog_folder_structure("./config")
>>> print(f"Created {len(result.created_files)} files in {len(result.created_directories)} directories")
Created 4 files in 2 directories

Verify an existing catalog structure:

>>> from adc_toolkit.data.catalogs.kedro.scaffold import catalog_structure_exists
>>> if catalog_structure_exists("./config"):
...     print("Catalog structure is ready")
... else:
...     print("Catalog structure is incomplete")
Catalog structure is ready
"""

from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Literal


@dataclass
class ScaffoldResult:
    """
    Result of a catalog scaffolding operation.

    This data class encapsulates the outcome of creating a catalog folder
    structure, tracking which files and directories were created versus
    which were skipped because they already existed.

    Attributes
    ----------
    created_files : list[Path]
        List of file paths that were successfully created during scaffolding.
        These are new files that did not exist before the operation.
    skipped_files : list[Path]
        List of file paths that were skipped because they already exist.
        Files are only skipped when overwrite=False is specified.
    created_directories : list[Path]
        List of directory paths that were created during scaffolding.
        Parent directories are created as needed.

    Properties
    ----------
    success : bool
        Returns True if at least one file or directory was created,
        indicating the scaffold operation made changes.

    Examples
    --------
    Check the results of a scaffolding operation:

    >>> result = create_catalog_folder_structure("./config")
    >>> if result.success:
    ...     print(f"Scaffolding successful!")
    ...     print(f"Created: {[f.name for f in result.created_files]}")
    ... else:
    ...     print("No changes made - structure already exists")
    Scaffolding successful!
    Created: ['globals.yml', 'catalog.yml', 'credentials.yml', '.gitignore']

    Identify which files were skipped:

    >>> result = create_catalog_folder_structure("./config", overwrite=False)
    >>> if result.skipped_files:
    ...     print(f"Skipped existing files: {[f.name for f in result.skipped_files]}")
    Skipped existing files: ['globals.yml', 'catalog.yml']
    """

    created_files: list[Path] = field(default_factory=list)
    skipped_files: list[Path] = field(default_factory=list)
    created_directories: list[Path] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """
        Determine if the scaffolding operation made any changes.

        Returns
        -------
        bool
            True if at least one file or directory was created during
            the scaffolding operation, False otherwise.

        Notes
        -----
        This property is useful for determining whether the scaffold operation
        was necessary or if the structure already existed. A False value
        indicates that all required files and directories already existed.

        Examples
        --------
        >>> result = create_catalog_folder_structure("./existing_config")
        >>> if not result.success:
        ...     print("Structure already complete - no changes needed")
        """
        return len(self.created_files) > 0 or len(self.created_directories) > 0


FileType = Literal["globals", "catalog", "credentials", "gitignore"]


def get_template_content(template_name: FileType) -> str:
    """
    Retrieve the content of a Kedro catalog configuration template file.

    This function accesses embedded template files from the package resources
    and returns their contents as strings. Templates are used to initialize
    new catalog configurations with sensible defaults and examples.

    Parameters
    ----------
    template_name : {"globals", "catalog", "credentials", "gitignore"}
        The logical name of the template to retrieve. Valid options are:

        - "globals": Global Kedro variables and settings
        - "catalog": Data catalog definitions
        - "credentials": Credentials for data sources (template version)
        - "gitignore": Git ignore rules for the local directory

    Returns
    -------
    str
        The complete text content of the requested template file. This
        content can be written directly to a new configuration file.

    Raises
    ------
    FileNotFoundError
        If the specified template file does not exist in the package
        resources. This typically indicates an invalid template_name
        or a corrupted package installation.
    KeyError
        If the template_name is not one of the valid FileType options.

    Notes
    -----
    The credentials template uses a "_template" suffix in its filename
    (credentials_template.yml) to prevent it from being matched by
    .gitignore patterns when stored in the package. When created in
    the user's project, it is saved as credentials.yml.

    The template files are stored in the package at:
    adc_toolkit.data.catalogs.kedro.templates/

    Examples
    --------
    Retrieve and examine a catalog template:

    >>> content = get_template_content("catalog")
    >>> print(content[:50])
    # This is the data catalog configuration file...

    Get the credentials template for manual customization:

    >>> creds_template = get_template_content("credentials")
    >>> # Customize the template content before writing
    >>> customized = creds_template.replace("example", "production")
    >>> Path("config/local/credentials.yml").write_text(customized)

    Retrieve the gitignore template:

    >>> gitignore = get_template_content("gitignore")
    >>> print(gitignore)
    *
    !.gitignore

    See Also
    --------
    create_catalog_folder_structure : Creates files using these templates
    """
    # Map template names to actual filenames
    # credentials uses _template suffix to avoid being matched by .gitignore
    filename_map: dict[FileType, str] = {
        "globals": "globals.yml",
        "catalog": "catalog.yml",
        "credentials": "credentials_template.yml",
        "gitignore": ".gitignore",
    }
    filename = filename_map[template_name]
    template_path = files("adc_toolkit.data.catalogs.kedro.templates").joinpath(filename)
    return template_path.read_text()


def create_catalog_folder_structure(
    path: str | Path,
    *,
    overwrite: bool = False,
    include_globals: bool = True,
    include_catalog: bool = True,
    include_credentials: bool = True,
) -> ScaffoldResult:
    """
    Create the complete Kedro catalog folder structure with template files.

    This function sets up the standard directory structure and configuration
    files needed for a Kedro-based ValidatedDataCatalog. It creates two
    subdirectories (base/ and local/) with appropriate template files,
    following Kedro conventions where base/ contains version-controlled
    catalog definitions and local/ contains environment-specific credentials.

    The created structure is::

        <path>/
        ├── base/
        │   ├── globals.yml      # Global variables and parameters
        │   └── catalog.yml      # Data catalog definitions
        └── local/
            ├── credentials.yml  # Credentials and secrets
            └── .gitignore       # Excludes credentials from version control

    Parameters
    ----------
    path : str or Path
        Root path where the configuration directory structure should be
        created. Can be absolute or relative. The directory will be created
        if it doesn't exist.
    overwrite : bool, default=False
        If True, overwrite existing files with fresh templates. If False,
        existing files are preserved and added to skipped_files in the
        result. This prevents accidental loss of customized configurations.
    include_globals : bool, default=True
        If True, create base/globals.yml with global parameter templates.
        Set to False if you want to manage globals separately or don't
        need global parameters.
    include_catalog : bool, default=True
        If True, create base/catalog.yml with example catalog entries.
        Set to False if you want to create an empty catalog manually.
    include_credentials : bool, default=True
        If True, create local/credentials.yml and local/.gitignore. The
        .gitignore file ensures credentials are not committed to version
        control. Set to False for projects without sensitive credentials.

    Returns
    -------
    ScaffoldResult
        A result object containing:

        - created_files: List of Path objects for newly created files
        - skipped_files: List of Path objects for existing files (when overwrite=False)
        - created_directories: List of Path objects for newly created directories
        - success: Property indicating if any changes were made

    Raises
    ------
    OSError
        If there is a filesystem error creating directories or writing files,
        such as insufficient permissions or disk space issues.
    PermissionError
        If the process lacks permission to create directories or files at
        the specified path.
    FileNotFoundError
        If template files are missing from the package installation.

    Notes
    -----
    The function uses atomic operations where possible, but partial failure
    may occur if disk space is exhausted mid-operation. In such cases, some
    directories and files may be created while others are not.

    The local/ directory's .gitignore file contains::

        *
        !.gitignore

    This pattern ignores all files in local/ except .gitignore itself,
    protecting credentials from accidental commits.

    If all include_* parameters are False, the function returns immediately
    with an empty ScaffoldResult, creating no directories or files.

    Examples
    --------
    Create a complete catalog structure:

    >>> from pathlib import Path
    >>> result = create_catalog_folder_structure("./config")
    >>> print(f"Created {len(result.created_files)} files")
    Created 4 files
    >>> print(f"Created directories: {[d.name for d in result.created_directories]}")
    Created directories: ['base', 'local']

    Create structure without credentials (for public projects):

    >>> result = create_catalog_folder_structure("./config", include_credentials=False)
    >>> print(f"Files created: {[f.name for f in result.created_files]}")
    Files created: ['globals.yml', 'catalog.yml']

    Overwrite existing configuration with fresh templates:

    >>> result = create_catalog_folder_structure("./config", overwrite=True)
    >>> print(f"Overwrote {len(result.created_files)} existing files")

    Handle existing structure gracefully:

    >>> result = create_catalog_folder_structure("./config")
    >>> if result.skipped_files:
    ...     print(f"Skipped {len(result.skipped_files)} existing files")
    ...     print("Use overwrite=True to replace them")
    Skipped 4 existing files
    Use overwrite=True to replace them

    Create only catalog definition without globals:

    >>> result = create_catalog_folder_structure("./config", include_globals=False)
    >>> files = [f.name for f in result.created_files]
    >>> assert "catalog.yml" in files
    >>> assert "globals.yml" not in files

    Use in a setup script:

    >>> import sys
    >>> result = create_catalog_folder_structure("./config")
    >>> if not result.success:
    ...     print("Catalog structure already exists")
    ...     sys.exit(0)
    ... else:
    ...     print("Catalog structure initialized successfully")
    ...     print("Please edit config/local/credentials.yml with your credentials")

    See Also
    --------
    catalog_structure_exists : Check if catalog structure is already set up
    get_template_content : Retrieve individual template contents
    ValidatedDataCatalog.in_directory : Load a catalog from the created structure
    """
    root_path = Path(path)
    config_path = root_path
    base_path = config_path / "base"
    local_path = config_path / "local"

    result = ScaffoldResult()

    # If no files are to be created, return early
    if not any([include_globals, include_catalog, include_credentials]):
        return result

    # Create directories
    for dir_path in [base_path, local_path]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            result.created_directories.append(dir_path)

    # Define file mappings: (file_path, template_name, should_create)
    files_to_create: list[tuple[Path, FileType]] = []

    if include_globals:
        files_to_create.append((base_path / "globals.yml", "globals"))
    if include_catalog:
        files_to_create.append((base_path / "catalog.yml", "catalog"))
    if include_credentials:
        files_to_create.append((local_path / "credentials.yml", "credentials"))
        files_to_create.append((local_path / ".gitignore", "gitignore"))

    # Create files
    for file_path, template_name in files_to_create:
        if file_path.exists() and not overwrite:
            result.skipped_files.append(file_path)
            continue

        content = get_template_content(template_name)
        file_path.write_text(content)
        result.created_files.append(file_path)

    return result


def catalog_structure_exists(path: str | Path, require_credentials: bool = True) -> bool:
    """
    Verify that the catalog folder structure exists at the specified path.

    This function checks whether all required Kedro catalog configuration
    files are present at the given location. It is useful for validation
    before attempting to load a catalog, or for determining whether
    scaffolding needs to be performed.

    The function verifies the presence of:

    - <path>/base/globals.yml (always required)
    - <path>/base/catalog.yml (always required)
    - <path>/local/credentials.yml (if require_credentials=True)
    - <path>/local/.gitignore (if require_credentials=True)

    Parameters
    ----------
    path : str or Path
        Root path of the configuration directory to check. This should
        be the parent directory containing the base/ and local/
        subdirectories. Can be absolute or relative.
    require_credentials : bool, default=True
        If True, the function requires credentials.yml and .gitignore
        to exist in the local/ directory. Set to False when checking
        structures that don't use credentials (e.g., public projects
        or catalogs that only reference local files).

    Returns
    -------
    bool
        True if all required files exist at their expected locations,
        False if any required file is missing. Missing optional files
        (when require_credentials=False) do not affect the result.

    Notes
    -----
    This function only checks for file existence, not file validity or
    content. It does not verify that YAML files are well-formed or that
    catalog definitions are valid.

    The function does not check for the existence of the parent directories
    (base/ and local/). If the files exist but are in an unexpected
    location, the function returns False.

    Examples
    --------
    Check if a complete catalog structure exists:

    >>> from pathlib import Path
    >>> if catalog_structure_exists("./config"):
    ...     print("Catalog is ready to use")
    ... else:
    ...     print("Need to run scaffolding")
    Catalog is ready to use

    Check structure without requiring credentials:

    >>> exists = catalog_structure_exists("./config", require_credentials=False)
    >>> print(f"Base structure exists: {exists}")
    Base structure exists: True

    Use in a validation function:

    >>> def validate_project_setup(config_path: str) -> bool:
    ...     if not catalog_structure_exists(config_path):
    ...         print(f"Error: Catalog structure missing at {config_path}")
    ...         print("Run: create_catalog_folder_structure(config_path)")
    ...         return False
    ...     return True

    Conditional scaffolding:

    >>> config_path = "./config"
    >>> if not catalog_structure_exists(config_path):
    ...     result = create_catalog_folder_structure(config_path)
    ...     print(f"Created catalog structure: {result.success}")
    ... else:
    ...     print("Using existing catalog structure")

    Check multiple possible locations:

    >>> possible_paths = ["./config", "./conf", "../config"]
    >>> for path in possible_paths:
    ...     if catalog_structure_exists(path, require_credentials=False):
    ...         print(f"Found catalog at: {path}")
    ...         break
    ... else:
    ...     print("No catalog found in any expected location")

    See Also
    --------
    create_catalog_folder_structure : Create the required structure
    ValidatedDataCatalog.in_directory : Load catalog from verified structure
    """
    root_path = Path(path)
    config_path = root_path
    required_files = [
        config_path / "base" / "globals.yml",
        config_path / "base" / "catalog.yml",
    ]
    if require_credentials:
        required_files.append(config_path / "local" / "credentials.yml")
        required_files.append(config_path / "local" / ".gitignore")
    return all(f.exists() for f in required_files)
