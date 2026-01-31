from src.intervals import Interval, IntervalSet, Point


class TestMathematicalRigor:
    """Explicit tests for mathematical rigor and edge cases."""

    def test_rigorous_boundary_merging(self):
        """
        Critical Test: Merging logic for (0, 10) U [10, 20).
        Mathematically, these are disjoint sets: (0, 10] and [10, 20) are NOT disjoint (share 10),
        but (0, 10) excludes 10, and [10, 20) includes 10.
        They are adjacent and their union creates a continuous interval (0, 20).
        """
        i1 = Interval(0, 10, open_start=True, open_end=True)  # (0, 10)
        i2 = Interval(10, 20, open_start=False, open_end=True)  # [10, 20)

        # Verify 10 is not in i1
        assert 10 not in i1
        # Verify 10 is in i2
        assert 10 in i2

        # Union should merge them into (0, 20) because they "touch" and fill the gap
        union = i1.union(i2)

        # Expectation: (0, 20)
        expected = Interval(0, 20, open_start=True, open_end=True)
        assert union == expected
        assert 10 in union

    def test_rigorous_difference_non_connected(self):
        """
        Critical Test: Difference creating disconnected sets.
        [0, 10] \ [3, 7] = [0, 3) U (7, 10]
        """
        full = Interval(0, 10)
        remove = Interval(3, 7)

        diff = full.difference(remove)

        # Expectation: IntervalSet with 2 intervals
        assert isinstance(diff, IntervalSet)
        assert len(diff) == 2

        left = diff[0]
        right = diff[1]

        # Left part: [0, 3)
        assert left.start == 0
        assert left.end == 3
        assert not left.open_start
        assert left.open_end

        # Right part: (7, 10]
        assert right.start == 7
        assert right.end == 10
        assert right.open_start
        assert not right.open_end

    def test_empty_set_consistency(self):
        """
        Verify empty set representation consistency.
        While Interval.empty() and IntervalSet() are different classes, they should behave rationally.
        """
        s_empty = IntervalSet()
        i_empty = Interval.empty()

        # Both should have 0 length/measure
        assert s_empty.measure() == 0
        assert i_empty.length() == 0

        # Union of empty with empty is empty
        assert (s_empty | IntervalSet([i_empty])).is_empty()

        # Intersection with empty is empty
        assert (Interval(0, 10) & i_empty).is_empty()
        assert (IntervalSet([Interval(0, 10)]) & s_empty).is_empty()

    def test_point_semantics(self):
        """
        Verify Point semantics.
        Point(5) should be equivalent to Interval(5, 5).
        """
        p = Point(5)
        i = Interval(5, 5)

        # Equality check (Interval equality handles checking checks internal values)
        assert p == i

        # Membership
        assert 5 in p
        assert 5 in i

        # Union with adjacent intervals
        # [0, 5) U {5} = [0, 5]
        left = Interval(0, 5, open_end=True)
        union = left.union(p)
        assert union == Interval(0, 5)
        assert 5 in union

    def test_ordering_strictness(self):
        """Verify strict ordering semantics."""
        a = Interval(0, 5)
        b = Interval(6, 10)
        c = Interval(4, 8)  # Overlaps a

        # Strict partial order: a < b means a is strictly to the left of b
        assert a < b

        # Overlapping intervals are not ordered relative to each other in this scheme
        # This is one valid interpretation (Allen's "Before" relation)
        assert not (a < c)
        assert not (c < a)

    def test_set_normalization_three_way(self):
        """Test normalization of A, B, C where A and C are joined by B."""
        # [0, 2], [2, 4], [4, 6] -> [0, 6]
        # Intervals touching at boundaries should merge
        s = IntervalSet([Interval(0, 2), Interval(4, 6), Interval(2, 4)])

        assert len(s) == 1
        assert s[0] == Interval(0, 6)

    def test_set_normalization_gap_filling(self):
        """
        Test normalization where a new interval fills a gap.
        [0, 2] U [4, 6] U [2, 4) -> [0, 2] U [2, 4) U [4, 6] -> [0, 6]
        Note: [2, 4) fills the gap between [0, 2] and [4, 6].
        [0, 2] touches [2, 4) at 2.
        [2, 4) touches [4, 6] at 4.
        """
        s = IntervalSet([Interval(0, 2), Interval(4, 6)])
        assert len(s) == 2

        gap_filler = Interval(2, 4, open_end=True)  # [2, 4)
        s_new = s | IntervalSet([gap_filler])

        if isinstance(s_new, Interval):
            assert s_new == Interval(0, 6)
        else:
            assert len(s_new) == 1
            assert s_new[0] == Interval(0, 6)
