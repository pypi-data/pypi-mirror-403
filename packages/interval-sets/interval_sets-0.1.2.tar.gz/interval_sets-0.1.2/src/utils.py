"""Utility functions for interval operations."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .intervals import Interval  # pragma: no cover


def interval_values(interval: "Interval") -> tuple:
    """
    Extract interval properties as a tuple for comparison.

    Args:
        interval: An Interval instance

    Returns:
        Tuple of (start, end, open_start, open_end)
    """
    return (
        interval.start,
        interval.end,
        interval.open_start,
        interval.open_end,
    )


def intervals_are_adjacent(interval1, interval2) -> bool:
    """
    Check if two intervals are adjacent (touching but not overlapping).

    Args:
        interval1: First interval (Interval)
        interval2: Second interval (Interval)

    Returns:
        True if intervals are adjacent, False otherwise
    """
    start_open1, end_open1 = interval1.open_start, interval1.open_end
    start_open2, end_open2 = interval2.open_start, interval2.open_end

    # interval1 ends where interval2 starts
    if interval1.end == interval2.start:
        return not (end_open1 and start_open2)

    # interval2 ends where interval1 starts
    if interval2.end == interval1.start:
        return not (end_open2 and start_open1)

    return False
