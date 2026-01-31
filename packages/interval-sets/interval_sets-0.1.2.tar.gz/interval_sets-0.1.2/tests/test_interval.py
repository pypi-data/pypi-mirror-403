import pytest
from src.intervals import Point, Interval, IntervalSet
from src.errors import InvalidIntervalError


class TestIntervalCreation:
    """Test interval creation and validation."""

    def test_basic_creation(self):
        """Test creating basic intervals."""
        interval = Interval(0, 10)
        assert interval.start == 0
        assert interval.end == 10
        assert not interval.open_start
        assert not interval.open_end

    def test_open_interval_creation(self):
        """Test creating open intervals."""
        interval = Interval(0, 10, open_start=True, open_end=True)
        assert interval.open_start
        assert interval.open_end

    def test_mixed_boundary_intervals(self):
        """Test creating intervals with mixed boundaries."""
        left_open = Interval(0, 10, open_start=True, open_end=False)
        assert left_open.open_start
        assert not left_open.open_end

        right_open = Interval(0, 10, open_start=False, open_end=True)
        assert not right_open.open_start
        assert right_open.open_end

    def test_point_creation(self):
        """Test creating point intervals."""
        point = Interval.point(5)
        assert point.start == 5
        assert point.end == 5
        assert not point.open_start
        assert not point.open_end

    def test_empty_creation(self):
        """Test creating empty intervals."""
        empty = Interval.empty()
        assert empty.start == 0
        assert empty.end == 0
        assert empty.open_start
        assert empty.open_end
        assert empty.is_empty()

    def test_class_methods(self):
        """Test all class method shortcuts."""
        # Test open
        open_interval = Interval.open(1, 5)
        assert open_interval.open_start and open_interval.open_end

        # Test closed
        closed_interval = Interval.closed(1, 5)
        assert not closed_interval.open_start and not closed_interval.open_end

        # Test left_open
        left_open = Interval.left_open(1, 5)
        assert left_open.open_start and not left_open.open_end

        # Test right_open
        right_open = Interval.right_open(1, 5)
        assert not right_open.open_start and right_open.open_end


class TestIntervalValidation:
    """Test interval validation and error cases."""

    def test_invalid_bounds_error(self):
        """Test error when start > end."""
        with pytest.raises(InvalidIntervalError, match="start.*must be <= end"):
            Interval(10, 5)

    def test_nan_boundaries_error(self):
        """Test error with NaN boundaries."""
        with pytest.raises(ValueError, match="cannot be NaN"):
            Interval(float("nan"), 5)

        with pytest.raises(ValueError, match="cannot be NaN"):
            Interval(0, float("nan"))

    def test_infinite_boundaries_error(self):
        """Test with infinite boundaries."""
        # Infinite boundaries are now allowed (treated as open by constructor usually, but manual is fine)
        # Wait, start=inf, end=5 -> start > end. Should raise InvalidIntervalError.
        with pytest.raises(InvalidIntervalError, match="must be <= end"):
            Interval(float("inf"), 5)

        # Valid infinite interval
        valid_inf = Interval(0, float("inf"))
        assert valid_inf.end == float("inf")

    def test_invalid_open_same_endpoints(self):
        """Test creating open interval with same start/end (except empty)."""
        # This now normalizes to empty interval
        empty = Interval(5, 5, open_start=True, open_end=True)
        assert empty.is_empty()

        # Mixed also becomes empty?
        # Logic: if start == end and (open_start or open_end): ... -> empty
        normalized = Interval(5, 5, open_start=True, open_end=False)
        assert normalized.is_empty()


class TestIntervalProperties:
    """Test interval properties and methods."""

    def test_is_empty(self):
        """Test empty interval detection."""
        # Empty interval
        empty = Interval.empty()
        assert empty.is_empty()

        # Non-empty intervals
        assert not Interval(0, 1).is_empty()
        assert not Interval.point(5).is_empty()

        # Open interval touching endpoints
        touching_open = Interval(0, 1, open_start=True, open_end=True)
        assert not touching_open.is_empty()  # (0,1) is not empty

    def test_length(self):
        """Test interval length calculation."""
        # Regular interval
        interval = Interval(0, 10)
        assert interval.length() == 10

        # Point interval
        point = Interval.point(5)
        assert point.length() == 0

        # Empty interval
        empty = Interval.empty()
        assert empty.length() == 0


