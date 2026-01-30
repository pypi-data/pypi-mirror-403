"""Tests for PanderaValidationError exception."""

from pathlib import Path
from unittest.mock import MagicMock

from adc_toolkit.data.validators.pandera.exceptions import PanderaValidationError


def test_pandera_validation_error_message_contains_table_name() -> None:
    """Test that the error message contains the table name."""
    table_name = "my_schema.my_table"
    schema_path = Path("/path/to/schema/my_schema/my_table.py")
    original_error = MagicMock()
    original_error.__str__ = MagicMock(return_value="Column 'x' not found")

    error = PanderaValidationError(
        table_name=table_name,
        schema_path=schema_path,
        original_error=original_error,
    )

    assert table_name in str(error)


def test_pandera_validation_error_message_contains_schema_path() -> None:
    """Test that the error message contains the schema path."""
    table_name = "my_schema.my_table"
    schema_path = Path("/path/to/schema/my_schema/my_table.py")
    original_error = MagicMock()
    original_error.__str__ = MagicMock(return_value="Column 'x' not found")

    error = PanderaValidationError(
        table_name=table_name,
        schema_path=schema_path,
        original_error=original_error,
    )

    assert str(schema_path) in str(error)


def test_pandera_validation_error_message_contains_original_error() -> None:
    """Test that the error message contains the original error details."""
    table_name = "my_schema.my_table"
    schema_path = Path("/path/to/schema/my_schema/my_table.py")
    original_error = MagicMock()
    original_error.__str__ = MagicMock(return_value="Column 'x' not found")

    error = PanderaValidationError(
        table_name=table_name,
        schema_path=schema_path,
        original_error=original_error,
    )

    assert "Column 'x' not found" in str(error)


def test_pandera_validation_error_stores_attributes() -> None:
    """Test that the exception stores all attributes correctly."""
    table_name = "my_schema.my_table"
    schema_path = Path("/path/to/schema/my_schema/my_table.py")
    original_error = MagicMock()

    error = PanderaValidationError(
        table_name=table_name,
        schema_path=schema_path,
        original_error=original_error,
    )

    assert error.table_name == table_name
    assert error.schema_path == schema_path
    assert error.original_error is original_error


def test_pandera_validation_error_is_exception() -> None:
    """Test that PanderaValidationError is an Exception."""
    table_name = "my_schema.my_table"
    schema_path = Path("/path/to/schema/my_schema/my_table.py")
    original_error = MagicMock()

    error = PanderaValidationError(
        table_name=table_name,
        schema_path=schema_path,
        original_error=original_error,
    )

    assert isinstance(error, Exception)
