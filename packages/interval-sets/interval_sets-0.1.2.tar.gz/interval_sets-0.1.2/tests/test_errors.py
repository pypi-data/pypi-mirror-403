import pytest

from src.errors import (
    point_error,
    continuous_interval_error,
    operand_error_message,
    IntervalError,
    InvalidIntervalError,
    OverlappingIntervalError,
)


def test_operand_error_message_format():
    """Test operand_error_message creates correct format"""
    msg = operand_error_message("TypeA", "+", "TypeB")
    assert msg == "Unsupported operand type(s) for +: 'TypeA' and 'TypeB'"


def test_operand_error_message_with_different_operators():
    """Test various operators"""
    operators = ["+", "-", "*", "/", "==", "!=", "<", "<=", ">", ">="]

    for op in operators:
        msg = operand_error_message("Type1", op, "Type2")
        assert f"for {op}:" in msg
        assert "'Type1' and 'Type2'" in msg


def test_point_error_returns_type_error():
    """Test point_error returns TypeError"""
    error = point_error("+", "string")

    assert isinstance(error, TypeError)


def test_point_error_message_content():
    """Test point_error message contains relevant information"""
    error = point_error("+", "string")
    error_msg = str(error)

    assert "Point" in error_msg
    assert "+" in error_msg
    assert "str" in error_msg


def test_point_error_with_various_types():
    """Test point_error with different object types"""
    test_objects = [
        (5, "int"),
        (5.5, "float"),
        ("test", "str"),
        ([1, 2], "list"),
        ({"key": "val"}, "dict"),
    ]

    for obj, expected_type in test_objects:
        error = point_error("+", obj)
        assert expected_type in str(error)


def test_continuous_interval_error_returns_type_error():
    """Test continuous_interval_error returns TypeError"""
    error = continuous_interval_error("<", 42)

    assert isinstance(error, TypeError)


def test_continuous_interval_error_message_content():
    """Test continuous_interval_error message contains relevant information"""
    error = continuous_interval_error("<=", [1, 2, 3])
    error_msg = str(error)

    assert "ContinuousInterval" in error_msg
    assert "<=" in error_msg
    assert "list" in error_msg


def test_interval_error_is_exception():
    """Test IntervalError is an Exception"""
    assert issubclass(IntervalError, Exception)

    # Should be able to raise and catch
    with pytest.raises(IntervalError):
        raise IntervalError("Test error")


def test_invalid_interval_error_inheritance():
    """Test InvalidIntervalError inherits from both IntervalError and ValueError"""
    assert issubclass(InvalidIntervalError, IntervalError)
    assert issubclass(InvalidIntervalError, ValueError)


def test_invalid_interval_error_can_be_raised():
    """Test InvalidIntervalError can be raised and caught"""
    with pytest.raises(InvalidIntervalError) as exc_info:
        raise InvalidIntervalError("Test invalid interval")

    assert "Test invalid interval" in str(exc_info.value)


def test_invalid_interval_error_caught_as_interval_error():
    """Test InvalidIntervalError can be caught as IntervalError"""
    with pytest.raises(IntervalError):
        raise InvalidIntervalError("Test")


def test_invalid_interval_error_caught_as_value_error():
    """Test InvalidIntervalError can be caught as ValueError"""
    with pytest.raises(ValueError):
        raise InvalidIntervalError("Test")


def test_overlapping_interval_error_inheritance():
    """Test OverlappingIntervalError inherits from IntervalError"""
    assert issubclass(OverlappingIntervalError, IntervalError)


def test_overlapping_interval_error_can_be_raised():
    """Test OverlappingIntervalError can be raised and caught"""
    with pytest.raises(OverlappingIntervalError) as exc_info:
        raise OverlappingIntervalError("Test overlapping intervals")

    assert "Test overlapping intervals" in str(exc_info.value)


def test_overlapping_interval_error_caught_as_interval_error():
    """Test OverlappingIntervalError can be caught as IntervalError"""
    with pytest.raises(IntervalError):
        raise OverlappingIntervalError("Test")


def test_all_error_classes_have_docstrings():
    """Test all custom exception classes have docstrings"""
    assert IntervalError.__doc__ is not None
    assert InvalidIntervalError.__doc__ is not None
    assert OverlappingIntervalError.__doc__ is not None


def test_error_message_with_special_characters():
    """Test error messages handle special characters"""
    msg = operand_error_message("Type<T>", ">>", "Type[U]")
    assert "Type<T>" in msg
    assert ">>" in msg
    assert "Type[U]" in msg


def test_point_error_with_none():
    """Test point_error with None value."""
    error = point_error("+", None)
    assert isinstance(error, TypeError)
    assert "Point" in str(error)
    assert "NoneType" in str(error)


def test_continuous_interval_error_with_none():
    """Test continuous_interval_error with None value."""
    error = continuous_interval_error("<=", None)
    assert isinstance(error, TypeError)
    assert "ContinuousInterval" in str(error)
    assert "NoneType" in str(error)