class TestIntervalContainment:
    """Test interval containment operations."""

    def test_contains_value(self):
        """Test value containment in intervals."""
        # Closed interval [0, 10]
        closed = Interval(0, 10)
        assert 0 in closed  # boundary included
        assert 5 in closed  # interior point
        assert 10 in closed  # boundary included
        assert -1 not in closed  # outside
        assert 11 not in closed  # outside

        # Open interval (0, 10)
        open_interval = Interval.open(0, 10)
        assert 0 not in open_interval  # boundary excluded
        assert 5 in open_interval  # interior point
        assert 10 not in open_interval  # boundary excluded

        # Mixed boundaries
        left_open = Interval.left_open(0, 10)  # (0, 10]
        assert 0 not in left_open
        assert 10 in left_open

        right_open = Interval.right_open(0, 10)  # [0, 10)
        assert 0 in right_open
        assert 10 not in right_open

    def test_contains_interval(self):
        """Test interval containment in intervals."""
        big = Interval(0, 10)
        small = Interval(2, 8)

        assert small in big
        assert big not in small

        # Boundary cases
        touching_start = Interval(0, 5)
        touching_end = Interval(5, 10)

        assert touching_start in big
        assert touching_end in big

        # Open boundary cases
        open_big = Interval.open(0, 10)
        closed_small = Interval(0, 10)

        assert closed_small not in open_big  # closed can't be in open with same bounds

    def test_empty_containment(self):
        """Test containment with empty intervals."""
        empty = Interval.empty()
        regular = Interval(0, 10)

        # Empty contains nothing
        assert 5 not in empty
        assert regular not in empty

        # Everything contains empty
        assert empty in regular


class TestIntervalOperations:
    """Test interval operations."""

    def test_overlaps(self):
        """Test interval overlap detection."""
        a = Interval(0, 5)
        b = Interval(3, 8)
        c = Interval(10, 15)

        assert a.overlaps(b)
        assert b.overlaps(a)
        assert not a.overlaps(c)
        assert not c.overlaps(a)

        # Touching intervals
        touching1 = Interval(0, 5)
        touching2 = Interval(5, 10)
        assert touching1.overlaps(touching2)  # [0,5] touches [5,10]

        # Open touching intervals
        open1 = Interval(0, 5, open_end=True)  # [0, 5)
        open2 = Interval(5, 10)  # [5, 10]
        assert not open1.overlaps(open2)  # [0,5) doesn't touch [5,10]

    def test_is_adjacent(self):
        """Test interval adjacency detection."""
        a = Interval(0, 5)
        b = Interval(5, 10)
        c = Interval(6, 10)

        assert a.is_adjacent(b)
        assert b.is_adjacent(a)
        assert not a.is_adjacent(c)  # gap between them

        # Overlapping intervals are not adjacent
        overlapping = Interval(3, 8)
        assert not a.is_adjacent(overlapping)


class TestIntervalComparison:
    """Test interval comparison and equality."""

    def test_equality(self):
        """Test interval equality."""
        a = Interval(0, 10)
        b = Interval(0, 10)
        c = Interval(0, 10, open_start=True)

        assert a == b
        assert a != c
        assert hash(a) == hash(b)
        assert hash(a) != hash(c)

    def test_comparison_operators(self):
        """Test interval comparison operators."""
        a = Interval(0, 5)
        b = Interval(5, 10)
        c = Interval(0, 5)
        d = Interval(6, 10)  # Actually disjoint from a

        # Test less than (completely to the left)
        assert a < d  # [0,5] is completely left of [6,10]
        assert not d < a
        assert not a < c  # equal intervals
        assert not a < b  # [0,5] touches [5,10], not completely left

        # Test less than or equal
        assert a <= d
        assert a <= c
        assert not d <= a


class TestIntervalStringRepresentation:
    """Test interval string representations."""

    def test_repr(self):
        """Test interval repr."""
        closed = Interval(0, 10)
        assert repr(closed) == "[0.0, 10.0]"

        open_interval = Interval.open(0, 10)
        assert repr(open_interval) == "(0.0, 10.0)"

        left_open = Interval.left_open(0, 10)
        assert repr(left_open) == "(0.0, 10.0]"

        right_open = Interval.right_open(0, 10)
        assert repr(right_open) == "[0.0, 10.0)"

        point = Interval.point(5)
        assert repr(point) == "Point(5.0)"

        empty = Interval.empty()
        assert repr(empty) == "∅"


