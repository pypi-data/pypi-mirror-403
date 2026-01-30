"""
Filesystem management for Pandera schema script files.

This module provides the FileManager class for managing the creation,
organization, and writing of Pandera schema Python files. It handles
the conversion of schema names (e.g., "schema.table") into properly
structured file paths with subfolders, following a consistent naming
convention for schema file organization.
"""

from dataclasses import dataclass, field
from pathlib import Path

from adc_toolkit.utils.manage_filesystem import (
    check_if_file_exists,
    create_file_in_directory_if_not_exists,
    write_string_to_file,
)


@dataclass
class FileManager:
    """
    Manage Pandera schema script files with automatic path resolution.

    FileManager is a dataclass that handles the creation, organization, and
    writing of Pandera schema Python files. It converts schema names following
    the "schema.table" convention into structured file paths organized in
    subfolders. The class automatically handles directory creation, file
    existence checks, and content writing operations.

    The file naming convention transforms dotted schema names into a folder
    structure. For example, "bronze.users" becomes "bronze/users.py" within
    the configured base path.

    Parameters
    ----------
    name : str
        The fully qualified name of the schema table using dot notation.
        Expected format is "schema.table" where "schema" becomes the
        subfolder name and "table" becomes the filename (with .py extension
        added automatically). Example: "bronze.users" or "silver.transactions".
    path : Path
        The base directory path where schema scripts are stored. All schema
        files will be created as subdirectories and files within this path.
        This should be an absolute path to ensure consistent file resolution.

    Attributes
    ----------
    name : str
        The fully qualified schema table name in dot notation.
    path : Path
        The base directory for schema script storage.
    file_path : Path
        The complete resolved file path including subfolder and filename.
        Automatically computed during initialization by combining the base
        path, schema subfolder, and table filename. Read-only attribute
        set in __post_init__.

    Methods
    -------
    check_if_file_exists()
        Check whether the schema file exists at the computed file path.
    create_directory_and_empty_file()
        Create the directory structure and an empty schema file if needed.
    split_table_name_into_subfolder_and_filename()
        Parse the schema name into subfolder and filename components.
    create_full_path()
        Construct the complete file path from the schema name and base path.
    write_file(string)
        Write content to the schema file, creating directories if needed.

    See Also
    --------
    adc_toolkit.utils.manage_filesystem : Underlying filesystem utilities.

    Notes
    -----
    This class is designed to work within the Pandera schema compilation
    workflow, where schema definitions are stored as Python scripts in an
    organized directory structure. The automatic path resolution ensures
    consistent file organization across the toolkit.

    The class uses the dataclass decorator for automatic initialization and
    representation. The file_path attribute is computed automatically during
    initialization and should not be set manually.

    Examples
    --------
    Create a file manager for a bronze schema table:

    >>> from pathlib import Path
    >>> fm = FileManager(name="bronze.users", path=Path("/data/schemas"))
    >>> print(fm.file_path)
    /data/schemas/bronze/users.py

    Check if the schema file exists and create it if needed:

    >>> if not fm.check_if_file_exists():
    ...     fm.create_directory_and_empty_file()

    Write schema content to the file:

    >>> schema_code = '''
    ... import pandera as pa
    ... schema = pa.DataFrameSchema({"user_id": pa.Column(int)})
    ... '''
    >>> fm.write_file(schema_code)

    Work with nested schema hierarchies:

    >>> fm_nested = FileManager(name="silver.marketing.campaigns", path=Path("/data/schemas"))
    >>> # Note: Current implementation expects single-level nesting only
    """

    name: str
    path: Path
    file_path: Path = field(init=False)

    def __post_init__(self) -> None:
        """
        Initialize the computed file_path attribute after instance creation.

        This post-initialization hook is called automatically after the
        dataclass __init__ method completes. It computes the full file path
        by parsing the schema name and combining it with the base path,
        storing the result in the file_path attribute.

        The method enables automatic path resolution at initialization time,
        ensuring that file_path is always available and consistent with the
        provided name and path attributes.

        Returns
        -------
        None
            This method modifies the instance in-place by setting file_path.

        See Also
        --------
        create_full_path : The method used to compute the file path.

        Notes
        -----
        This is a dataclass lifecycle method that executes automatically
        during instance creation. Users should not call this method manually.

        The file_path attribute is marked with `field(init=False)` to exclude
        it from the generated __init__ signature, as it is derived from other
        attributes rather than provided by the caller.

        Examples
        --------
        The __post_init__ method runs automatically during instantiation:

        >>> fm = FileManager(name="bronze.users", path=Path("/schemas"))
        >>> # __post_init__ has already executed
        >>> assert fm.file_path == Path("/schemas/bronze/users.py")
        """
        self.file_path = self.create_full_path()

    def check_if_file_exists(self) -> bool:
        """
        Check whether the schema file exists at the computed file path.

        This method verifies the existence of the schema file by checking
        the file_path attribute against the filesystem. It is useful for
        conditional logic that determines whether a schema file needs to
        be created or can be read from disk.

        Returns
        -------
        bool
            True if the file exists at file_path, False otherwise. Returns
            False if the path points to a directory rather than a file, or
            if the path does not exist at all.

        See Also
        --------
        create_directory_and_empty_file : Create the file if it does not exist.
        adc_toolkit.utils.manage_filesystem.check_if_file_exists : Underlying utility function.

        Notes
        -----
        This method delegates to the underlying filesystem utility function
        for the actual existence check. It operates on the file_path
        attribute that was computed during initialization.

        The method does not raise exceptions if the file does not exist;
        it simply returns False, making it safe for conditional checks.

        Examples
        --------
        Check before creating a new schema file:

        >>> fm = FileManager(name="bronze.users", path=Path("/schemas"))
        >>> if not fm.check_if_file_exists():
        ...     print("File does not exist, creating...")
        ...     fm.create_directory_and_empty_file()

        Verify file existence after writing:

        >>> fm.write_file("schema_content")
        >>> assert fm.check_if_file_exists() is True
        """
        return check_if_file_exists(self.file_path)

    def create_directory_and_empty_file(self) -> None:
        """
        Create the directory structure and an empty schema file if needed.

        This method ensures that the complete directory path exists and
        creates an empty file at the computed file_path location. If the
        directory structure does not exist, it will be created recursively.
        If the file already exists, this method does nothing, making it
        safe to call idempotently.

        This is typically used to initialize a new schema file location
        before writing schema content, ensuring that the filesystem is
        properly prepared for the write operation.

        Returns
        -------
        None
            This method modifies the filesystem but does not return a value.

        See Also
        --------
        check_if_file_exists : Check file existence before creating.
        write_file : Write content to the schema file.
        adc_toolkit.utils.manage_filesystem.create_file_in_directory_if_not_exists : Underlying utility.

        Notes
        -----
        The method creates directories with default permissions. Parent
        directories are created recursively as needed, similar to the
        `mkdir -p` command in Unix systems.

        If the file already exists, no action is taken and no exception is
        raised. This idempotent behavior makes it safe to call multiple times.

        Examples
        --------
        Initialize a new schema file location:

        >>> from pathlib import Path
        >>> fm = FileManager(name="bronze.users", path=Path("/schemas"))
        >>> fm.create_directory_and_empty_file()
        >>> # Directory /schemas/bronze/ and file users.py now exist

        Safe to call multiple times:

        >>> fm.create_directory_and_empty_file()  # No error if already exists
        >>> assert fm.check_if_file_exists() is True

        Typical workflow for new schema files:

        >>> fm = FileManager(name="silver.products", path=Path("/schemas"))
        >>> if not fm.check_if_file_exists():
        ...     fm.create_directory_and_empty_file()
        ...     fm.write_file("# New schema file")
        """
        create_file_in_directory_if_not_exists(self.file_path)

    def split_table_name_into_subfolder_and_filename(self) -> tuple[str, str]:
        """
        Parse the schema name into subfolder and filename components.

        This method implements the file naming convention by splitting the
        fully qualified schema name (in "schema.table" format) into two
        components: the subfolder name (schema part) and the filename
        (table part with .py extension).

        The naming convention follows a simple pattern:
        - Everything before the first dot becomes the subfolder name
        - Everything after the first dot becomes the base filename
        - The .py extension is automatically appended to the filename

        Returns
        -------
        subfolder_name : str
            The name of the subfolder corresponding to the schema part of
            the qualified name. This is the portion before the first dot.
        filename : str
            The Python filename including the .py extension. This is derived
            from the table part of the qualified name (after the first dot).

        See Also
        --------
        create_full_path : Uses this method to construct the complete path.

        Notes
        -----
        This implementation expects exactly one dot in the name, separating
        the schema and table components. Names with multiple dots will use
        only the first dot as the separator, with all subsequent parts
        becoming part of the filename.

        For example:
        - "bronze.users" -> ("bronze", "users.py")
        - "silver.fact.sales" -> ("silver", "fact.sales.py")

        The method does not validate the format of the name. If the name
        does not contain a dot, calling this method will raise an IndexError.

        Raises
        ------
        IndexError
            If the name does not contain a dot separator. The method expects
            names in the format "category.dataset" and will fail when splitting
            names without a dot.

        Examples
        --------
        Parse a standard schema name:

        >>> fm = FileManager(name="bronze.users", path=Path("/schemas"))
        >>> subfolder, filename = fm.split_table_name_into_subfolder_and_filename()
        >>> print(f"Subfolder: {subfolder}, Filename: {filename}")
        Subfolder: bronze, Filename: users.py

        Parse a name with multiple dots:

        >>> fm = FileManager(name="silver.fact.sales", path=Path("/schemas"))
        >>> subfolder, filename = fm.split_table_name_into_subfolder_and_filename()
        >>> print(f"Subfolder: {subfolder}, Filename: {filename}")
        Subfolder: silver, Filename: fact.sales.py

        The method is used internally for path construction:

        >>> fm = FileManager(name="gold.reports", path=Path("/schemas"))
        >>> full_path = fm.create_full_path()
        >>> print(full_path)
        /schemas/gold/reports.py
        """
        table_name_splitted = self.name.split(".")
        subfolder_name = table_name_splitted[0]
        filename = table_name_splitted[1] + ".py"
        return subfolder_name, filename

    def create_full_path(self) -> Path:
        """
        Construct the complete file path from the schema name and base path.

        This method combines the base path with the parsed schema name
        components to create a fully qualified Path object pointing to the
        schema file location. It uses the naming convention implemented in
        split_table_name_into_subfolder_and_filename() to organize files
        into subfolders based on the schema name.

        The resulting path follows the structure:
        base_path / schema_name / table_name.py

        Returns
        -------
        Path
            The complete absolute or relative path to the schema file,
            including the subfolder structure and filename with .py
            extension. This path object can be used for all filesystem
            operations.

        See Also
        --------
        split_table_name_into_subfolder_and_filename : Parses the schema name.
        __post_init__ : Calls this method during initialization.

        Notes
        -----
        This method is called automatically during instance initialization
        via __post_init__ to set the file_path attribute. It can also be
        called directly if needed, though this is uncommon in typical usage.

        The method uses the Path division operator (/) to construct the
        path in a platform-independent manner, ensuring compatibility across
        Windows, Linux, and macOS systems.

        Examples
        --------
        The method is called automatically during initialization:

        >>> from pathlib import Path
        >>> fm = FileManager(name="bronze.users", path=Path("/data/schemas"))
        >>> print(fm.file_path)  # Already computed by __post_init__
        /data/schemas/bronze/users.py

        The path structure follows the schema naming convention:

        >>> fm = FileManager(name="silver.transactions", path=Path("/schemas"))
        >>> print(fm.create_full_path())
        /schemas/silver/transactions.py

        Works with relative paths:

        >>> fm = FileManager(name="gold.reports", path=Path("./schemas"))
        >>> print(fm.create_full_path())
        schemas/gold/reports.py

        The resulting path is a proper Path object:

        >>> path = fm.create_full_path()
        >>> print(type(path))
        <class 'pathlib.Path'>
        >>> print(path.name)  # Filename only
        reports.py
        >>> print(path.parent)  # Parent directory
        schemas/gold
        """
        subfolder_name, filename = self.split_table_name_into_subfolder_and_filename()
        return self.path / subfolder_name / filename

    def write_file(self, string: str) -> None:
        """
        Write content to the schema file at the computed file path.

        This method writes the provided string content to the schema file,
        overwriting any existing content. The file and its parent directories
        must already exist; use create_directory_and_empty_file() first if
        the file location has not been initialized.

        The method is typically used to save generated or manually crafted
        Pandera schema definitions to disk as Python source files.

        Parameters
        ----------
        string : str
            The content to write to the file. This is typically Python source
            code containing Pandera schema definitions, but can be any string
            content. The string should include proper Python syntax if it is
            intended to be a valid schema module. No validation is performed
            on the content before writing.

        Returns
        -------
        None
            This method performs a side effect (file writing) and does not
            return a value.

        See Also
        --------
        create_directory_and_empty_file : Initialize the file location first.
        check_if_file_exists : Verify file existence.
        adc_toolkit.utils.manage_filesystem.write_string_to_file : Underlying utility.

        Notes
        -----
        This method overwrites the entire file content if the file already
        exists. There is no append mode; any previous content is replaced.

        The method delegates to the underlying filesystem utility for the
        actual write operation. It does not create parent directories; ensure
        they exist by calling create_directory_and_empty_file() first.

        The content is written using the system's default text encoding
        (typically UTF-8). No explicit encoding parameter is supported at
        this level.

        Examples
        --------
        Write a simple schema definition:

        >>> from pathlib import Path
        >>> fm = FileManager(name="bronze.users", path=Path("/schemas"))
        >>> schema_code = '''import pandera as pa
        ...
        ... schema = pa.DataFrameSchema({
        ...     "user_id": pa.Column(int, nullable=False),
        ...     "username": pa.Column(str),
        ... })
        ... '''
        >>> fm.create_directory_and_empty_file()
        >>> fm.write_file(schema_code)

        Overwrite existing content:

        >>> updated_schema = '''import pandera as pa
        ...
        ... schema = pa.DataFrameSchema({
        ...     "user_id": pa.Column(int, nullable=False),
        ...     "username": pa.Column(str),
        ...     "email": pa.Column(str, nullable=True),
        ... })
        ... '''
        >>> fm.write_file(updated_schema)  # Replaces previous content

        Complete workflow for a new schema file:

        >>> fm = FileManager(name="silver.products", path=Path("/schemas"))
        >>> if not fm.check_if_file_exists():
        ...     fm.create_directory_and_empty_file()
        >>> fm.write_file("import pandera as pa\\n\\nschema = pa.DataFrameSchema({})")
        """
        write_string_to_file(string, self.file_path)
