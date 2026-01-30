"""Tests for execute_schema_script module."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pandera.errors import SchemaError, SchemaErrors

from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError
from adc_toolkit.data.validators.pandera.execute_schema_script import (
    construct_module_name,
    execute_validation,
    validate_data_with_script_from_path,
)
from adc_toolkit.data.validators.pandera.parameters import PanderaParameters


class TestConstructModuleName(unittest.TestCase):
    """Tests for construct_module_name function."""

    @patch("adc_toolkit.data.validators.pandera.execute_schema_script.extract_relative_path")
    def test_construct_module_name(self, mock_relative_path: MagicMock) -> None:
        """Test construct_module_name with valid inputs."""
        name = "test_table"
        path = Path("/home/user/project_folder/project_name/src/data/validators/pandera/schemas")
        mock_relative_path.return_value = Path("src/data/validators/pandera/schemas")
        expected_output = "src.data.validators.pandera.schemas.test_table"
        result = construct_module_name(name, path)
        self.assertEqual(result, expected_output)

    @patch("adc_toolkit.data.validators.pandera.execute_schema_script.extract_relative_path")
    def test_construct_module_name_with_empty_name(self, mock_relative_path: MagicMock) -> None:
        """Test construct_module_name with empty name."""
        name = ""
        path = Path("/home/user/project_folder/project_name/src/data/validators/pandera/schemas")
        mock_relative_path.return_value = Path("src/data/validators/pandera/schemas")
        expected_output = "src.data.validators.pandera.schemas."
        result = construct_module_name(name, path)
        self.assertEqual(result, expected_output)

    @patch("adc_toolkit.data.validators.pandera.execute_schema_script.extract_relative_path")
    def test_construct_module_name_with_empty_path(self, mock_relative_path: MagicMock) -> None:
        """Test construct_module_name with empty path."""
        name = "test_table"
        path = Path()
        mock_relative_path.return_value = Path()
        expected_output = "..test_table"
        result = construct_module_name(name, path)
        self.assertEqual(result, expected_output)

    @patch("adc_toolkit.data.validators.pandera.execute_schema_script.extract_relative_path")
    def test_construct_module_name_with_backslash(self, mock_relative_path: MagicMock) -> None:
        """Test construct_module_name with valid inputs."""
        name = "test_table"
        path = Path("\\home\\user\\project_folder\\project_name\\src\\data\\validators\\pandera\\schemas")
        mock_relative_path.return_value = Path("src\\data\\validators\\pandera\\schemas")
        expected_output = "src.data.validators.pandera.schemas.test_table"
        result = construct_module_name(name, path)
        self.assertEqual(result, expected_output)


@patch("adc_toolkit.data.validators.pandera.execute_schema_script.ModuleType")
def test_execute_validation(mock_module: MagicMock) -> None:
    """Test execute_validation with valid inputs and lazy=False (default)."""
    mock_module.schema.validate.return_value = "validated_data"
    module = mock_module
    data = MagicMock()
    parameters = PanderaParameters()
    expected_output = "validated_data"
    result = execute_validation(module, data, parameters)
    assert result == expected_output
    mock_module.schema.validate.assert_called_once_with(data, lazy=True)


@patch("adc_toolkit.data.validators.pandera.execute_schema_script.ModuleType")
def test_execute_validation_with_lazy_false(mock_module: MagicMock) -> None:
    """Test execute_validation with lazy=False."""
    mock_module.schema.validate.return_value = "validated_data"
    module = mock_module
    data = MagicMock()
    parameters = PanderaParameters(lazy=False)
    expected_output = "validated_data"
    result = execute_validation(module, data, parameters)
    assert result == expected_output
    mock_module.schema.validate.assert_called_once_with(data, lazy=False)


@patch("adc_toolkit.data.validators.pandera.execute_schema_script.import_or_reload_module")
@patch("adc_toolkit.data.validators.pandera.execute_schema_script.construct_module_name")
@patch("adc_toolkit.data.validators.pandera.execute_schema_script.execute_validation")
def test_validate_data_with_script_from_path(
    mock_execute_validation: MagicMock,
    mock_construct_module_name: MagicMock,
    mock_import_or_reload_module: MagicMock,
) -> None:
    """Test validate_data_with_script_from_path with valid inputs."""
    mock_execute_validation.return_value = "validated_data"
    mock_construct_module_name.return_value = "module_name"
    mock_module = MagicMock()
    mock_import_or_reload_module.return_value = mock_module
    name = "test_table"
    data = MagicMock()
    path = Path("/home/user/project_folder/project_name/src/data/validators/pandera/schemas")
    parameters = PanderaParameters()
    expected_output = "validated_data"
    result = validate_data_with_script_from_path(name, data, path, parameters)
    assert result == expected_output
    mock_execute_validation.assert_called_once_with(mock_module, data, parameters)


@patch("adc_toolkit.data.validators.pandera.execute_schema_script.FileManager")
@patch("adc_toolkit.data.validators.pandera.execute_schema_script.import_or_reload_module")
@patch("adc_toolkit.data.validators.pandera.execute_schema_script.construct_module_name")
@patch("adc_toolkit.data.validators.pandera.execute_schema_script.execute_validation")
def test_validate_data_with_script_from_path_wraps_schema_error(
    mock_execute_validation: MagicMock,
    mock_construct_module_name: MagicMock,
    mock_import_or_reload_module: MagicMock,
    mock_file_manager: MagicMock,
) -> None:
    """Test that SchemaError is wrapped in PanderaValidationError."""
    # Arrange
    original_error = SchemaError(schema=None, data=None, message="Column 'x' not found")
    mock_execute_validation.side_effect = original_error
    mock_construct_module_name.return_value = "module_name"
    mock_import_or_reload_module.return_value = MagicMock()
    mock_file_manager_instance = mock_file_manager.return_value
    mock_file_manager_instance.create_full_path.return_value = Path("/path/to/schema/test_table.py")

    name = "test_table"
    data = MagicMock()
    path = Path("/path/to/schemas")
    parameters = PanderaParameters()

    # Act & Assert
    with pytest.raises(PanderaValidationError) as exc_info:
        validate_data_with_script_from_path(name, data, path, parameters)

    error = exc_info.value
    assert error.table_name == name
    assert error.schema_path == Path("/path/to/schema/test_table.py")
    assert error.original_error is original_error
    assert name in str(error)


class MockSchemaErrors(SchemaErrors):
    """Mock SchemaErrors that can be instantiated without a schema."""

    def __init__(self, message: str = "Multiple validation errors") -> None:
        Exception.__init__(self, message)
        self.message = message


@patch("adc_toolkit.data.validators.pandera.execute_schema_script.FileManager")
@patch("adc_toolkit.data.validators.pandera.execute_schema_script.import_or_reload_module")
@patch("adc_toolkit.data.validators.pandera.execute_schema_script.construct_module_name")
@patch("adc_toolkit.data.validators.pandera.execute_schema_script.execute_validation")
def test_validate_data_with_script_from_path_wraps_schema_errors(
    mock_execute_validation: MagicMock,
    mock_construct_module_name: MagicMock,
    mock_import_or_reload_module: MagicMock,
    mock_file_manager: MagicMock,
) -> None:
    """Test that SchemaErrors (multiple errors) is wrapped in PanderaValidationError."""
    # Arrange - Create a mock exception that inherits from SchemaErrors
    original_error = MockSchemaErrors("Multiple validation errors")
    mock_execute_validation.side_effect = original_error
    mock_construct_module_name.return_value = "module_name"
    mock_import_or_reload_module.return_value = MagicMock()
    mock_file_manager_instance = mock_file_manager.return_value
    mock_file_manager_instance.create_full_path.return_value = Path("/path/to/schema/my_table.py")

    name = "my_schema.my_table"
    data = MagicMock()
    path = Path("/path/to/schemas")
    parameters = PanderaParameters()

    # Act & Assert
    with pytest.raises(PanderaValidationError) as exc_info:
        validate_data_with_script_from_path(name, data, path, parameters)

    error = exc_info.value
    assert error.table_name == name
    assert error.original_error is original_error
