"""Pandera validation parameters.

This module defines configuration parameters for Pandera-based data validation
within the adc-toolkit framework. The PanderaParameters dataclass encapsulates
settings that control validation behavior, particularly error handling strategies.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class PanderaParameters:
    """
    Configuration parameters for Pandera data validation.

    This immutable dataclass encapsulates configuration options that control
    how Pandera validates DataFrames within the adc-toolkit validation workflow.
    It is designed to be passed to PanderaValidator instances to customize
    validation behavior.

    The primary configuration option controls error collection strategy:
    whether to fail fast on the first validation error or to collect all
    validation errors before raising an exception. Lazy validation is
    recommended for production workflows as it provides comprehensive
    error reporting, making it easier to fix all issues in a single pass.

    This class is immutable (frozen) to ensure validation parameters remain
    consistent throughout the validation lifecycle and to enable safe
    sharing across multiple validation operations.

    Attributes
    ----------
    lazy : bool, default=True
        Controls the validation error collection strategy.

        - If True (default): Collects all validation errors across all
          rows and columns before raising a SchemaErrors exception. This
          provides comprehensive error reporting, showing all violations
          in a single validation run.
        - If False: Raises a SchemaError immediately upon encountering
          the first validation failure. This "fail-fast" mode is useful
          for debugging or when you want to fix errors incrementally.

        The lazy parameter is passed directly to Pandera's
        `DataFrameSchema.validate()` method.

    See Also
    --------
    PanderaValidator : Validator that uses these parameters for data validation.
    pandera.DataFrameSchema.validate : Underlying Pandera validation method
        that receives the lazy parameter.

    Notes
    -----
    This dataclass is configured with the following features:

    - **frozen=True**: Makes instances immutable after creation. Attempting
      to modify attributes after instantiation raises FrozenInstanceError.
    - **slots=True**: Uses __slots__ for memory efficiency and faster
      attribute access by preventing dynamic attribute creation.
    - **kw_only=True**: Requires all parameters to be specified as keyword
      arguments, improving code clarity and preventing positional argument
      errors.

    The immutability design ensures that validation parameters cannot be
    accidentally modified during the validation process, promoting
    predictable and reproducible validation behavior.

    Examples
    --------
    Create a PanderaParameters instance with default lazy validation:

    >>> from adc_toolkit.data.validators.pandera import PanderaParameters
    >>> params = PanderaParameters()
    >>> params.lazy
    True

    Create parameters for fail-fast validation:

    >>> params_strict = PanderaParameters(lazy=False)
    >>> params_strict.lazy
    False

    Use with PanderaValidator for comprehensive error reporting:

    >>> from adc_toolkit.data.validators.pandera import PanderaValidator
    >>> validator = PanderaValidator(config_path="config/validators", parameters=PanderaParameters(lazy=True))

    Use with PanderaValidator for fail-fast debugging:

    >>> validator_debug = PanderaValidator(config_path="config/validators", parameters=PanderaParameters(lazy=False))

    Demonstrate immutability (frozen dataclass):

    >>> params = PanderaParameters()
    >>> params.lazy = False  # doctest: +SKIP
    Traceback (most recent call last):
        ...
    dataclasses.FrozenInstanceError: cannot assign to field 'lazy'

    Compare parameter instances:

    >>> params1 = PanderaParameters(lazy=True)
    >>> params2 = PanderaParameters(lazy=True)
    >>> params1 == params2
    True
    >>> params3 = PanderaParameters(lazy=False)
    >>> params1 == params3
    False
    """

    lazy: bool = True
