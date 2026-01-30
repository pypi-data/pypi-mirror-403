"""Tests for validate_data module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from adc_toolkit.data.validators.pandera.parameters import PanderaParameters
from adc_toolkit.data.validators.pandera.validate_data import create_schema_script_if_not_exists, validate_data


@patch("adc_toolkit.data.validators.pandera.validate_data.FileManager")
@patch("adc_toolkit.data.validators.pandera.validate_data.compile_type_specific_schema_script")
def test_create_schema_script_if_not_exists_file_exists(
    mock_compile_type_specific_schema_script: MagicMock,
    mock_file_manager: MagicMock,
) -> None:
    """Test validate_data when the schema file already exists."""
    # Arrange
    mock_file_manager_instance = mock_file_manager.return_value
    mock_file_manager_instance.check_if_file_exists.return_value = True
    mock_compile_type_specific_schema_script.return_value = "schema_script"
    name = "test_table"
    data = MagicMock()
    config_path = Path("/path/to/config")

    # Act
    create_schema_script_if_not_exists(name, data, config_path)

    # Assert
    mock_file_manager.assert_called_once_with(name, config_path)
    mock_file_manager_instance.check_if_file_exists.assert_called_once_with()
    mock_file_manager_instance.create_directory_and_empty_file.assert_not_called()
    mock_compile_type_specific_schema_script.assert_not_called()
    mock_file_manager_instance.write_file.assert_not_called()


@patch("adc_toolkit.data.validators.pandera.validate_data.FileManager")
@patch("adc_toolkit.data.validators.pandera.validate_data.compile_type_specific_schema_script")
def test_create_schema_script_if_not_exists_file_does_not_exist(
    mock_compile_type_specific_schema_script: MagicMock,
    mock_file_manager: MagicMock,
) -> None:
    """Test validate_data when the schema file already exists."""
    # Arrange
    mock_file_manager_instance = mock_file_manager.return_value
    mock_file_manager_instance.check_if_file_exists.return_value = False
    mock_compile_type_specific_schema_script.return_value = "schema_script"
    name = "test_table"
    data = MagicMock()
    config_path = Path("/path/to/config")

    # Act
    create_schema_script_if_not_exists(name, data, config_path)

    # Assert
    mock_file_manager.assert_called_once_with(name, config_path)
    mock_file_manager_instance.check_if_file_exists.assert_called_once_with()
    mock_file_manager_instance.create_directory_and_empty_file.assert_called_once_with()
    mock_compile_type_specific_schema_script.assert_called_once_with(data)
    mock_file_manager_instance.write_file.assert_called_once_with("schema_script")


@patch("adc_toolkit.data.validators.pandera.validate_data.create_schema_script_if_not_exists")
@patch("adc_toolkit.data.validators.pandera.validate_data.validate_data_with_script_from_path")
def test_validate_data(
    mock_validate_data_with_script_from_path: MagicMock,
    mock_create_schema_script_if_not_exists: MagicMock,
) -> None:
    """Test validate_data."""
    # Arrange
    mock_validate_data_with_script_from_path.return_value = "validated_data"
    name = "test_table"
    data = MagicMock()
    config_path = Path("/path/to/config")
    parameters = PanderaParameters()

    # Act
    result = validate_data(name, data, config_path, parameters)

    # Assert
    mock_create_schema_script_if_not_exists.assert_called_once_with(name, data, config_path)
    mock_validate_data_with_script_from_path.assert_called_once_with(name, data, config_path, parameters)
    assert result == "validated_data"


@patch("adc_toolkit.data.validators.pandera.validate_data.create_schema_script_if_not_exists")
@patch("adc_toolkit.data.validators.pandera.validate_data.validate_data_with_script_from_path")
def test_validate_data_with_lazy_true(
    mock_validate_data_with_script_from_path: MagicMock,
    mock_create_schema_script_if_not_exists: MagicMock,
) -> None:
    """Test validate_data with lazy=True parameter."""
    # Arrange
    mock_validate_data_with_script_from_path.return_value = "validated_data"
    name = "test_table"
    data = MagicMock()
    config_path = Path("/path/to/config")
    parameters = PanderaParameters(lazy=True)

    # Act
    result = validate_data(name, data, config_path, parameters)

    # Assert
    mock_create_schema_script_if_not_exists.assert_called_once_with(name, data, config_path)
    mock_validate_data_with_script_from_path.assert_called_once_with(name, data, config_path, parameters)
    assert result == "validated_data"
