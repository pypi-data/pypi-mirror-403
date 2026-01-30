"""Test expectation addition strategy classes."""

import pandas as pd
from great_expectations.data_context.data_context.ephemeral_data_context import EphemeralDataContext

from adc_toolkit.data.validators.gx import BatchManager
from adc_toolkit.data.validators.gx.batch_managers.expectation_addition_strategy import (
    SchemaExpectationAddition,
    SkipExpectationAddition,
)
from adc_toolkit.data.validators.gx.data_context.tests import data_context


def test_skip_expectation_addition(
    data_context: EphemeralDataContext,
) -> None:
    """Test SkipExpectationAddition class add_expectation method."""
    data = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": [4.0, 5.0, 6.0],
            "col3": ["a", "b", "c"],
        }
    )
    name = "test_name"
    batch_manager = BatchManager(name, data, data_context)
    batch_manager.data_context.add_or_update_expectation_suite(expectation_suite_name="test_name_suite")
    SkipExpectationAddition().add_expectations(batch_manager=batch_manager)
    suite = data_context.get_expectation_suite(expectation_suite_name="test_name_suite")
    assert suite.expectations == []


def test_schema_expectation_addition(
    data_context: EphemeralDataContext,
) -> None:
    """Test SchemaExpectationAddition class add_expectation method."""
    data = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": [4.0, 5.0, 6.0],
            "col3": ["a", "b", "c"],
        }
    )
    name = "test_name"
    batch_manager = BatchManager(name, data, data_context)
    batch_manager.data_context.add_or_update_expectation_suite(expectation_suite_name="test_name_suite")
    SchemaExpectationAddition().add_expectations(batch_manager=batch_manager)
    suite = data_context.get_expectation_suite(expectation_suite_name="test_name_suite")
    assert suite.expectations[0]["expectation_type"] == "expect_batch_schema_to_match_dict"
    assert suite.expectations[0]["kwargs"] == {
        "schema": {
            "col1": "int64",
            "col2": "float64",
            "col3": "object",
        }
    }


def test_schema_expectation_addition_check_if_exists(
    data_context: EphemeralDataContext,
) -> None:
    """Test SchemaExpectationAddition class _check_if_expectation_exists method."""
    data = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": [4.0, 5.0, 6.0],
            "col3": ["a", "b", "c"],
        }
    )
    name = "test_name"
    batch_manager = BatchManager(name, data, data_context)

    # Test when suite exists but has no expectations
    batch_manager.data_context.add_or_update_expectation_suite(expectation_suite_name="test_name_suite")
    strategy = SchemaExpectationAddition()
    assert not strategy._check_if_expectation_exists(batch_manager)

    # Test when suite exists and has expectations
    strategy.add_expectations(batch_manager)
    assert strategy._check_if_expectation_exists(batch_manager)
