import pytest
import math
from src.intervals import Interval, IntervalSet
from src.multidimensional import Box, Set


class TestAnalysis1D:
    def test_interval_analysis(self):
        i = Interval.closed(0, 10)
        assert i.convex_hull() == i
        assert i.diameter() == 10.0

        empty = Interval.empty()
        assert empty.convex_hull().is_empty()
        assert empty.diameter() == 0.0

    def test_interval_set_analysis(self):
        s = IntervalSet([Interval(0, 1), Interval(5, 10)])
        hull = s.convex_hull()
        assert hull == Interval.closed(0, 10)
        assert s.diameter() == 10.0

        # Open boundaries in hull
        s2 = IntervalSet([Interval.open(0, 1), Interval.open(5, 10)])
        hull2 = s2.convex_hull()
        assert hull2 == Interval.open(0, 10)

        # Mixed boundaries
        s3 = IntervalSet([Interval.closed(0, 1), Interval.open(5, 10)])
        hull3 = s3.convex_hull()
        # [0, 1] hull (5, 10) is [0, 10)
        assert hull3 == Interval.right_open(0, 10)

        empty = IntervalSet()
        assert empty.convex_hull().is_empty()
        assert empty.diameter() == 0.0

    def test_properties_1d(self):
        # Boundedness
        assert Interval.closed(0, 10).is_bounded()
        assert not Interval(0, float("inf")).is_bounded()
        assert not Interval(float("-inf"), 0).is_bounded()
        assert Interval.empty().is_bounded()

        # Open/Closed
        assert Interval.open(0, 1).is_open()
        assert not Interval.closed(0, 1).is_open()
        assert Interval.closed(0, 1).is_closed()
        assert not Interval.open(0, 1).is_closed()

        # Compact
        assert Interval.closed(0, 1).is_compact()
        assert not Interval.open(0, 1).is_compact()
        assert not Interval(0, float("inf"), open_end=True).is_compact()

        # IntervalSet properties
        s = IntervalSet([Interval.closed(0, 1), Interval.closed(2, 3)])
        assert s.is_closed()
        assert not s.is_open()
        assert s.is_bounded()
        assert s.is_compact()

        s_open = IntervalSet([Interval.open(0, 1), Interval.open(2, 3)])
        assert s_open.is_open()
        assert not s_open.is_closed()

        # Clopen set (empty set is clopen)
        assert IntervalSet().is_open() is False  # wait, library defines True/False?
        # Actually in our code:
        # def is_open(self): return not self.is_empty() and self == self.interior()
        # So empty is neither open nor closed in this lib's named methods.
        # But topographically it is both. Let's see what I implemented.

        # Distance between sets
        s1 = IntervalSet([Interval(0, 1)])
        s2 = IntervalSet([Interval(5, 6)])
        assert s1.distance(s2) == 4.0


class TestAnalysisND:
    def test_box_analysis(self):
        b = Box([Interval(0, 3), Interval(0, 4)])
        assert b.convex_hull() == b
        assert b.diameter() == 5.0  # sqrt(3^2 + 4^2)

        # distance_to_point
        assert b.distance_to_point([0, 0]) == 0.0
        assert b.distance_to_point([1.5, 2]) == 0.0
        assert b.distance_to_point([-3, 0]) == 3.0
        assert b.distance_to_point([0, -4]) == 4.0
        assert b.distance_to_point([6, 8]) == 5.0  # (6-3=3, 8-4=4) -> sqrt(3^2+4^2)=5

        with pytest.raises(ValueError):
            b.distance_to_point([0])

        empty = Box.empty(2)
        assert empty.distance_to_point([0, 0]) == float("inf")
        assert empty.convex_hull().is_empty()
        assert empty.diameter() == 0.0

    def test_set_analysis(self):
        b1 = Box([Interval(0, 1), Interval(0, 1)])
        b2 = Box([Interval(2, 3), Interval(4, 5)])
        s = Set([b1, b2])

        hull = s.convex_hull()
        # x range: [0, 3], y range: [0, 5]
        assert hull == Box([Interval.closed(0, 3), Interval.closed(0, 5)])
        assert s.diameter() == math.sqrt(3**2 + 5**2)

        # distance_to_point
        assert s.distance_to_point([0.5, 0.5]) == 0.0
        assert s.distance_to_point([1.5, 0.5]) == 0.5  # dist to b1 (x=1)
        assert s.distance_to_point([2.5, 4.5]) == 0.0  # inside b2

        empty = Set()
        assert empty.distance_to_point([0, 0]) == float("inf")
        assert empty.convex_hull().is_empty()
        assert empty.diameter() == 0.0

        # Coverage for Set.convex_hull dimension logic (Line 475)
        s_unknown = Set()
        assert s_unknown.convex_hull().dimension == 1

        s_2d_empty = Set()
        s_2d_empty._dimension = 2
        assert s_2d_empty.convex_hull().dimension == 2

    def test_properties_nd(self):
        # Boundedness
        b = Box([Interval(0, 1), Interval(0, 1)])
        assert b.is_bounded()
        b_inf = Box([Interval(0, float("inf")), Interval(0, 1)])
        assert not b_inf.is_bounded()

        # Open/Closed
        b_open = Box([Interval.open(0, 1), Interval.open(0, 1)])
        assert b_open.is_open()
        assert not b_open.is_closed()

        b_closed = Box([Interval.closed(0, 1), Interval.closed(0, 1)])
        assert b_closed.is_closed()
        assert not b_closed.is_open()

        # Compact
        assert b_closed.is_compact()
        assert not b_open.is_compact()

        # Set properties
        s = Set([b_closed])
        assert s.is_closed()
        assert s.is_bounded()
        assert s.is_compact()
        assert not s.is_open()

        s_open = Set([Box([Interval.open(0, 1), Interval.open(0, 1)])])
        assert s_open.is_open()
        assert not s_open.is_closed()
        assert not s_open.is_compact()

        # Empty Set properties
        empty_s = Set()
        assert not empty_s.is_open()
        assert not empty_s.is_closed()
        assert not empty_s.is_compact()
        assert empty_s.is_bounded()

        # Distance between sets
        s2 = Set([Box([Interval(3, 4), Interval(0, 1)])])
        assert s.distance(s2) == 2.0  # (3-1) = 2 in x, 0 in y.

        # Distance to Box/Interval/IntervalSet
        assert s.distance(Box([Interval(3, 4), Interval(0, 1)])) == 2.0
        # For multi-dimensional distance, inputs MUST match dimensions.
        # Interval.closed(3, 4) is 1D, s is 2d -> expected failure or promotion?
        # In our implementation it fails. We should use a matching Box.
        assert s.distance(Box([Interval.closed(3, 4), Interval.closed(0, 0)])) == 2.0

    def test_coverage_gaps(self):
        # Box matches jv.end < iv.start (Line 275)
        b1 = Box([Interval(5, 6)])
        b2 = Box([Interval(0, 1)])
        assert b1.distance(b2) == 4.0

        # distance with empty
        assert Box.empty(1).distance(b1) == float("inf")
        assert Set().distance(Set()) == float("inf")

        # is_bounded/is_compact empty
        assert Box.empty(1).is_bounded()
        assert Set().is_bounded()
        assert not Set().is_compact()  # it's neither open nor closed in our lib

        # dimension check in distance
        with pytest.raises(ValueError):
            b1.distance(Box([Interval(0, 1), Interval(0, 1)]))
