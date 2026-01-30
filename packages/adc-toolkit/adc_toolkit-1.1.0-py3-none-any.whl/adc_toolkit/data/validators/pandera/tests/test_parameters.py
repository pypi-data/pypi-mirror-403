"""Tests for PanderaParameters dataclass."""

from dataclasses import FrozenInstanceError

import pytest

from adc_toolkit.data.validators.pandera.parameters import PanderaParameters


def test_pandera_parameters_default_lazy_is_true() -> None:
    """Test that the default value of lazy is True."""
    params = PanderaParameters()
    assert params.lazy is True


def test_pandera_parameters_lazy_can_be_set_to_false() -> None:
    """Test that lazy can be set to False."""
    params = PanderaParameters(lazy=False)
    assert params.lazy is False


def test_pandera_parameters_is_frozen() -> None:
    """Test that PanderaParameters is immutable (frozen)."""
    params = PanderaParameters()
    with pytest.raises(FrozenInstanceError):
        params.lazy = False  # type: ignore[misc]


def test_pandera_parameters_equality() -> None:
    """Test that two PanderaParameters with same values are equal."""
    params1 = PanderaParameters(lazy=False)
    params2 = PanderaParameters(lazy=False)
    assert params1 == params2


def test_pandera_parameters_inequality() -> None:
    """Test that two PanderaParameters with different values are not equal."""
    params1 = PanderaParameters(lazy=True)
    params2 = PanderaParameters(lazy=False)
    assert params1 != params2
