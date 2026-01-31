"""
methurator
Python package designed to estimate CpGs
saturation for DNA methylation sequencing data.
"""

from importlib.metadata import version

__version__ = version("methurator")

from .plot import plot
from .downsample import downsample

__all__ = [
    "plot",
    "downsample",
    "gt_estimator",
    "__version__",
]
