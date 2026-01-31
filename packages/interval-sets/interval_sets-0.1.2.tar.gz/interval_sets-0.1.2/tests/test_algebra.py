from src.intervals import Interval


def test_allen_algebra():
    # Base intervals
    # i1: [0, 5]
    # i2: [5, 10]
    # i3: [2, 7]
    # i4: [1, 4]
    # i5: [0, 6]
    # i6: [-2, 0)

    i1 = Interval(0, 5)
    i2 = Interval(5, 10)
    i3 = Interval(2, 7)
    i4 = Interval(1, 4)
    i5 = Interval(0, 6)
    i7 = Interval(10, 15)

    # Meets
    # [0, 5] does NOT meet [5, 10] because they share point 5 (overlap).
    assert not i1.meets(i2)
    assert not i2.met_by(i1)

    # [0, 5] matches (5, 10] -> Adjacent and Disjoint -> Meets
    i2_open = Interval(5, 10, open_start=True)
    assert i1.meets(i2_open)
    assert i2_open.met_by(i1)

    # Precedes
    assert i1.precedes(i7)  # [0, 5] < [10, 15]
    assert i7.preceded_by(i1)

    # Overlaps (strict)
    # [0, 5] overlaps [2, 7]
    assert i1.overlaps_strictly(i3)
    assert i3.overlapped_by(i1)

    # Starts
    # [0, 5] starts [0, 6]
    assert i1.starts(i5)
    assert i5.started_by(i1)

    # During
    # [1, 4] during [0, 5]
    assert i4.during(i1)
    assert i1.contains_strictly(i4)

    # Finishes
    # [2, 5] finishes [0, 5]
    i8 = Interval(2, 5)
    assert i8.finishes(i1)
    assert i1.finished_by(i8)

    # Equals
    i9 = Interval(0, 5)
    assert i1.equals(i9)


def test_precedes_strictness():
    # [0, 2) and [2, 4]
    i1 = Interval(0, 2, open_end=True)
    i2 = Interval(2, 4)
    # i1 ends at 2 (open), i2 starts at 2 (closed).
    # They are adjacent -> i1 meets i2
    assert i1.meets(i2)
    assert not i1.precedes(i2)

    # [0, 1] and [2, 3] -> Precedes
    i3 = Interval(0, 1)
    i4 = Interval(2, 3)
    assert i3.precedes(i4)
    assert not i3.meets(i4)


def test_algebra_false_branches():
    """Cover False branches in Allen algebra methods."""
    # Precedes False (overlap)
    i1 = Interval(0, 10)
    i2 = Interval(5, 15)
    assert not i1.precedes(i2)

    # Overlaps Strictly False (disjoint)
    i3 = Interval(0, 5)
    i4 = Interval(10, 15)
    assert not i3.overlaps_strictly(i4)
