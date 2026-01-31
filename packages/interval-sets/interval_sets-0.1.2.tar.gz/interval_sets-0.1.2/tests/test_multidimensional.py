import pytest
from src.intervals import Interval
from src.multidimensional import Box


class TestBoxBasic:
    def test_initialization(self):
        i1 = Interval(0, 5)
        i2 = Interval(0, 5)
        b = Box([i1, i2])
        assert b.dimension == 2
        assert len(b.intervals) == 2
        assert str(b) == f"Box([{repr(i1)}, {repr(i2)}])"

    def test_empty_box(self):
        # One dimension empty -> Box empty
        b = Box([Interval.empty(), Interval(0, 5)])
        assert b.is_empty()
        assert b.volume() == 0.0

    def test_volume_2d(self):
        # 5x5 square
        b = Box([Interval(0, 5), Interval(0, 5)])
        assert b.volume() == 25.0

    def test_volume_3d_degenerate_point(self):
        # Point in 3D: [1,1] x [2,2] x [3,3]
        b = Box([Interval.point(1), Interval.point(2), Interval.point(3)])
        assert b.volume() == 0.0

    def test_contains_point(self):
        b = Box([Interval(0, 5), Interval(0, 10)])
        assert b.contains((1, 1))
        assert b.contains((0, 0))  # Inclusive closed boundaries
        assert not b.contains((-1, 5))
        assert not b.contains((2, 11))

    def test_contains_dimension_mismatch(self):
        b = Box([Interval(0, 1)])
        with pytest.raises(ValueError, match="must match Box dimension"):
            b.contains((1, 2))

    def test_overlaps(self):
        b1 = Box([Interval(0, 5), Interval(0, 5)])
        # Overlaps
        b2 = Box([Interval(4, 6), Interval(4, 6)])
        assert b1.overlaps(b2)

        # Disjoint in x
        b3 = Box([Interval(6, 10), Interval(0, 5)])
        assert not b1.overlaps(b3)

        # Disjoint in y
        b4 = Box([Interval(0, 5), Interval(6, 10)])
        assert not b1.overlaps(b4)

    def test_intersection(self):
        # Intersect two 2D boxes
        # [0, 5]x[0, 5] AND [3, 8]x[3, 8] -> [3, 5]x[3, 5]
        b1 = Box([Interval(0, 5), Interval(0, 5)])
        b2 = Box([Interval(3, 8), Interval(3, 8)])

        inter = b1.intersection(b2)
        assert inter.intervals[0] == Interval(3, 5)
        assert inter.intervals[1] == Interval(3, 5)
        assert inter.dimension == 2

    def test_intersection_disjoint(self):
        b1 = Box([Interval(0, 1)])
        b2 = Box([Interval(2, 3)])
        inter = b1.intersection(b2)
        assert inter.is_empty()

    def test_difference_no_overlap(self):
        # A=[0,5], B=[10,15] -> A \ B = {A}
        a = Box([Interval(0, 5)])
        b = Box([Interval(10, 15)])
        diff = a.difference(b)
        assert len(diff) == 1
        assert diff[0] == a

    def test_difference_contained(self):
        # A=[0,10], B=[0,10] -> Empty
        a = Box([Interval(0, 10)])
        b = Box([Interval(0, 10)])
        diff = a.difference(b)
        assert len(diff) == 0

    def test_difference_2d_hole(self):
        # A = [0, 10]x[0, 10]
        # B = [3, 7]x[3, 7]
        # Partial overlap in center
        # Slices:
        # Dim x:
        #   Left: [0, 3) x [0, 10]
        #   Right: (7, 10] x [0, 10]
        #   Middle constraint: [3, 7] x [0, 10]
        # Dim y (applied to middle x):
        #   Bottom: [3, 7] x [0, 3)
        #   Top: [3, 7] x (7, 10]

        a = Box([Interval(0, 10), Interval(0, 10)])
        b = Box([Interval(3, 7), Interval(3, 7)])

        diff = a.difference(b)
        # Should have 4 boxes
        assert len(diff) == 4

        # Verify total volume
        # A vol = 100. B vol = 16. Diff vol = 84.
        total_vol = sum(box.volume() for box in diff)
        assert total_vol == 84.0

        # Verify disjointness
        for i, b1 in enumerate(diff):
            for j, b2 in enumerate(diff):
                if i != j:
                    assert not b1.overlaps(b2)

    def test_difference_edge_slice(self):
        # A = [0, 10]
        # B = [5, 10] (Right half)
        # A \ B = [0, 5)
        a = Box([Interval(0, 10)])
        b = Box([Interval(5, 10)])

        diff = a.difference(b)
        assert len(diff) == 1
        assert diff[0].intervals[0] == Interval(0, 5, open_end=True)
