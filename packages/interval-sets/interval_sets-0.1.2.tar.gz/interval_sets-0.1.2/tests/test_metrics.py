from src.intervals import IntervalSet, Interval


def test_distance_metric():
    # Distance between intervals
    # [0, 1] and [2, 3] -> distance 1
    i1 = Interval(0, 1)
    i2 = Interval(2, 3)
    assert i1.distance(i2) == 1.0

    # Overlapping -> 0
    i3 = Interval(0, 5)
    i4 = Interval(2, 6)
    assert i3.distance(i4) == 0.0

    # Touching -> 0
    i5 = Interval(0, 1)
    i6 = Interval(1, 2)
    assert i5.distance(i6) == 0.0


def test_hausdorff_distance():
    # Hausdorff distance
    # A = [0, 1], B = [0, 2]
    # d(A, B): sup_{x in A} d(x, B) -> for all x in [0,1], dist is 0. max 0.
    # d(B, A): sup_{y in B} d(y, A) -> for [0, 1] dist is 0. for (1, 2] dist increases to 1. max 1.
    # Result 1.
    s1 = IntervalSet([Interval(0, 1)])
    s2 = IntervalSet([Interval(0, 2)])
    assert s1.hausdorff_distance(s2) == 1.0

    # A = [0, 1], B = [2, 3]
    # directed(A, B): 0->2 (dist 2), 1->2 (dist 1). max 2.
    # directed(B, A): 2->1 (dist 1), 3->1 (dist 2). max 2.
    # Result 2.
    s3 = IntervalSet([Interval(0, 1)])
    s4 = IntervalSet([Interval(2, 3)])
    assert s3.hausdorff_distance(s4) == 2.0

    # Infinite case
    # A = (-inf, 0], B = (-inf, 10]
    # directed(A, B): -inf->-inf (0), 0->in B (0). max 0.
    # directed(B, A): -inf->-inf (0), 10->0 (dist 10). max 10.
    # Result 10.
    s5 = IntervalSet([Interval(float("-inf"), 0)])
    s6 = IntervalSet([Interval(float("-inf"), 10)])
    assert s5.hausdorff_distance(s6) == 10.0


def test_distance_edge_cases():
    """Test edge cases for IntervalSet distance."""
    s1 = IntervalSet([Interval(0, 1)])
    empty = IntervalSet()

    # Distance to empty set is infinite
    assert s1.distance(empty) == float("inf")
    assert empty.distance(s1) == float("inf")

    # Distance between disjoint sets (min gap)
    s2 = IntervalSet([Interval(2, 3)])
    assert s1.distance(s2) == 1.0

    # Distance with multiple intervals (min gap found)
    # s1=[0,1], s3=[2,3]U[5,6]
    s3 = IntervalSet([Interval(2, 3), Interval(5, 6)])
    assert s1.distance(s3) == 1.0


def test_hausdorff_infinite_bounds_edge_cases():
    """Test Hausdorff distance edge cases for infinite bounds."""
    # Source has -inf, Target does not
    s_inf_start = IntervalSet([Interval(float("-inf"), 0)])
    s_bounded = IntervalSet([Interval(0, 10)])

    # directed(s_inf_start, s_bounded) -> inf
    assert s_inf_start.hausdorff_distance(s_bounded) == float("inf")

    # Source has inf, Target does not
    s_inf_end = IntervalSet([Interval(0, float("inf"))])

    # directed(s_inf_end, s_bounded) -> inf
    assert s_inf_end.hausdorff_distance(s_bounded) == float("inf")


def test_distance_to_point_edge_cases():
    """Test distance_to_point edge cases."""
    s = IntervalSet([Interval(0, 10)])
    empty = IntervalSet()

    # Empty set -> inf
    assert empty.distance_to_point(5) == float("inf")

    # Inside -> 0 (covered)

    # Left -> positive
    assert s.distance_to_point(-5) == 5.0

    # Right -> positive
    assert s.distance_to_point(15) == 5.0

    # Inside logic fallback (hit by open boundary)
    # Open interval (0, 10). Point 0 is not contained, but distance is 0.
    s_open = IntervalSet([Interval(0, 10, open_start=True)])
    assert 0 not in s_open
    assert s_open.distance_to_point(0) == 0.0

    # Same for end
    s_open_end = IntervalSet([Interval(0, 10, open_end=True)])
    assert 10 not in s_open_end
    assert s_open_end.distance_to_point(10) == 0.0


def test_metrics_final_coverage():
    """Cover remaining metric edge cases."""
    # Interval distance reverse case (other < self)
    i1 = Interval(10, 15)
    i2 = Interval(0, 5)
    assert i1.distance(i2) == 5.0

    # Interval distance disjoint but start==end open (gap 0)
    i3 = Interval(0, 5, open_end=True)
    i4 = Interval(5, 10, open_start=True)
    assert i3.distance(i4) == 0.0

    # IntervalSet distance overlapping
    s1 = IntervalSet([Interval(0, 10)])
    s2 = IntervalSet([Interval(5, 15)])
    assert s1.distance(s2) == 0.0

    # Hausdorff empty
    s3 = IntervalSet([Interval(0, 1)])
    empty = IntervalSet()
    assert s3.hausdorff_distance(empty) == float("inf")

    # Hausdorff both infinite
    s4 = IntervalSet([Interval(0, float("inf"))])
    s5 = IntervalSet([Interval(10, float("inf"))])
    assert s4.hausdorff_distance(s5) == 10.0

    # distance_to_point missing update branch
    # We need a set where first interval gives min_dist, second gives LARGER dist (so no update)
    # Intervals are sorted by start.
    # [0, 2], [10, 12]. Point -5.
    # [0, 2] -> 5.0. min=5.0
    # [10, 12] -> 15.0. 15 < 5 False.
    s6 = IntervalSet([Interval(0, 2), Interval(10, 12)])
    assert s6.distance_to_point(-5) == 5.0
