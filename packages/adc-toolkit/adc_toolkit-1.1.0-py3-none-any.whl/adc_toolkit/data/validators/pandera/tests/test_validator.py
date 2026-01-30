"""Tests for Pandera Validator."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from adc_toolkit.data.validators.pandera.parameters import PanderaParameters
from adc_toolkit.data.validators.pandera.validator import PanderaValidator


def test_pandera_validator_init() -> None:
    """Test the initialization of PanderaValidator with default parameters."""
    validator = PanderaValidator("test/path")
    assert validator.config_path == Path("test/path/pandera_schemas")
    assert validator.parameters == PanderaParameters()
    assert validator.parameters.lazy is True


def test_pandera_validator_init_with_parameters() -> None:
    """Test the initialization of PanderaValidator with custom parameters."""
    parameters = PanderaParameters(lazy=True)
    validator = PanderaValidator("test/path", parameters=parameters)
    assert validator.config_path == Path("test/path/pandera_schemas")
    assert validator.parameters == parameters
    assert validator.parameters.lazy is True


def test_pandera_validator_in_directory() -> None:
    """Test the in_directory method of PanderaValidator with default parameters."""
    path = "test/path"
    validator = PanderaValidator.in_directory(path)
    assert validator.config_path == Path(path) / "pandera_schemas"
    assert validator.parameters == PanderaParameters()
    assert validator.parameters.lazy is True


def test_pandera_validator_in_directory_with_parameters() -> None:
    """Test the in_directory method of PanderaValidator with custom parameters."""
    path = "test/path"
    parameters = PanderaParameters(lazy=True)
    validator = PanderaValidator.in_directory(path, parameters=parameters)
    assert validator.config_path == Path(path) / "pandera_schemas"
    assert validator.parameters == parameters
    assert validator.parameters.lazy is True


@patch("adc_toolkit.data.validators.pandera.validator.validate_data")
def test_pandera_validator_validate(mock_validate_data: MagicMock) -> None:
    """Test the validate method of PanderaValidator."""
    # Arrange
    mock_data = MagicMock()
    mock_validate_data.return_value = mock_data
    validator = PanderaValidator("test/path")
    name = "test_schema"

    # Act
    result = validator.validate(name, mock_data)

    # Assert
    mock_validate_data.assert_called_once_with(name, mock_data, validator.config_path, validator.parameters)
    assert result == mock_data


@patch("adc_toolkit.data.validators.pandera.validator.validate_data")
def test_pandera_validator_validate_with_lazy_true(mock_validate_data: MagicMock) -> None:
    """Test the validate method of PanderaValidator with lazy=True."""
    # Arrange
    mock_data = MagicMock()
    mock_validate_data.return_value = mock_data
    parameters = PanderaParameters(lazy=True)
    validator = PanderaValidator("test/path", parameters=parameters)
    name = "test_schema"

    # Act
    result = validator.validate(name, mock_data)

    # Assert
    mock_validate_data.assert_called_once_with(name, mock_data, validator.config_path, parameters)
    assert result == mock_data
