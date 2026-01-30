"""
Factory functions for creating default catalog and validator instances.

This module provides factory functions that return sensible default implementations
of the data catalog and data validator abstractions used throughout the adc-toolkit.
These defaults follow a priority-based selection strategy and use lazy imports to
avoid requiring all optional dependencies.

Default Selection Logic
-----------------------
**Data Catalog**: Always returns ``KedroDataCatalog`` if the kedro package is
installed. This provides YAML-based configuration and supports multiple data
formats (CSV, Parquet, JSON, etc.).

**Data Validator**: Follows a priority hierarchy:
    1. ``GXValidator`` (Great Expectations) - preferred default if installed
    2. ``PanderaValidator`` (Pandera) - fallback if GX is not installed
    3. ``ImportError`` - raised if neither validation package is available

The lazy import mechanism ensures that only the actually-used implementation is
imported, allowing users to install only the optional dependencies they need.

Functions
---------
default_catalog(config_path)
    Return the default data catalog implementation (KedroDataCatalog).
default_validator(config_path)
    Return the default data validator implementation (GX or Pandera).

See Also
--------
adc_toolkit.data.abs.DataCatalog : Abstract base class for data catalogs.
adc_toolkit.data.abs.DataValidator : Abstract base class for data validators.
adc_toolkit.data.ValidatedDataCatalog : Main validated data catalog abstraction.

Notes
-----
These factory functions are primarily used by ``ValidatedDataCatalog.in_directory()``
to automatically construct a validated catalog with sensible defaults when the user
doesn't explicitly specify catalog or validator implementations.

Users can always bypass these defaults by directly instantiating specific
implementations (e.g., ``KedroDataCatalog``, ``GXValidator``, ``PanderaValidator``,
or ``NoValidator``).

Examples
--------
The default factories are typically used indirectly through ValidatedDataCatalog:

>>> from adc_toolkit.data import ValidatedDataCatalog
>>> catalog = ValidatedDataCatalog.in_directory("config/")
>>> # This uses default_catalog() and default_validator() internally

Direct usage of the factory functions:

>>> from adc_toolkit.data.default_attributes import default_catalog, default_validator
>>> catalog = default_catalog("config/")
>>> validator = default_validator("config/")
>>> # Manually construct ValidatedDataCatalog with defaults
>>> from adc_toolkit.data import ValidatedDataCatalog
>>> validated_catalog = ValidatedDataCatalog(catalog, validator)
"""

import warnings
from importlib.util import find_spec
from pathlib import Path

from adc_toolkit.data.abs import DataCatalog, DataValidator


