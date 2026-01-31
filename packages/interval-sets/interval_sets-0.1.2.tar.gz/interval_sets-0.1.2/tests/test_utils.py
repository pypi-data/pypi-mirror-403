from src.intervals import Interval
from src.utils import interval_values, intervals_are_adjacent


def test_interval_values():
    interval = Interval(0, 10, open_start=True, open_end=False)

    values = interval_values(interval)

    assert values == (0, 10, True, False)
    assert isinstance(values, tuple)
    assert len(values) == 4


def test_intervals_are_adjacent_touching_closed():
    interval1 = Interval(0, 5)
    interval2 = Interval(5, 10)

    assert intervals_are_adjacent(interval1, interval2)
    assert intervals_are_adjacent(interval2, interval1)


def test_intervals_are_adjacent_touching_open():
    interval1 = Interval(0, 5, open_end=True)
    interval2 = Interval(5, 10, open_start=True)

    # Both open at the touching point - not adjacent
    assert not intervals_are_adjacent(interval1, interval2)


def test_intervals_are_adjacent_touching_mixed():
    interval1 = Interval(0, 5, open_end=False)
    interval2 = Interval(5, 10, open_start=True)

    # One closed, one open at touching point - still adjacent
    assert intervals_are_adjacent(interval1, interval2)

    interval3 = Interval(0, 5, open_end=True)
    interval4 = Interval(5, 10, open_start=False)

    assert intervals_are_adjacent(interval3, interval4)


def test_intervals_are_not_adjacent_overlapping():
    interval1 = Interval(0, 10)
    interval2 = Interval(5, 15)

    assert not intervals_are_adjacent(interval1, interval2)


def test_intervals_are_not_adjacent_disjoint():
    interval1 = Interval(0, 5)
    interval2 = Interval(10, 15)

    assert not intervals_are_adjacent(interval1, interval2)
