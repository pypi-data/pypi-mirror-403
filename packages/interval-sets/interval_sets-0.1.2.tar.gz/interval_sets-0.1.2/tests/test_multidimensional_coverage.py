import pytest
from src.intervals import Interval, IntervalSet
from src.multidimensional import Box, Set


class TestBoxCoverage:
    """Targeted tests to fix coverage gaps in multidimensional.py."""

    def test_init_validation(self):
        """Cover Line 32: if not intervals: raise ValueError."""
        with pytest.raises(ValueError, match="must have at least 1 dimension"):
            Box([])

    def test_contains_is_empty(self):
        """Cover Line 77, 92, 98: is_empty checks in contains/overlaps."""
        # Create an empty box (one dimension empty)
        empty = Box([Interval.empty(), Interval(0, 1)])
        assert empty.is_empty()

        # Test contains with empty box
        assert not empty.contains((0.5, 0.5))

        # Test overlaps with empty box
        b = Box([Interval(0, 1), Interval(0, 1)])
        assert not empty.overlaps(b)
        assert not b.overlaps(empty)

    def test_overlaps_type_error(self):
        """Cover Line 92: Check overlap with non-Box."""
        b = Box([Interval(0, 1)])
        assert not b.overlaps("not a box")

    def test_overlaps_dimension_mismatch(self):
        """Cover Line 95: Overlaps dimension mismatch."""
        b1 = Box([Interval(0, 1)])
        b2 = Box([Interval(0, 1), Interval(0, 1)])
        with pytest.raises(ValueError, match="Cannot compare Box"):
            b1.overlaps(b2)

    def test_intersection_dimension_mismatch(self):
        """Cover Line 108: Intersection dimension mismatch."""
        b1 = Box([Interval(0, 1)])
        b2 = Box([Interval(0, 1), Interval(0, 1)])
        with pytest.raises(ValueError, match="Dimension mismatch"):
            b1.intersection(b2)

    def test_union_fallback(self):
        """Line 137: intersection fallback (should unlikely happen)."""
        # Hard to hit: Intersection of Convex Intervals is Convex.
        pass

    def test_difference_dimension_mismatch(self):
        """Cover Line 161: Difference dimension mismatch."""
        b1 = Box([Interval(0, 1)])
        b2 = Box([Interval(0, 1), Interval(0, 1)])
        with pytest.raises(ValueError, match="Dimension mismatch"):
            b1.difference(b2)

    def test_difference_no_overlap_check(self):
        # Line 167: overlaps check optimization
        # We implicitly hit this if we pass disjoint boxes, but we need to ensure we don't return early before the check if we enable optimization.
        # Current code checks intersection is_empty.
        b1 = Box([Interval(0, 1)])
        b2 = Box([Interval(2, 3)])
        # intersection is empty.
        diff = b1.difference(b2)
        assert len(diff) == 1
        assert diff[0] == b1

    def test_intersection_results_in_point(self):
        """Cover Line 121 (implicit): Intersection results in Point."""
        # [0, 1] & [1, 2] -> Point(1)
        b1 = Box([Interval(0, 1)])
        b2 = Box([Interval(1, 2)])
        inter = b1.intersection(b2)
        # Should be Box([Point(1)])
        assert inter.dimension == 1
        assert inter.intervals[0].is_point()
        assert inter.intervals[0].start == 1.0

    def test_equality_type_check(self):
        """Cover Line 146: __eq__ with non-Box."""
        b = Box([Interval(0, 1)])
        assert not (b == "not a box")
        assert not (b == 123)


class TestFinalCoverage:
    def test_intervalset_minkowski_diff_returns_single_interval(self):
        # A = [0, 10], B = [1, 2]
        # Erosion: A - B = {x : x + B subset A}
        # x + [1, 2] subset [0, 10] -> [x+1, x+2] subset [0, 10]
        # x+1 >= 0 => x >= -1
        # x+2 <= 10 => x <= 8
        # Result [-1, 8]

        s1 = IntervalSet([Interval(0, 10)])
        s2 = IntervalSet([Interval(1, 2)])

        diff = s1.minkowski_difference(s2)
        assert isinstance(diff, IntervalSet)
        assert len(diff) == 1
        assert diff._intervals[0] == Interval(-1, 8)

    def test_intervalset_opening_promotion(self):
        # Opening = dilate(erode(A, B), B)
        # s1 = [0, 10], s2 = [1, 2]
        # erode(s1, s2) -> [-1, 8] (IntervalSet, but internally treated as result)
        # dilate([-1, 8], [1, 2]) -> [-1+1, 8+2] = [0, 10]

        s1 = IntervalSet([Interval(0, 10)])
        s2 = IntervalSet([Interval(1, 2)])

        opened = s1.opening(s2)
        assert isinstance(opened, IntervalSet)
        assert opened == s1

    def test_intervalset_closing_promotion(self):
        # Closing = erode(dilate(A, B), B)
        # s1 = [0, 1], s2 = [2, 3]
        # dilate([0, 1], [2, 3]) -> [2, 4]
        # erode([2, 4], [2, 3]) -> [0, 1]

        s1 = IntervalSet([Interval(0, 1)])
        s2 = IntervalSet([Interval(2, 3)])

        closed = s1.closing(s2)
        assert isinstance(closed, IntervalSet)
        assert closed == s1

    def test_multidimensional_convex_hull_no_dimension(self):
        # Force _dimension is None logic
        class BrokenSet(Set):
            def is_empty(self):
                return False

        s = BrokenSet()
        s._dimension = None  # explicit None
        s._boxes = [Box.empty(1)]  # dummy

        hull = s.convex_hull()
        assert hull.is_empty()
        assert hull.dimension == 1

    def test_box_intersection_weird_return(self):
        # Line 181: inter is not Interval and not empty Set

        class MockResult:
            pass

        class BadInterval:
            # Mimic Interval enough for Box init
            def __init__(self):
                self.start = 0
                self.end = 1
                self.open_start = False
                self.open_end = False

            def is_empty(self):
                return False

            def intersection(self, other):
                return MockResult()  # Not an Interval, not empty Set

        # Bypass type hinting checks by using strict=False or just ignoring
        b_bad = Box([BadInterval()])
        b_normal = Box([Interval(0, 1)])

        # This will trigger Line 181 where it appends Interval.empty()
        # because result is not Interval and not "is_empty"
        res = b_bad.intersection(b_normal)
        assert res.is_empty()