def default_catalog(config_path: str | Path) -> DataCatalog:
    """
    Return the default data catalog implementation initialized from configuration.

    This factory function provides the default ``DataCatalog`` implementation for
    the adc-toolkit. It uses a lazy import mechanism to check for the kedro package
    and returns a ``KedroDataCatalog`` instance if available.

    The function performs runtime package detection using ``importlib.util.find_spec``
    to avoid hard dependencies on kedro. This allows users to install only the
    catalog implementations they need.

    Parameters
    ----------
    config_path : str or pathlib.Path
        Path to the configuration directory containing the data catalog YAML file.
        For ``KedroDataCatalog``, this directory should contain a ``catalog.yaml``
        file that defines dataset configurations in Kedro format. The path can be
        either absolute or relative to the current working directory.

    Returns
    -------
    DataCatalog
        An instance of ``KedroDataCatalog`` initialized with the configuration
        found in the specified directory. The returned object implements the
        ``DataCatalog`` abstract interface, providing ``load()`` and ``save()``
        methods for data I/O operations.

    Raises
    ------
    ImportError
        If the kedro package is not installed. The error message provides
        installation instructions using the uv package manager (formerly poetry).
        Users can install kedro by running ``uv sync --group kedro`` or implement
        their own custom ``DataCatalog`` subclass.

    See Also
    --------
    adc_toolkit.data.catalogs.kedro.KedroDataCatalog : The Kedro-based catalog implementation.
    adc_toolkit.data.abs.DataCatalog : Abstract base class for data catalogs.
    adc_toolkit.data.ValidatedDataCatalog : Validated catalog using this default.

    Notes
    -----
    **Lazy Import Mechanism**: The function uses ``importlib.util.find_spec`` to
    check for kedro's availability before importing. This allows the module to be
    imported even when kedro is not installed, with the ImportError only raised
    when the function is actually called.

    **Alternative Implementations**: Users who don't want to use Kedro can:
        1. Implement a custom ``DataCatalog`` subclass
        2. Directly instantiate their catalog and pass it to ``ValidatedDataCatalog``

    **Configuration Format**: The KedroDataCatalog expects a ``catalog.yaml`` file
    in the specified directory. See the Kedro documentation for the full
    specification of the catalog configuration format.

    Examples
    --------
    Basic usage to get a default catalog:

    >>> from adc_toolkit.data.default_attributes import default_catalog
    >>> catalog = default_catalog("path/to/config")
    >>> # catalog is now a KedroDataCatalog instance
    >>> df = catalog.load("my_dataset")

    Using with ValidatedDataCatalog (typical usage pattern):

    >>> from adc_toolkit.data import ValidatedDataCatalog
    >>> validated_cat = ValidatedDataCatalog.in_directory("config/")
    >>> # This internally calls default_catalog("config/")

    Handling the ImportError when kedro is not installed:

    >>> try:
    ...     catalog = default_catalog("config/")
    ... except ImportError as e:
    ...     print("Kedro not installed, using custom catalog")
    ...     catalog = MyCustomCatalog("config/")

    Working with Path objects:

    >>> from pathlib import Path
    >>> config_dir = Path(__file__).parent / "config"
    >>> catalog = default_catalog(config_dir)
    """
    is_kedro_installed = find_spec("kedro") is not None
    if not is_kedro_installed:
        raise ImportError(
            "Default data catalog is KedroDataCatalog. "
            "You must install kedro to use KedroDataCatalog. "
            "Run `uv sync --group kedro` to do so."
            "Alternatively, you can implement your own data catalog."
        )

    from adc_toolkit.data.catalogs.kedro import KedroDataCatalog

    return KedroDataCatalog(config_path)


