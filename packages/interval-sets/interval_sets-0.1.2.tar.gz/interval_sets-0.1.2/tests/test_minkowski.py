import pytest
from src.intervals import Interval, IntervalSet
from src.multidimensional import Box, Set


class TestMinkowski1D:
    def test_interval_sum(self):
        # [0, 2] + [1, 3] = [1, 5]
        i1 = Interval.closed(0, 2)
        i2 = Interval.closed(1, 3)
        assert i1 + i2 == Interval.closed(1, 5)

        # (0, 2) + [1, 3] = (1, 5)
        i3 = Interval.open(0, 2)
        assert i3 + i2 == Interval.open(1, 5)

        # Scalar shift
        assert i1 + 10 == Interval.closed(10, 12)
        assert 10 + i1 == Interval.closed(10, 12)

        # Scalar infinity shift (Line 618-621 in intervals.py)
        i_inf = i1 + float("inf")
        assert i_inf.is_empty()

        # Empty sum
        assert Interval.empty().minkowski_sum(i1) == Interval.empty()
        assert i1.minkowski_sum(Interval.empty()) == Interval.empty()

        # Type error
        with pytest.raises(TypeError):
            i1.minkowski_sum("not an interval")

        # dilate alias
        assert i1.dilate(10) == Interval.closed(10, 12)

    def test_interval_erosion(self):
        # [0, 10] erode [0, 1] = [0, 9]
        a = Interval.closed(0, 10)
        b = Interval.closed(0, 1)
        assert a.minkowski_difference(b) == Interval.closed(0, 9)

        # (0, 10) erode [0, 1] = (0, 9)
        a_open = Interval.open(0, 10)
        assert a_open.erode(b) == Interval.open(0, 9)

        # (0, 10) erode (0, 1) = [0, 9]
        b_open = Interval.open(0, 1)
        assert a_open.erode(b_open) == Interval.closed(0, 9)

        # Edge cases for coverage
        assert Interval.empty().erode(b) == Interval.empty()
        assert a.erode(Interval.empty()) == Interval.empty()
        with pytest.raises(TypeError):
            a.erode("not an interval")

        # Too large erosion -> empty (Line 670)
        assert b.erode(a) == Interval.empty()
        # Degenerate erosion becomes empty if boundaries are open (Line 679)
        assert Interval.open(0, 1).erode(Interval.closed(0, 1)) == Interval.empty()

    def test_interval_set_sum(self):
        # {[0, 1], [10, 11]} + [0, 1] = {[0, 2], [10, 12]}
        s = IntervalSet([Interval(0, 1), Interval(10, 11)])
        b = Interval.closed(0, 1)
        res = s + b
        assert len(res) == 2
        assert Interval.closed(0, 2) in res
        assert Interval.closed(10, 12) in res

        # Scalar shift for IntervalSet (Line 1299)
        res_scalar = s + 10
        assert Interval.closed(10, 11) in res_scalar
        assert Interval.closed(20, 21) in res_scalar

        # Reverse scalar shift (Line 1373)
        res_rscalar = 10 + s
        assert res_rscalar == res_scalar

        # Sum of two sets
        s2 = IntervalSet([Interval(0, 1), Interval(5, 6)])
        res2 = s + s2
        # Components: [0, 2], [5, 7], [10, 12], [15, 17]
        assert len(res2) == 4

        # Empty/Edge cases for IntervalSet.minkowski_sum
        assert IntervalSet().minkowski_sum(b) == IntervalSet()
        assert s.minkowski_sum(Interval.empty()) == IntervalSet()
        assert s.minkowski_sum(IntervalSet()) == IntervalSet()
        with pytest.raises(TypeError):
            s.minkowski_sum("not supported")

    def test_interval_set_erosion(self):
        s = IntervalSet([Interval(0, 5), Interval(10, 15)])
        b = Interval.closed(0, 1)
        res = s.erode(b)
        assert len(res) == 2

        # Erosion by set: A -(B1 U B2) = (A-B1) \cap (A-B2)
        b_set = IntervalSet([Interval(0, 1), Interval(4, 5)])
        res2 = s.erode(b_set)
        assert 0 in res2
        assert 10 in res2

        # Early break in intersection (Line 1357)
        # s - { [0, 1], [20, 30] } -> (s - [0, 1]) & (s - [20, 30])
        # s - [20, 30] is empty. Intersection is empty.
        b_set_far = IntervalSet([Interval(0, 1), Interval(20, 30)])
        assert s.erode(b_set_far).is_empty()

        # Empty/Edge cases for IntervalSet.minkowski_difference
        assert IntervalSet().erode(b) == IntervalSet()
        assert s.erode(Interval.empty()) == IntervalSet()
        assert s.erode(IntervalSet()) == IntervalSet()
        with pytest.raises(TypeError):
            s.erode("not supported")

    def test_morphology_1d(self):
        # dilate_epsilon(0)
        s = IntervalSet.point(5)
        assert s.dilate_epsilon(0) == s

        # dilate_epsilon(1) (Line 1397)
        res_eps = s.dilate_epsilon(1.0)
        assert res_eps == Interval.closed(4, 6)

        # Opening/Closing
        s2 = IntervalSet([Interval(0, 0.5), Interval(1, 10)])
        b = Interval.closed(0, 1)
        assert s2.opening(b) == Interval.closed(1, 10)

        s3 = IntervalSet([Interval(0, 1), Interval(1.1, 2)])
        b2 = Interval.closed(0, 0.2)
        assert s3.closing(b2) == Interval.closed(0, 2)

    def test_cross_type_equality(self):
        # IntervalSet vs Interval
        i = Interval.closed(0, 1)
        s = IntervalSet([i])
        assert s == i
        assert i == s
        assert s != Interval.closed(0, 2)
        assert s != "not a set"