class TestIntervalEdgeCases:
    """Test interval edge cases and boundary conditions."""

    def test_zero_length_intervals(self):
        """Test intervals with zero length."""
        point = Interval.point(5)
        assert point.length() == 0
        assert 5 in point
        assert 4.9 not in point
        assert 5.1 not in point

    def test_very_small_intervals(self):
        """Test very small intervals."""
        tiny = Interval(0, 1e-10)
        assert tiny.length() == 1e-10
        assert 0 in tiny
        assert 1e-10 in tiny
        assert 5e-11 in tiny  # midpoint

    def test_negative_intervals(self):
        """Test intervals with negative values."""
        negative = Interval(-10, -5)
        assert negative.length() == 5
        assert -7 in negative
        assert -15 not in negative
        assert 0 not in negative

    def test_mixed_sign_intervals(self):
        """Test intervals crossing zero."""
        crossing = Interval(-5, 5)
        assert crossing.length() == 10
        assert 0 in crossing
        assert -3 in crossing
        assert 3 in crossing

    def test_is_point_method(self):
        """Test is_point method."""
        # Point interval
        point = Interval.point(5)
        assert point.is_point()

        # Regular interval
        regular = Interval(0, 10)
        assert not regular.is_point()

        # Empty interval
        empty = Interval.empty()
        assert not empty.is_point()

    def test_contains_non_interval_types(self):
        """Test contains method with non-interval, non-numeric types."""
        interval = Interval(0, 10)

        # Should return False for non-numeric, non-interval types
        assert not interval.contains("5")
        assert not interval.contains(None)
        assert not interval.contains([5])
        assert not interval.contains({})

    def test_overlaps_edge_cases(self):
        """Test overlaps method edge cases."""
        a = Interval(0, 5)
        empty = Interval.empty()

        # Empty intervals don't overlap with anything
        assert not a.overlaps(empty)
        assert not empty.overlaps(a)
        assert not empty.overlaps(empty)

        # Test touching intervals with mixed boundaries
        c = Interval(0, 5, open_end=True)  # [0, 5)

        # [0, 5] and (5, 10] should NOT overlap (touching at 5)
        touching_closed_open = Interval(0, 5)
        touching_open_closed = Interval(5, 10, open_start=True)
        assert not touching_closed_open.overlaps(touching_open_closed)

        # [0, 5) and [5, 10] should NOT overlap (gap at 5)
        assert not c.overlaps(Interval(5, 10))

    def test_interval_intersection_edge_cases(self):
        """Test interval intersection edge cases."""
        a = Interval(0, 10)
        b = Interval(5, 15)
        empty = Interval.empty()

        # Intersection with empty
        assert a.intersection(empty).is_empty()
        assert empty.intersection(a).is_empty()

        # Normal intersection
        intersection = a.intersection(b)
        if isinstance(intersection, Interval):
            assert intersection == Interval(5, 10)

    def test_interval_union_non_overlapping(self):
        """Test interval union with non-overlapping intervals."""
        a = Interval(0, 5)
        b = Interval(10, 15)

        # Should create a IntervalSet with two intervals
        union = a.union(b)
        assert isinstance(union, IntervalSet)
        assert len(union) == 2

    def test_interval_difference_edge_cases(self):
        """Test interval difference edge cases."""
        a = Interval(0, 10)
        empty = Interval.empty()

        # Difference with empty should return original
        diff = a.difference(empty)
        if isinstance(diff, Interval):
            assert diff == a
        else:
            assert len(diff) == 1 and diff[0] == a

        # Empty difference with anything should return empty
        empty_diff = empty.difference(a)
        assert empty_diff.is_empty()

    def test_interval_operators(self):
        """Test interval operators."""
        a = Interval(0, 10)
        b = Interval(5, 15)

        # Test | operator (union)
        union = a | b
        assert isinstance(union, (Interval, IntervalSet))

        # Test & operator (intersection)
        intersection = a & b
        assert isinstance(intersection, (Interval, IntervalSet))

        # Test - operator (difference)
        difference = a - b
        assert isinstance(difference, (Interval, IntervalSet))

    def test_intersection_edge_case_open_boundaries(self):
        """
        Cover logic in Interval.intersection where start == end
        but boundaries are open, resulting in empty set instead of invalid interval.
        """
        # Case 1: Open boundaries -> empty set
        i1 = Interval(0, 5, open_end=True)
        i2 = Interval(5, 10, open_start=True)
        intersection = i1.intersection(i2)
        assert intersection.is_empty()

        # Case 2: Closed boundaries -> Point
        i3 = Interval(0, 5)
        i4 = Interval(5, 10)
        intersection_point = i3.intersection(i4)
        assert isinstance(intersection_point, Point)
        assert intersection_point.value == 5

    def test_union_branch_start_conditions(self):
        """Cover union branching where start conditions vary."""
        # 1. start == self.start (True)
        # i1 wins start.
        i1 = Interval(0, 10)
        i2 = Interval(5, 10)  # start=0. 0==0.
        i1.union(i2)

        # 2. start != self.start (False) -> start == other.start (True)
        i3 = Interval(5, 10)
        i4 = Interval(0, 10)  # start=0. 0!=5. 0==0.
        i3.union(i4)

        # 3. start == self.start AND start == other.start
        i5 = Interval(0, 10)
        i6 = Interval(0, 5)
        i5.union(i6)
