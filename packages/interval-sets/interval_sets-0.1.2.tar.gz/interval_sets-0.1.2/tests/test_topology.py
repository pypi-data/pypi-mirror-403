import math
from src.intervals import Interval, Point, IntervalSet
from src.multidimensional import Box, Set


class TestTopology1D:
    def test_interval_interior_closure(self):
        # [0, 10]
        i = Interval.closed(0, 10)
        assert i.interior() == Interval.open(0, 10)
        assert i.closure() == Interval.closed(0, 10)

        # (0, 10)
        i2 = Interval.open(0, 10)
        assert i2.interior() == Interval.open(0, 10)
        assert i2.closure() == Interval.closed(0, 10)

        # [0, 5)
        i3 = Interval.right_open(0, 5)
        assert i3.interior() == Interval.open(0, 5)
        assert i3.closure() == Interval.closed(0, 5)

    def test_point_topology(self):
        p = Point(5)
        assert p.interior().is_empty()
        assert p.closure() == p
        assert p.boundary().volume() == 0.0  # It's a point set
        assert 5 in p.boundary()

    def test_interval_boundary(self):
        i = Interval.closed(0, 10)
        b = i.boundary()
        assert isinstance(b, IntervalSet)
        assert b.volume() == 0.0
        assert 0 in b
        assert 10 in b
        assert 5 not in b

        # Unbounded
        i_inf = Interval(0, float("inf"))
        b_inf = i_inf.boundary()
        assert 0 in b_inf
        assert not math.isinf(list(b_inf)[0].start)

    def test_interval_set_topology(self):
        s = IntervalSet([Interval(0, 2), Interval(4, 6)])

        # Interior
        int_s = s.interior()
        assert Interval.open(0, 2) in int_s
        assert Interval.open(4, 6) in int_s
        assert 0 not in int_s
        assert 2 not in int_s

        # Closure
        cl_s = s.closure()
        assert 0 in cl_s
        assert 2 in cl_s

        # Boundary
        bound_s = s.boundary()
        assert 0 in bound_s
        assert 2 in bound_s
        assert 4 in bound_s
        assert 6 in bound_s
        assert 1 not in bound_s


class TestTopologyND:
    def test_box_topology(self):
        # 2D Unit Square [0, 1]x[0, 1]
        b = Box([Interval.closed(0, 1), Interval.closed(0, 1)])

        # Interior
        int_b = b.interior()
        assert int_b.intervals[0].open_start
        assert int_b.intervals[0].open_end
        assert int_b.contains((0.5, 0.5))
        assert not int_b.contains((0, 0))

        # Closure
        cl_b = b.closure()
        assert not cl_b.intervals[0].open_start
        assert cl_b.contains((0, 0))

        # Boundary
        bound_b = b.boundary()
        assert (
            bound_b.volume() == 0.0
        )  # Mathematical 2D boundary of 2D box has 0 volume
        # (0, 0) is on boundary
        assert (0, 0) in bound_b
        # (0.5, 0.5) is NOT on boundary
        assert (0.5, 0.5) not in bound_b
        # (0.5, 1) IS on boundary
        assert (0.5, 1) in bound_b

    def test_set_topology(self):
        # L-shape
        v = Box([Interval(0, 1), Interval(0, 2)])
        h = Box([Interval(0, 2), Interval(0, 1)])
        l_shape = Set([v, h])

        # Boundary of L-shape should NOT contain the internal shared part [0,1]x[0,1]
        bound_l = l_shape.boundary()
        assert (0.5, 0.5) not in bound_l
        assert (0, 0) in bound_l
        assert (2, 0.5) in bound_l  # Outer edge of horizontal part
        assert (0.5, 2) in bound_l  # Outer edge of vertical part
        assert (1.5, 1) in bound_l  # "Top" edge of horizontal part (extended)

        # (1, 1) is a corner of the interior shared part, still on boundary
        assert (1, 1) in bound_l

    def test_connectivity(self):
        # Connected: Two touching boxes
        b1 = Box([Interval(0, 1), Interval(0, 1)])
        b2 = Box([Interval(1, 2), Interval(0, 1)])  # Side-by-side
        s = Set([b1, b2])
        assert s.is_connected()
        assert len(s.connected_components()) == 1

        # Disconnected: Gap between boxes
        b3 = Box([Interval(3, 4), Interval(0, 1)])
        s2 = s | b3
        assert not s2.is_connected()
        assert len(s2.connected_components()) == 2

        # Empty set is connected
        assert Set().is_connected()
        assert Set().connected_components() == []

    def test_box_equality(self):
        """Cover Box.__eq__."""
        b1 = Box([Interval(0, 1)])
        b2 = Box([Interval(0, 1)])
        b3 = Box([Interval(0, 2)])
        assert b1 == b2
        assert b1 != b3
        assert b1 != "not a box"

    def test_empty_topology(self):
        # 1D Set
        s = IntervalSet()
        assert s.interior().is_empty()
        assert s.closure().is_empty()
        assert s.boundary().is_empty()

        # 1D Interval
        i_empty = Interval.empty()
        assert i_empty.interior().is_empty()
        assert i_empty.closure().is_empty()
        assert i_empty.boundary().is_empty()

        # N-D Box
        b = Box([Interval.empty()])
        assert b.interior().is_empty()
        assert b.closure().is_empty()
        assert b.boundary().is_empty()

        # N-D Set
        ns = Set()
        assert ns.interior().is_empty()
        assert ns.closure().is_empty()
        assert ns.boundary().is_empty()

    def test_unbounded_boundary(self):
        """Cover isinf checks in boundary."""
        # (-inf, inf) has NO boundary points
        i = Interval(float("-inf"), float("inf"))
        assert i.boundary().is_empty()

        # [0, inf) has ONE boundary point
        i2 = Interval(0, float("inf"))
        b2 = i2.boundary()
        assert 0 in b2
        assert len(b2) == 1

    def test_interval_set_boundary_singleton(self):
        """Cover Line 1196: if isinstance(diff, Interval): return IntervalSet([diff])."""
        # A single point [5, 5] has boundary {5} which is one point interval.
        s = IntervalSet.point(5)
        b = s.boundary()
        assert isinstance(b, IntervalSet)
        assert len(b) == 1
        assert 5 in b

    def test_interval_operators_coverage(self):
        """Cover 556, 566, 575, 579-582 in src/intervals.py."""
        i1 = Interval.closed(0, 5)
        i2 = Interval.closed(10, 15)

        # repr (556)
        assert "[0.0, 5.0]" in repr(i1)

        # operator | (566)
        res_or = i1 | i2
        assert len(res_or) == 2

        # operator ^ (575, 579-582)
        res_xor = i1 ^ i2
        assert len(res_xor) == 2
        assert 2.5 in res_xor
        assert 12.5 in res_xor
