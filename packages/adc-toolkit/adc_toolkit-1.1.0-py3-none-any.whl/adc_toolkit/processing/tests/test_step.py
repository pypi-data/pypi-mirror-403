"""Unit tests for the PipelineStep class."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from ..step import PipelineStep


@pytest.fixture
def mock_step_function() -> MagicMock:
    """
    Fixture that creates a mock step function.

    Returns
    -------
    Mock
        A mock function that returns the input data unchanged.
    """
    return MagicMock(return_value=pd.DataFrame({"mock_column": [42]}), __name__="mock_step_function")


@pytest.fixture
def pipeline_step(mock_step_function: MagicMock) -> PipelineStep:
    """
    Fixture that creates a PipelineStep instance with a mock function.

    Parameters
    ----------
    mock_step_function : MagicMock
        The mock step function to use.

    Returns
    -------
    PipelineStep
        A PipelineStep instance configured with the mock function.
    """
    return PipelineStep(step=mock_step_function, param1="test", param2=123)


def test_pipeline_step_initialization(pipeline_step: PipelineStep) -> None:
    """
    Test that PipelineStep is initialized correctly with the given parameters.

    Parameters
    ----------
    pipeline_step : PipelineStep
        The pipeline step fixture to test.
    """
    assert pipeline_step.step is not None
    assert isinstance(pipeline_step.kwargs, dict)
    assert pipeline_step.kwargs == {"param1": "test", "param2": 123}


def test_pipeline_step_str_representation(pipeline_step: PipelineStep) -> None:
    """
    Test the string representation of PipelineStep.

    Parameters
    ----------
    pipeline_step : PipelineStep
        The pipeline step fixture to test.
    """
    expected_str = f"{pipeline_step.step.__name__}(param1=test, param2=123)"
    assert str(pipeline_step) == expected_str


def test_pipeline_step_successful_execution(pipeline_step: PipelineStep, mock_step_function: MagicMock) -> None:
    """
    Test successful execution of a pipeline step.

    Parameters
    ----------
    pipeline_step : PipelineStep
        The pipeline step fixture to test.
    mock_step_function : MagicMock
        The mock step function to verify calls.
    """
    input_data = pd.DataFrame({"mock_column": [21]})
    result = pipeline_step.execute(input_data)

    # Verify the step function was called with correct arguments
    mock_step_function.assert_called_once_with(input_data, param1="test", param2=123)

    # Verify the result
    assert isinstance(result, pd.DataFrame)
    assert result["mock_column"].iloc[0] == 42


def test_pipeline_step_execution_error(pipeline_step: PipelineStep, mock_step_function: MagicMock) -> None:
    """
    Test error handling during pipeline step execution.

    Parameters
    ----------
    pipeline_step : PipelineStep
        The pipeline step fixture to test.
    mock_step_function : MagicMock
        The mock step function to configure for error testing.
    """
    # Configure mock to raise an exception
    mock_step_function.side_effect = ValueError("Test error")

    # Test that the error is propagated
    with pytest.raises(ValueError) as exc_info:
        pipeline_step.execute(pd.DataFrame({"mock_column": [21]}))

    assert str(exc_info.value) == "Test error"
