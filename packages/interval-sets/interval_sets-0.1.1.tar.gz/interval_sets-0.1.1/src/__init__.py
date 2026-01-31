"""
Interval Arithmetic Library

A Python library for working with intervals and points on the real number line.
Supports continuous intervals with open/closed boundaries and disjoint interval collections.
"""

from .intervals import Interval, Set
from .errors import (
    IntervalError,
    InvalidIntervalError,
    OverlappingIntervalError,
    point_error,
    continuous_interval_error,
)

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "Interval", 
    "Set",
    
    # Exceptions
    "IntervalError",
    "InvalidIntervalError", 
    "OverlappingIntervalError",
    
    # Error functions
    "point_error",
    "continuous_interval_error",
]