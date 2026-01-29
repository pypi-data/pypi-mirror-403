"""
methurator
Python package designed to estimate CpGs
saturation for DNA methylation sequencing data.
"""

__version__ = "2.0.0"

from .plot import plot
from .downsample import downsample

__all__ = [
    "plot",
    "downsample",
    "gt-estimator",
    "__version__",
]
