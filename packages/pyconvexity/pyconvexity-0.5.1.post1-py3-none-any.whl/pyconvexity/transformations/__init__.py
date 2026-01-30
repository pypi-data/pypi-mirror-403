"""
Transformations module for PyConvexity.

Provides functions for transforming network data, including:
- Time axis modification (truncation, resampling)
- Future: network merging, scenario duplication, etc.
"""

from pyconvexity.transformations.api import modify_time_axis
from pyconvexity.transformations.time_axis import TimeAxisModifier

__all__ = [
    "modify_time_axis",
    "TimeAxisModifier",
]
