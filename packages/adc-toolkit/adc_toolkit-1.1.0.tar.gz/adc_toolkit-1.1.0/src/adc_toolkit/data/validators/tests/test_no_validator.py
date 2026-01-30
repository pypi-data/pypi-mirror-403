"""Tests for NoValidator."""

import unittest

import pandas as pd

from adc_toolkit.data.validators.no_validator import NoValidator


class TestNoValidator(unittest.TestCase):
    """Tests for NoValidator."""

    def setUp(self) -> None:
        """Set up."""
        self.validator = NoValidator()

    def test_warning(self) -> None:
        """Test that warning is raised during initialization."""
        with self.assertWarns(UserWarning) as warning:
            NoValidator()

        self.assertEqual(
            str(warning.warning),
            "Not using any validator is not recommended. "
            "Consider using a validator from the `adc_toolkit.data.validators` module.",
        )

    def test_in_directory(self) -> None:
        """Test in_directory."""
        validator = NoValidator.in_directory(".")
        self.assertIsInstance(validator, NoValidator)

    def test_validate(self) -> None:
        """Test validate."""
        name = "test_name"
        data = pd.DataFrame(
            {
                "col1": [1, 2, 3],
                "col2": [4, 5, 6],
            }
        )

        result = self.validator.validate(name, data)

        pd.testing.assert_frame_equal(result, data)
