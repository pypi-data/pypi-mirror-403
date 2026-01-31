"""
datapipe — Data Pipeline Tool.
"""

__version__ = "0.1.1"

from datapipe.core import decomposition, MIN_DELAY, MAX_DELAY, MAX_OFFSET
from datapipe.cli import main as evolution

__all__ = ["decomposition", "evolution", "MIN_DELAY", "MAX_DELAY", "MAX_OFFSET", "__version__"]
