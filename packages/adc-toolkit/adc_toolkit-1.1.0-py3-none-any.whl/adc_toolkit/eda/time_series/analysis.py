"""
This module provides a class for performing exploratory data analysis (EDA) on time series data.

The module uses configuration files to customize the analysis.
"""

from typing import ClassVar

from adc_toolkit.eda.time_series.plotting import time_series_eda
from adc_toolkit.eda.time_series.statistics import print_time_series_statistics
from adc_toolkit.eda.utils.base_analysis import ExploratoryDataAnalysis
from adc_toolkit.eda.utils.prepare_data import drop_non_numeric_columns
from adc_toolkit.logger import Logger


logger = Logger(__name__)


class TimeSeries(ExploratoryDataAnalysis):
    """
    Class for performing time series-specific exploratory data analysis.

    Methods:
        analyze: Run time series specific analysis.
    """

    DEFAULT_CONFIG_FILE_NAME = "ts_parameters.yaml"
    REQUIRED_KEYS: ClassVar[list[str]] = ["entity_column", "value_column", "time_column"]

    def analyze(self) -> None:
        """Run time series specific analysis."""
        # Only continue with numeric data for time series
        numeric_data = drop_non_numeric_columns(self.dataset)

        print_time_series_statistics(numeric_data, self.settings)
        time_series_eda(numeric_data, self.settings)
