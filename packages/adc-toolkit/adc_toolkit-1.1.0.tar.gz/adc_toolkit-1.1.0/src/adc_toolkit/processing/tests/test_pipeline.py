"""Unit tests for the processing pipeline module."""

import pandas as pd
import pytest

from ..pipeline import ProcessingPipeline


def mock_step(data: pd.DataFrame, increment: int = 1) -> pd.DataFrame:
    """Mock processing step that increments the data value.

    Args:
        data: Input data to process
        increment: Value to add to the data

    Returns:
        Processed data with incremented value
    """
    result = pd.DataFrame({"mock_column": [data["mock_column"].iloc[0] + increment]})
    return result


def mock_multiply_step(data: pd.DataFrame, factor: int = 2) -> pd.DataFrame:
    """Mock processing step that multiplies the data value.

    Args:
        data: Input data to process
        factor: Value to multiply the data by

    Returns:
        Processed data with multiplied value
    """
    result = pd.DataFrame({"mock_column": [data["mock_column"].iloc[0] * factor]})
    return result


@pytest.fixture
def pipeline() -> ProcessingPipeline:
    """Create a fresh pipeline instance for testing.

    Returns:
        Empty ProcessingPipeline instance
    """
    return ProcessingPipeline()


@pytest.fixture
def mock_input_data() -> pd.DataFrame:
    """Create mock input data for testing.

    Returns:
        MockData instance with initial value of 1
    """
    return pd.DataFrame({"mock_column": [1]})


def test_pipeline_initialization(pipeline: ProcessingPipeline) -> None:
    """Test that pipeline is initialized with empty steps list."""
    assert len(pipeline.steps) == 0
    assert len(pipeline) == 0
    assert str(pipeline) == ""


def test_pipeline_add_step(pipeline: ProcessingPipeline) -> None:
    """Test adding a step to the pipeline."""
    pipeline.add(mock_step, increment=2)
    assert len(pipeline) == 1
    assert str(pipeline) != ""


def test_pipeline_multiple_steps(pipeline: ProcessingPipeline) -> None:
    """Test adding and representing multiple steps."""
    pipeline.add(mock_step, increment=2)
    pipeline.add(mock_multiply_step, factor=3)
    assert len(pipeline) == 2
    assert " -> " in str(pipeline)


def test_pipeline_run_single_step(pipeline: ProcessingPipeline, mock_input_data: pd.DataFrame) -> None:
    """Test running pipeline with a single step."""
    pipeline.add(mock_step, increment=2)
    result = pipeline.run(mock_input_data)

    assert isinstance(result, pd.DataFrame)
    assert result["mock_column"].iloc[0] == 3  # 1 + 2
    assert mock_input_data["mock_column"].iloc[0] == 1  # Original data unchanged


def test_pipeline_run_multiple_steps(pipeline: ProcessingPipeline, mock_input_data: pd.DataFrame) -> None:
    """Test running pipeline with multiple steps."""
    pipeline.add(mock_step, increment=2)  # 1 + 2 = 3
    pipeline.add(mock_multiply_step, factor=3)  # 3 * 3 = 9
    pipeline.add(mock_step, increment=1)  # 9 + 1 = 10

    result = pipeline.run(mock_input_data)

    assert isinstance(result, pd.DataFrame)
    assert result["mock_column"].iloc[0] == 10
    assert mock_input_data["mock_column"].iloc[0] == 1  # Original data unchanged


def test_pipeline_chaining(pipeline: ProcessingPipeline) -> None:
    """Test that add method supports method chaining."""
    result = pipeline.add(mock_step, increment=1).add(mock_multiply_step, factor=2)

    assert result is pipeline
    assert len(pipeline) == 2


def test_pipeline_deep_copy_input(pipeline: ProcessingPipeline, mock_input_data: pd.DataFrame) -> None:
    """Test that pipeline creates a deep copy of input data."""
    pipeline.add(mock_step, increment=5)
    result: pd.DataFrame = pipeline.run(mock_input_data)

    assert result is not mock_input_data
    assert result["mock_column"].iloc[0] != mock_input_data["mock_column"].iloc[0]
