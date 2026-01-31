import pytest
from src.intervals import Interval, IntervalSet
from src.multidimensional import Box, Set


class TestBoxSet:
    def test_init_normalizes_overlap(self):
        # Two overlapping boxes: [0, 5]x[0, 5] and [3, 8]x[3, 8]
        b1 = Box([Interval(0, 5), Interval(0, 5)])
        b2 = Box([Interval(3, 8), Interval(3, 8)])

        region = Set([b1, b2])

        # Should have decomposed b2 into parts that don't overlap b1
        # b1 remains intact. b2 is fragmented.
        # b1: 1 box. b2 parts: 3 or 4 boxes.
        # Check volume: 25 + 25 - overlap(2x2=4) = 46.
        assert region.volume() == 46.0

        # Verify disjointness
        boxes = region.boxes
        for i, b1 in enumerate(boxes):
            for j, b2 in enumerate(boxes):
                if i != j:
                    assert not b1.overlaps(b2)

    def test_add_disjoint(self):
        region = Set()
        region.add(Box([Interval(0, 1)]))
        region.add(Box([Interval(2, 3)]))
        assert len(region.boxes) == 2
        assert region.volume() == 2.0

    def test_union_l_shape(self):
        # Create L-shape
        # Vertical: [0, 1]x[0, 2]
        # Horizontal: [0, 2]x[0, 1]
        v = Box([Interval(0, 1), Interval(0, 2)])
        h = Box([Interval(0, 2), Interval(0, 1)])

        r1 = Set([v])
        r2 = r1.union(h)
        assert r2.volume() == 3.0  # 2 + 2 - 1

    def test_difference_hole(self):
        # 10x10 square minus 2x2 hole in middle
        outer = Set([Box([Interval(0, 10), Interval(0, 10)])])
        hole = Box([Interval(4, 6), Interval(4, 6)])

        r = outer.difference(hole)
        assert r.volume() == 100.0 - 4.0

    def test_intersection(self):
        # [0, 10]x[0, 10] intersect [5, 15]x[5, 15] -> [5, 10]x[5, 10]
        r1 = Set([Box([Interval(0, 10), Interval(0, 10)])])
        r2 = Set([Box([Interval(5, 15), Interval(5, 15)])])

        inter = r1.intersection(r2)
        assert inter.volume() == 25.0

    def test_empty_region(self):
        r = Set()
        assert r.is_empty()
        assert r.volume() == 0.0
        assert not r.contains((0, 0))

    def test_dimension_mismatch(self):
        r = Set([Box([Interval(0, 1)])])
        b2 = Box([Interval(0, 1), Interval(0, 1)])

        with pytest.raises(ValueError, match="mismatch"):
            r.add(b2)

    def test_contains(self):
        r = Set([Box([Interval(0, 5)])])
        assert r.contains((2.5,))
        assert not r.contains((6,))
        # assert not r.contains((2.5, 2.5)) # Dim mismatch raises ValueError now

        with pytest.raises(ValueError, match="match Set dimension"):
            r.contains((2.5, 2.5))

    def test_dimension_property(self):
        r = Set()
        assert r.dimension is None
        r.add(Box([Interval(0, 1)]))
        assert r.dimension == 1

    def test_add_empty_box(self):
        """Cover Line 269: if box.is_empty(): return."""
        r = Set()
        invalid_box = Box([Interval.empty()])
        r.add(invalid_box)
        assert r.is_empty()

    def test_intersection_coercion(self):
        """Cover Line 322: intersection with Box."""
        r = Set([Box([Interval(0, 10)])])
        b = Box([Interval(5, 15)])
        # Should coerce b to Set and intersect
        res = r.intersection(b)
        assert res.volume() == 5.0

    def test_intersection_dimension_mismatch(self):
        """Cover Line 325: ValueError on mismatch."""
        r = Set([Box([Interval(0, 1)])])
        b = Box([Interval(0, 1), Interval(0, 1)])
        with pytest.raises(ValueError, match="mismatch"):
            r.intersection(b)

    def test_difference_dimension_mismatch(self):
        """Cover Line 362: ValueError on mismatch."""
        r = Set([Box([Interval(0, 1)])])
        b = Box([Interval(0, 1), Interval(0, 1)])
        with pytest.raises(ValueError, match="mismatch"):
            r.difference(b)

    def test_difference_coercion(self):
        """Cover Line 358: difference with Box."""
        r = Set([Box([Interval(0, 10)])])
        b = Box([Interval(0, 5)])
        res = r.difference(b)
        assert res.volume() == 5.0

    def test_add_optimization_break(self):
        """Cover Line 287: if not fragments: break."""
        # We need a case where fragments become empty mid-loop.
        # r has boxes B1, B2.
        # We add B_new.
        # B_new overlaps B1 fully -> fragments becomes empty?
        # If fragments empty, we break.
        # Setup: B_new is subset of B1.
        r = Set([Box([Interval(0, 10)]), Box([Interval(20, 30)])])
        b_sub = Box([Interval(2, 5)])  # Inside first box

        # When adding b_sub:
        # Loop 1 (B1): overlaps. b_sub - B1 -> Empty. fragments=[]
        # Loop 2 (B2): break immediately.
        r.add(b_sub)
        # Verify nothing added (volume same)
        assert r.volume() == 20.0

    def test_union_with_box(self):
        """Cover Line 390: union with Box."""
        r = Set([Box([Interval(0, 5)])])
        b = Box([Interval(5, 10)])
        res = r.union(b)
        assert res.volume() == 10.0

    def test_difference_no_overlap(self):
        """Cover Line 375: else branch (no overlap in difference)."""
        r = Set([Box([Interval(0, 5)])])
        b = Set([Box([Interval(10, 15)])])
        res = r.difference(b)
        assert res.volume() == 5.0
        assert len(res.boxes) == 1

    def test_difference_partial_overlap_break(self):
        """Cover Line 378: break when fragments empty."""
        r = Set([Box([Interval(0, 5)])])
        # Two boxes in difference source.
        # First one swallows the region completely.
        b1 = Box([Interval(-1, 6)])
        b2 = Box([Interval(10, 20)])
        other = Set([b1, b2])

        # When processing difference:
        # Loop 1 (b1): fragments becomes empty.
        # Loop 2 (b2): Should break.
        res = r.difference(other)
        assert res.is_empty()

    def test_intersection_no_overlap(self):
        """Cover Line 338: if b1.overlaps(b2) is False."""
        r1 = Set([Box([Interval(0, 5)])])
        r2 = Set([Box([Interval(6, 10)])])
        res = r1.intersection(r2)
        assert res.is_empty()

    def test_iter(self):
        """Cover Line 405: __iter__."""
        b = Box([Interval(0, 1)])
        r = Set([b])
        assert list(r) == [b]

    def test_union_with_set(self):
        """Cover Line 393: union with Set."""
        r1 = Set([Box([Interval(0, 5)])])
        r2 = Set([Box([Interval(5, 10)])])
        res = r1.union(r2)
        assert res.volume() == 10.0
        assert len(res.boxes) == 2  # Assuming disjoint, normalization logic

    def test_add_promotion_interval(self):
        """Cover Line 267: Promotion of Interval to Box."""
        s = Set()
        i = Interval(0, 10)
        s.add(i)
        assert s.dimension == 1
        assert s.volume() == 10.0

    def test_add_promotion_interval_set(self):
        """Cover Line 269-271: Promotion of IntervalSet to Box."""
        s = Set()
        iset = IntervalSet([Interval(0, 5), Interval(10, 15)])
        s.add(iset)
        assert s.dimension == 1
        assert s.volume() == 10.0
        assert len(s.boxes) == 2

    def test_add_promotion_recursive_set(self):
        """Cover Line 262-264: adding another Set (formerly Region)."""
        s1 = Set([Box([Interval(0, 5)])])
        s2 = Set([Box([Interval(10, 15)])])
        s1.add(s2)
        assert s1.volume() == 10.0
        assert len(s1.boxes) == 2

    def test_add_type_error(self):
        """Cover Line 275: TypeError on invalid item."""
        s = Set()
        with pytest.raises(
            TypeError, match="Expected Box, Set, Interval or IntervalSet"
        ):
            s.add("not a box")

    def test_init_with_mixed_promotion(self):
        """Test constructor with mixed types."""
        b = Box([Interval(0, 1)])
        i = Interval(2, 3)
        iset = IntervalSet([Interval(4, 5)])
        s = Set([b, i, iset])
        assert s.volume() == 3.0
        assert len(s.boxes) == 3


