"""Error handling for interval operations."""


def operand_error_message(this_type: str, operation: str, other_type: str) -> str:
    """Generate a standardized error message for unsupported operand types."""
    classes_msg = f"'{this_type}' and '{other_type}'"
    return f"Unsupported operand type(s) for {operation}: {classes_msg}"


def point_error(operator: str, other: object) -> TypeError:
    """Create a TypeError for invalid Point operations."""
    error_msg = operand_error_message("Point", operator, type(other).__name__)
    return TypeError(error_msg)


def continuous_interval_error(operator: str, other: object) -> TypeError:
    """Create a TypeError for invalid ContinuousInterval operations."""
    error_msg = operand_error_message(
        "ContinuousInterval", operator, type(other).__name__
    )
    return TypeError(error_msg)


class IntervalError(Exception):
    """Base exception for interval-related errors."""

    pass


class InvalidIntervalError(IntervalError, ValueError):
    """Raised when an interval is constructed with invalid parameters."""

    pass


class OverlappingIntervalError(IntervalError):
    """Raised when overlapping intervals are found where they shouldn't be."""

    pass
