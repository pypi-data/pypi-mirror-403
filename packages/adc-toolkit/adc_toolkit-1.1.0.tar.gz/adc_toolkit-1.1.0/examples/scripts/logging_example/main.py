"""A simple example of logging in Python."""

from adc_toolkit.logger import Logger
from examples.scripts.logging_example.module.functions import add_one


Logger.set_level("debug")

logger = Logger(__name__)


def main() -> None:
    """Test function.

    It will work regardless of the logger library installed.

    """
    # Call the add_one function
    result = add_one(5)

    # Log the result
    logger.info(f"The result is: {result}")