class TestBoxSetOperators:
    """Test pythonic operators for N-dimensional Set class."""

    def test_or_operator(self):
        s1 = Set([Box([Interval(0, 5)])])
        s2 = Set([Box([Interval(10, 15)])])
        res = s1 | s2
        assert res.volume() == 10.0
        assert len(res.boxes) == 2

    def test_and_operator(self):
        s1 = Set([Box([Interval(0, 10)])])
        s2 = Box([Interval(5, 15)])  # Test promotion in &
        res = s1 & s2
        assert res.volume() == 5.0

    def test_sub_operator(self):
        s1 = Set([Box([Interval(0, 10)])])
        i = Interval(0, 5)  # Test promotion in -
        res = s1 - i
        assert res.volume() == 5.0

    def test_xor_operator(self):
        s1 = Set([Box([Interval(0, 10)])])
        s2 = Set([Box([Interval(5, 15)])])
        res = s1 ^ s2
        # (0, 10) ^ (5, 15) = (0, 5) | (10, 15)
        assert res.volume() == 10.0
        assert len(res.boxes) >= 2

    def test_contains_operator(self):
        s = Set([Box([Interval(0, 5)])])
        assert (2.5,) in s
        assert (6.0,) not in s

    def test_repr(self):
        s = Set([Box([Interval(0, 5)])])
        r = repr(s)
        assert "Set(dim=1, boxes=1)" in r

    def test_symmetric_difference_method(self):
        """Cover symmetric_difference with non-Set other."""
        s = Set([Box([Interval(0, 10)])])
        b = Box([Interval(5, 15)])
        res = s.symmetric_difference(b)
        assert res.volume() == 10.0