class TestMinkowskiND:
    def test_box_minkowski(self):
        b1 = Box([Interval.closed(0, 1), Interval.closed(0, 1)])
        # Scalar shift
        assert b1 + 10 == Box([Interval.closed(10, 11), Interval.closed(10, 11)])

        # Reverse scalar shift (Line 254)
        assert 10 + b1 == b1 + 10

        # Vector shift
        res_v = b1 + [10, 20]
        assert res_v.intervals[0] == Interval.closed(10, 11)

        # dilate alias (Line 244)
        assert b1.dilate(10) == b1 + 10

        # Vector dimension mismatch (Line 191)
        with pytest.raises(ValueError):
            b1 + [10]

        # Box mismatch (Line 209)
        with pytest.raises(ValueError):
            b1 + Box([Interval(0, 1)])

        # Type error (Line 203)
        with pytest.raises(TypeError):
            b1 + "not a box"

        # Empty
        assert Box.empty(2).minkowski_sum(b1).is_empty()  # Line 184
        assert b1.minkowski_sum(Box.empty(2)).is_empty()  # Line 206 (formerly 201)

        # Erosion
        assert b1.erode(Box([Interval(0, 0.5), Interval(0, 0.5)])) == Box(
            [Interval(0, 0.5), Interval(0, 0.5)]
        )

        # Erosion empty self (Line 222)
        assert Box.empty(2).erode(b1).is_empty()

        # Erosion type error (Line 225)
        with pytest.raises(TypeError):
            b1.erode("not a box")

        # Erosion mismatch (Line 231)
        with pytest.raises(ValueError):
            b1.erode(Box([Interval(0, 1)]))

        # Erosion result empty (Line 237)
        assert b1.erode(Box([Interval(0, 10), Interval(0, 10)])).is_empty()

        # Box equality False (Line 261)
        assert b1 != [0, 1, 0, 1]

        # Box len and iter (Line 268, 272)
        assert len(b1) == 2
        ints = list(iter(b1))
        assert ints[0] == Interval.closed(0, 1)

    def test_set_minkowski(self):
        s = Set([Box([Interval(0, 1), Interval(0, 1)])])

        # Scalar/sequence shift (Line 673)
        assert (s + 10) == Set([Box([Interval(10, 11), Interval(10, 11)])])
        assert (s + [10, 20]) == Set([Box([Interval(10, 11), Interval(20, 21)])])

        # Reverse scalar shift (Line 753)
        assert (10 + s) == (s + 10)

        # Empty self (Line 669)
        assert Set().minkowski_sum(Box([Interval(0, 1)])) == Set()
        # Other empty (Line 679)
        assert s.minkowski_sum(Set()) == Set()

        # Erosion coverage
        assert Set().erode(Box([Interval(0, 1)])) == Set()  # Empty result
        assert (
            Set().erode(Box([Interval(0, 1), Interval(0, 1)])) == Set()
        )  # empty self coverage?
        assert s.erode(Interval.empty()) == Set()  # Line 692

        # Erosion by Interval promotion (Line 702)
        s_1d = Set([Box([Interval(0, 10)])])
        res_e_1d = s_1d.erode(Interval.closed(0, 1))
        assert res_e_1d == Box([Interval.closed(0, 9)])

        # Erosion result inclusion check (Line 707)
        # Create a set with two boxes, one too small for erosion
        s_mixed = Set(
            [
                Box([Interval(0, 10), Interval(0, 10)]),
                Box([Interval(20, 21), Interval(20, 21)]),
            ]
        )
        res_mixed = s_mixed.erode(Box([Interval(0, 5), Interval(0, 5)]))
        assert len(res_mixed.boxes) == 1

        # Erosion by Set
        s_other = Set(
            [
                Box([Interval(0, 1), Interval(0, 1)]),
                Box([Interval(5, 6), Interval(5, 6)]),
            ]
        )
        res_e_set = s_mixed.erode(s_other)
        assert len(res_e_set.boxes) == 1  # (s_mixed - B1) & (s_mixed - B2)

        # Coverage for Box.distance overlap/adjacency (Line 270)
        b_adj1 = Box([Interval(0, 1)])
        b_adj2 = Box([Interval(1, 2)])
        assert b_adj1.distance(b_adj2) == 0.0

        # dilate_epsilon
        s_eps = Set([Box([Interval(0, 1), Interval(0, 1)])])
        assert s_eps.dilate_epsilon(0) == s_eps
        s_eps_res = s_eps.dilate_epsilon(1.0)
        assert s_eps_res.volume() == 9.0  # [-1, 2] x [-1, 2] = 3 * 3 = 9
        assert Set().dilate_epsilon(1.0) == Set()

        # Opening/Closing aliases
        box_big = Box([Interval(0, 10), Interval(0, 10)])
        box_small = Box([Interval(0, 1), Interval(0, 1)])
        s_big = Set([box_big])
        assert s_big.opening(box_small) == box_big
        assert s_big.closing(box_small) == box_big

        # Coverage for Set.minkowski_sum promotion and pairwise
        s_base = Set([Box([Interval(0, 1)])])
        s_sum = s_base.minkowski_sum(Box([Interval(0, 1)]))  # Promote Box
        assert s_sum.volume() == 2.0

        s_pair1 = Set([Box([Interval(0, 1)])])
        s_pair2 = Set([Box([Interval(2, 3)])])
        s_pair_sum = s_pair1.dilate(s_pair2)  # dilate alias
        assert s_pair_sum.volume() == 2.0

        # TypeError for erosion
        import pytest

        with pytest.raises(TypeError):
            s_base.erode("not a set")

        # Early break in erosion
        s_breakable = Set([Box([Interval(0, 1)])])
        s_other_breakable = Set(
            [
                Box([Interval(10, 11)]),  # Result empty
                Box([Interval(0, 1)]),  # Should be skipped by break
            ]
        )
        assert s_breakable.erode(s_other_breakable).is_empty()

    def test_containment_nd(self):
        b1 = Box([Interval(0, 10), Interval(0, 10)])
        b2 = Box([Interval(1, 2), Interval(1, 2)])
        b_outside = Box([Interval(11, 12), Interval(11, 12)])

        # Box mismatch in contains
        assert b1.contains(Box([Interval(0, 1)])) is False

        # Box in Box
        assert b2 in b1
        assert b1 not in b2
        assert Box.empty(2) in b1
        assert b2 not in Box.empty(2)

        # Set in Box
        s2 = Set([b2])
        assert s2 in b1
        assert Set() in b1

        # Box in Set
        s1 = Set([b1])
        assert b2 in s1
        assert Box.empty(2) in s1
        assert b_outside not in s1

        # Set empty in empty contains
        assert Box.empty(2) in Set()

        # Set in Set
        assert s2 in s1
        assert Set() in s1

        # Dimension mismatch in Set equality
        assert Set([Box([Interval(0, 1)])]) != Set(
            [Box([Interval(0, 1), Interval(0, 1)])]
        )

        # __contains__ for Box
        assert [5, 5] in b1

        # Box not empty in empty Set contains
        assert b1 not in Set()

    def test_coverage_gap_fill(self):
        # Box.__eq__ with something having .boxes but not a Set
        class FakeSet:
            def __init__(self):
                self.boxes = []

            def __eq__(self, other):
                return False

        assert Box([Interval(0, 1)]) != FakeSet()

        # Set.minkowski_difference with IntervalSet
        s = Set([Box([Interval(0, 10)])])
        iset = IntervalSet([Interval(0, 1)])
        # Promotion of IntervalSet to Set ensures it's handled.
        assert s.erode(iset) == Box([Interval.closed(0, 9)])

        # Set.minkowski_difference with invalid type
        with pytest.raises(TypeError):
            s.erode("invalid")

        # Set.minkowski_difference with empty set
        # Erosion by empty set is Set() in our implementation
        assert s.erode(Set()) == Set()

        # Set.minkowski_difference premature break
        s_2d = Set([Box([Interval(0, 1), Interval(0, 1)])])
        s_other = Set(
            [
                Box([Interval(0, 0.5), Interval(0, 0.5)]),
                Box([Interval(10, 11), Interval(10, 11)]),
            ]
        )
        # Erosion by B1 is [0, 0.5]x[0, 0.5]
        # Erosion by B2 is empty, so res becomes empty and loop breaks.
        assert s_2d.erode(s_other).is_empty()

        # Set.__eq__ with non-Set
        assert Set() != "not a set"

        # Box.minkowski_difference with empty box
        b1 = Box([Interval(0, 1)])
        assert b1.erode(Box.empty(1)).is_empty()

    def test_intervalset_minkowski_diff_returns_single_interval(self):
        # A = [0, 10], B = [1, 2]
        # Result [-1, 8]
        s1 = IntervalSet([Interval(0, 10)])
        s2 = IntervalSet([Interval(1, 2)])
        diff = s1.minkowski_difference(s2)
        assert isinstance(diff, IntervalSet)
        assert len(diff) == 1
        assert diff._intervals[0] == Interval(-1, 8)

    def test_intervalset_opening_promotion(self):
        # Opening = dilate(erode(A, B), B)
        s1 = IntervalSet([Interval(0, 10)])
        s2 = IntervalSet([Interval(1, 2)])
        opened = s1.opening(s2)
        assert isinstance(opened, IntervalSet)
        assert opened == s1

    def test_intervalset_closing_promotion(self):
        # Closing = erode(dilate(A, B), B)
        s1 = IntervalSet([Interval(0, 1)])
        s2 = IntervalSet([Interval(2, 3)])
        closed = s1.closing(s2)
        assert isinstance(closed, IntervalSet)
        assert closed == s1
