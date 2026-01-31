import math
from src.intervals import Interval, IntervalSet


def test_unbounded_creation():
    inf = float("inf")
    # (-inf, inf)
    i = Interval(-inf, inf)
    assert i.start == -inf
    assert i.end == inf
    assert i.open_start  # Enforced
    assert i.open_end  # Enforced
    assert not i.is_empty()
    assert math.isinf(i.length())

    # (0, inf)
    i2 = Interval(0, inf, open_start=True)
    assert i2.start == 0
    assert i2.end == inf
    assert i2.open_start
    assert i2.open_end  # Enforced


def test_infinite_arithmetic():
    inf = float("inf")
    # Union of adjacent closed-at-boundary intervals
    # (-inf, 0] | [0, inf) -> (-inf, inf)
    i3 = Interval(-inf, 0, open_end=False)
    i4 = Interval(0, inf, open_start=False)
    u = i3.union(i4)
    assert isinstance(u, Interval)
    assert u.start == -inf
    assert u.end == inf
    assert u.open_start
    assert u.open_end

    # Intersection
    # (-inf, 10) & (-10, inf) -> (-10, 10)
    i5 = Interval(-inf, 10)
    i6 = Interval(-10, inf)
    inter = i5.intersection(i6)
    assert inter.start == -10
    assert inter.end == 10


def test_complement():
    # Complement of [0, 1] in explicit universe R
    universe = IntervalSet(
        [Interval(float("-inf"), float("inf"), open_start=True, open_end=True)]
    )
    s = IntervalSet.interval(0, 1)  # [0, 1]
    comp = s.complement(universe)

    # Should be (-inf, 0) U (1, inf)
    assert len(comp) == 2
    intervals = comp.intervals()
    i1 = intervals[0]
    i2 = intervals[1]

    # Ordered by start
    assert i1.start == float("-inf")
    assert i1.end == 0
    assert i1.open_end

    assert i2.start == 1
    assert i2.end == float("inf")
    assert i2.open_start


def test_invalid_infinity():
    # Attempt to create closed infinity
    # It should be forced to open, not raise error (based on my implementation)
    i = Interval(float("-inf"), 5, open_start=False)
    assert i.open_start

    i2 = Interval(5, float("inf"), open_end=False)
    assert i2.open_end


def test_empty_infinity():
    # (inf, inf) -> empty
    i = Interval(float("inf"), float("inf"))
    assert i.is_empty()
    assert i.start == 0  # Canonical normalization
    assert i.end == 0
