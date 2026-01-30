"""Example functions for logging."""

from adc_toolkit.logger import Logger


logger = Logger(__name__)


def add_one(a: int) -> int:
    """Add one to the input."""
    logger.debug(f"input: {a}")
    logger.info("adding one...")
    return a + 1