def default_validator(config_path: str | Path) -> DataValidator:
    """
    Return the default data validator implementation with priority-based selection.

    This factory function provides the default ``DataValidator`` implementation for
    the adc-toolkit by attempting to load validation libraries in priority order.
    It implements a fallback chain: Great Expectations (preferred) → Pandera
    (fallback) → ImportError (if neither is available).

    The function uses lazy imports and runtime package detection to check for
    available validation libraries, allowing users to install only the validator
    they prefer. When Great Expectations is not available but Pandera is, a
    warning is issued to inform users they are using the fallback implementation.

    Priority Selection Logic
    ------------------------
    1. **GXValidator (Great Expectations)**: Preferred default. Provides comprehensive
       data validation with extensive built-in expectations, profiling capabilities,
       and data documentation features.

    2. **PanderaValidator (Pandera)**: Fallback option. Provides DataFrame schema
       validation with a more lightweight, Pythonic API. Used automatically when
       Great Expectations is not installed.

    3. **ImportError**: Raised when neither validation library is available, with
       detailed installation instructions.

    Parameters
    ----------
    config_path : str or pathlib.Path
        Path to the configuration directory containing validator configuration files.
        The expected file structure depends on the validator:

        - **GXValidator**: Expects a Great Expectations project structure with
          ``great_expectations.yml`` or expectations suite configurations.
        - **PanderaValidator**: Expects Pandera schema definition files (Python
          modules or YAML files depending on configuration).

        The path can be either absolute or relative to the current working directory.

    Returns
    -------
    DataValidator
        An instance of either ``GXValidator`` or ``PanderaValidator`` (in priority
        order), initialized with the configuration found in the specified directory.
        The returned object implements the ``DataValidator`` abstract interface,
        providing ``validate()`` methods for data quality checks.

    Raises
    ------
    ImportError
        Raised when neither the great_expectations nor pandera packages are
        installed. The error message provides detailed installation instructions
        for both options using the uv package manager, and also mentions the
        alternative of implementing a custom validator or using ``NoValidator``
        (though the latter is not recommended for production use).

    Warns
    -----
    UserWarning
        Issued when Great Expectations is not installed but Pandera is available.
        This warning informs users that they are using the fallback validator
        implementation rather than the preferred default. The warning includes
        stacklevel=2 to show the calling code location rather than the factory
        function itself.

    See Also
    --------
    adc_toolkit.data.validators.gx.GXValidator : Great Expectations validator implementation.
    adc_toolkit.data.validators.pandera.PanderaValidator : Pandera validator implementation.
    adc_toolkit.data.validators.no_validator.NoValidator : No-op validator (not recommended).
    adc_toolkit.data.abs.DataValidator : Abstract base class for data validators.
    adc_toolkit.data.ValidatedDataCatalog : Validated catalog using this default.

    Notes
    -----
    **Lazy Import Mechanism**: The function uses ``importlib.util.find_spec`` to
    check for package availability before importing. This allows the module to be
    imported even when validation libraries are not installed, with the ImportError
    only raised when the function is actually called.

    **Installation Options**: Users should install the validation library that best
    fits their needs:

    - For comprehensive validation and data documentation: ``uv sync --group gx``
    - For lightweight DataFrame validation: ``uv sync --group pandera``
    - For both (if needed): ``uv sync --group gx --group pandera``

    **Alternative Implementations**: Users who don't want to use the defaults can:

    1. Implement a custom ``DataValidator`` subclass
    2. Use the ``NoValidator`` class (bypasses all validation, not recommended)
    3. Directly instantiate a specific validator and pass it to ``ValidatedDataCatalog``

    **Warning Behavior**: The fallback warning uses ``stacklevel=2`` to ensure the
    warning appears to originate from the user's code that called this function,
    not from within the factory function itself. This makes it easier for users
    to identify where the fallback is being triggered.

    Examples
    --------
    Basic usage to get a default validator:

    >>> from adc_toolkit.data.default_attributes import default_validator
    >>> validator = default_validator("path/to/config")
    >>> # validator is either GXValidator or PanderaValidator
    >>> validated_df = validator.validate("my_dataset", df)

    Using with ValidatedDataCatalog (typical usage pattern):

    >>> from adc_toolkit.data import ValidatedDataCatalog
    >>> validated_cat = ValidatedDataCatalog.in_directory("config/")
    >>> # This internally calls default_validator("config/")
    >>> df = validated_cat.load("my_dataset")  # Validates after loading

    Handling the fallback warning:

    >>> import warnings
    >>> warnings.filterwarnings("ignore", message=".*PanderaValidator.*")
    >>> validator = default_validator("config/")
    >>> # Warning is suppressed if only Pandera is installed

    Explicitly choosing a validator to avoid the default behavior:

    >>> from adc_toolkit.data.validators.pandera import PanderaValidator
    >>> from adc_toolkit.data.validators.gx import GXValidator
    >>> # Choose GXValidator explicitly
    >>> validator = GXValidator.in_directory("config/")

    Handling the ImportError when no validators are installed:

    >>> from adc_toolkit.data.validators.no_validator import NoValidator
    >>> try:
    ...     validator = default_validator("config/")
    ... except ImportError:
    ...     print("No validators installed, using NoValidator")
    ...     validator = NoValidator()

    Working with Path objects:

    >>> from pathlib import Path
    >>> config_dir = Path(__file__).parent / "config"
    >>> validator = default_validator(config_dir)
    """
    is_great_expectations_installed = find_spec("great_expectations") is not None
    is_pandera_installed = find_spec("pandera") is not None

    if is_great_expectations_installed:
        from adc_toolkit.data.validators.gx import GXValidator

        return GXValidator.in_directory(config_path)
    elif is_pandera_installed:
        warnings.warn(
            "Default data validator is GXValidator. "
            "Great Expectations is not installed. "
            "Using PanderaValidator instead.",
            stacklevel=2,
        )
        from adc_toolkit.data.validators.pandera import PanderaValidator

        return PanderaValidator.in_directory(config_path)
    else:
        raise ImportError(
            "Default data validators are GXValidator and PanderaValidator. "
            "You must install either great_expectations or pandera to use them. "
            "Neither package is installed. "
            "Run `uv sync --group gx` or "
            "`uv sync --group pandera` to do so. "
            "Alternatively, you can implement your own data validator. "
            "If you don't want to validate data, use NoValidator class (not recommended)."
        )
