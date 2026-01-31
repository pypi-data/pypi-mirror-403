"""Core classes for interval arithmetic and set operations."""

import math
from typing import Union, List, Optional, Iterator, Iterable
from .errors import InvalidIntervalError
from .utils import intervals_are_adjacent


class Interval:
    """
    Represents a single continuous interval on the real number line.

    An interval is defined by its start and end points, and whether each boundary
    is open or closed. This class replaces ContinuousInterval with a cleaner API.

    Examples:
        >>> Interval(0, 5)          # [0, 5] - closed interval
        >>> Interval(0, 5, open_start=True)  # (0, 5] - open start
        >>> Interval(0, 5, open_end=True)    # [0, 5) - open end
        >>> Interval(0, 5, open_start=True, open_end=True)  # (0, 5) - open interval
        >>> Interval(0, 5, open_start=True, open_end=True)  # (0, 5) - open interval
        >>> Point(5)                # [5, 5] - degenerate interval (point)
    """

    def __init__(
        self,
        start: float,
        end: float,
        *,
        open_start: bool = False,
        open_end: bool = False,
    ):
        """
        Create a new interval.

        Args:
            start: The start point of the interval
            end: The end point of the interval
            open_start: Whether the start boundary is open
            open_end: Whether the end boundary is open

        Raises:
            InvalidIntervalError: If start > end or invalid boundary conditions
            ValueError: If start or end is NaN or infinite
        """
        # Convert to float and validate
        start = float(start)
        end = float(end)

        # Validate numeric values
        if math.isnan(start) or math.isnan(end):
            raise ValueError("Interval boundaries cannot be NaN")
        # Infinite boundaries are allowed, but usually treated as open in R

        # Enforce open boundaries for infinity to adhere to R topology
        if math.isinf(start) and start < 0:
            open_start = True
        if math.isinf(end) and end > 0:
            open_end = True

        # Validate interval bounds
        if start > end:
            raise InvalidIntervalError(
                f"Invalid interval: start ({start}) must be <= end ({end})"
            )

        # Normalize any empty interval (start==end and open) to canonical (0, 0)
        # This handles (inf, inf) and prevents issues with is_empty() checks
        if start == end and (open_start or open_end):
            start = 0.0
            end = 0.0
            open_start = True
            open_end = True

        self._start = start
        self._end = end
        self._open_start = open_start
        self._open_end = open_end

    @classmethod
    def point(cls, value: float) -> "Interval":
        """
        Create a degenerate interval representing a single point.

        Args:
            value: The point value

        Returns:
            An interval [value, value]
        """
        return Point(value)

    @classmethod
    def empty(cls) -> "Interval":
        """
        Create an empty interval.

        Returns:
            The empty interval (0, 0)
        """
        return cls(0, 0, open_start=True, open_end=True)

    @classmethod
    def open(cls, start: float, end: float) -> "Interval":
        """Create an open interval (start, end)."""
        return cls(start, end, open_start=True, open_end=True)

    @classmethod
    def closed(cls, start: float, end: float) -> "Interval":
        """Create a closed interval [start, end]."""
        return cls(start, end, open_start=False, open_end=False)

    @classmethod
    def left_open(cls, start: float, end: float) -> "Interval":
        """Create a left-open interval (start, end]."""
        return cls(start, end, open_start=True, open_end=False)

    @classmethod
    def right_open(cls, start: float, end: float) -> "Interval":
        """Create a right-open interval [start, end)."""
        return cls(start, end, open_start=False, open_end=True)

    # Properties
    @property
    def start(self) -> float:
        """The start point of the interval."""
        return self._start

    @property
    def end(self) -> float:
        """The end point of the interval."""
        return self._end

    @property
    def open_start(self) -> bool:
        """Whether the start boundary is open."""
        return self._open_start

    @property
    def open_end(self) -> bool:
        """Whether the end boundary is open."""
        return self._open_end

    def is_empty(self) -> bool:
        """Check if this interval is empty."""
        return self._start == self._end == 0 and self._open_start and self._open_end

    def is_point(self) -> bool:
        """Check if this interval represents a single point."""
        return (
            self._start == self._end
            and not self._open_start
            and not self._open_end
            and not self.is_empty()
        )

    def length(self) -> float:
        """Get the length of the interval."""
        if self.is_empty():
            return 0.0
        return self._end - self._start

    def is_bounded(self) -> bool:
        """Check if the interval is bounded (neither end is infinite)."""
        if self.is_empty():
            return True
        return not math.isinf(self._start) and not math.isinf(self._end)

    def is_open(self) -> bool:
        """Check if the interval is open."""
        return not self.is_empty() and self == self.interior()

    def is_closed(self) -> bool:
        """Check if the interval is closed."""
        return not self.is_empty() and self == self.closure()

    def is_compact(self) -> bool:
        """Check if the interval is compact (closed and bounded)."""
        return self.is_closed() and self.is_bounded()

    def contains(self, value: Union[float, "Interval"]) -> bool:
        """
        Check if this interval contains a value or another interval.

        Args:
            value: A numeric value or another Interval

        Returns:
            True if the value/interval is contained within this interval
        """
        if isinstance(value, (int, float)):
            return self._contains_value(value)
        elif isinstance(value, Interval):
            return self._contains_interval(value)
        else:
            return False

    def _contains_value(self, value: float) -> bool:
        """Check if interval contains a numeric value."""
        if self.is_empty():
            return False

        # Check bounds
        if value < self._start or value > self._end:
            return False

        # Check boundaries
        if value == self._start and self._open_start:
            return False
        if value == self._end and self._open_end:
            return False

        return True

    def _contains_interval(self, other: "Interval") -> bool:
        """Check if this interval completely contains another interval."""
        if self.is_empty() or other.is_empty():
            return other.is_empty()

        # Check if other's bounds are within our bounds
        if other._start < self._start or other._end > self._end:
            return False

        # Check boundary conditions
        if other._start == self._start:
            if self._open_start and not other._open_start:
                return False

        if other._end == self._end:
            if self._open_end and not other._open_end:
                return False

        return True

    def overlaps(self, other: "Interval") -> bool:
        """
        Check if this interval overlaps with another interval.

        Args:
            other: Another interval

        Returns:
            True if the intervals overlap or touch
        """
        if self.is_empty() or other.is_empty():
            return False

        # Check for touching intervals first
        if self._end == other._start:
            return not (self._open_end or other._open_start)
        if other._end == self._start:
            return not (other._open_end or self._open_start)

        # Check for general overlap
        return not (self._end < other._start or other._end < self._start)

    def is_adjacent(self, other: "Interval") -> bool:
        """Check if intervals are adjacent (touching but not overlapping)."""
        return intervals_are_adjacent(self, other)

    def distance(self, other: "Interval") -> float:
        """
        Compute the Euclidean distance between this interval and another.
        Returns 0.0 if they overlap or touch.
        """
        if self.overlaps(other) or self.is_adjacent(other):
            return 0.0

        # If disjoint, distance is gap between them
        if self._end < other._start:
            return other._start - self._end
        elif other._end < self._start:
            return self._start - other._end

        return 0.0  # Should be covered above

    # --- Allen's Interval Algebra Relations ---

    def precedes(self, other: "Interval") -> bool:
        """
        Allen's 'precedes' (b): Self is strictly before other.
        """
        # End < Start (with boundary checks)
        if self._end < other._start:
            return True
        if self._end == other._start:
            # strictly before means no shared point.
            # If touching, it's 'meets', unless both open/etc makes them separated?
            # 'precedes' implies a gap or at least no touch?
            # Usually Allen's 'before' means end < start.
            # If end == start, it's 'meets' if they touch, or 'before' if there is a gap (e.g. open-open)?
            # In continuous reals, (0,1) and (1,2) has a 'gap' of size 0 but no point.
            # We treat strict < as precedes.
            # If they touch (is_adjacent), it is 'meets'.
            return not self.is_adjacent(other) and self.intersection(other).is_empty()
        return False

    def meets(self, other: "Interval") -> bool:
        """
        Allen's 'meets' (m): Self touches other, end to start.
        Equivalent to is_adjacent where self is on the left, but MUST be disjoint (no overlap).
        """
        if not (self._end == other._start and self.is_adjacent(other)):
            return False

        # Allen's meets requires disjointness.
        # [0, 5] and [5, 10] overlap at 5, so strictly they 'overlap' not 'meet'.
        # [0, 5] and (5, 10] meet.
        return self.intersection(other).is_empty()

    def overlaps_strictly(self, other: "Interval") -> bool:
        """
        Allen's 'overlaps' (o): Self starts before other, ends inside other.
        Distinguished from general 'overlaps()' which means 'intersects'.
        """
        if not self.overlaps(other):
            return False
        # strict overlap: start1 < start2 < end1 < end2
        # We need to handle equalities carefully with start/end points
        # But conceptually: starts before, ends during.

        # Condition 1: Self starts strictly before Other
        # (Or starts same place but includes points before? complex with boundaries)
        # Simplified: self.start < other.start (lexicographical with openness)

        starts_before = (self._start < other._start) or (
            self._start == other._start and not self._open_start and other._open_start
        )

        # Condition 2: Self ends strictly before Other
        ends_before = (self._end < other._end) or (
            self._end == other._end and self._open_end and not other._open_end
        )

        # Condition 3: They must intersect (already checked)

        return starts_before and ends_before

    def starts(self, other: "Interval") -> bool:
        """
        Allen's 'starts' (s): Self and other start together, self ends earlier.
        """
        same_start = (
            self._start == other._start and self._open_start == other._open_start
        )
        ends_earlier = (self._end < other._end) or (
            self._end == other._end and self._open_end and not other._open_end
        )
        return same_start and ends_earlier

    def during(self, other: "Interval") -> bool:
        """
        Allen's 'during' (d): Self is strictly contained in other.
        """
        # Starts later
        starts_later = (self._start > other._start) or (
            self._start == other._start and self._open_start and not other._open_start
        )
        # Ends earlier
        ends_earlier = (self._end < other._end) or (
            self._end == other._end and self._open_end and not other._open_end
        )

        return starts_later and ends_earlier

    def finishes(self, other: "Interval") -> bool:
        """
        Allen's 'finishes' (f): Self ends with other, but starts later.
        """
        starts_later = (self._start > other._start) or (
            self._start == other._start and self._open_start and not other._open_start
        )

        same_end = self._end == other._end and self._open_end == other._open_end

        return starts_later and same_end

    def equals(self, other: "Interval") -> bool:
        """Allen's 'equals' (e)."""
        return self == other

    # Inverses
    def met_by(self, other: "Interval") -> bool:
        """Allen's 'met by' (mi)."""
        return other.meets(self)

    def overlapped_by(self, other: "Interval") -> bool:
        """Allen's 'overlapped by' (oi)."""
        return other.overlaps_strictly(self)

    def started_by(self, other: "Interval") -> bool:
        """Allen's 'started by' (si)."""
        return other.starts(self)

    def contains_strictly(self, other: "Interval") -> bool:
        """Allen's 'contains' (di)."""
        return other.during(self)

    def finished_by(self, other: "Interval") -> bool:
        """Allen's 'finished by' (fi)."""
        return other.finishes(self)

    def preceded_by(self, other: "Interval") -> bool:
        """Allen's 'preceded by' (bi)."""
        return other.precedes(self)

    def intersection(self, other: "Interval") -> Union["Interval", "IntervalSet"]:
        """
        Compute the intersection of this interval with another.

        Returns:
            - An Interval if intersection is a single interval or point
            - A IntervalSet if intersection is empty
        """
        # Import IntervalSet from below in this file

        if not self.overlaps(other):
            return _create_empty_set()  # Empty set

        # Determine intersection bounds
        start = max(self._start, other._start)
        end = min(self._end, other._end)

        if start == self._start and start == other._start:
            open_start = self._open_start or other._open_start
        elif start == self._start:
            open_start = self._open_start
        else:
            open_start = other._open_start

        if end == self._end and end == other._end:
            open_end = self._open_end or other._open_end
        elif end == self._end:
            open_end = self._open_end
        else:
            open_end = other._open_end

        # If intersection is a single point, return appropriately
        if start == end:
            if not open_start and not open_end:
                return Point(start)  # Return point class instance
            return _create_empty_set()  # pragma: no cover

        return Interval(start, end, open_start=open_start, open_end=open_end)

    def union(self, other: "Interval") -> Union["Interval", "IntervalSet"]:
        """
        Compute the union of this interval with another.

        Returns:
            - An Interval if intervals are adjacent/overlapping (can be merged)
            - A IntervalSet containing both intervals if disjoint
        """
        # Import IntervalSet from below in this file

        if not (self.overlaps(other) or self.is_adjacent(other)):
            # Disjoint intervals - return IntervalSet containing both
            return _create_set([self, other])

        # Merge intervals
        start = min(self._start, other._start)
        end = max(self._end, other._end)

        if start == self._start and start == other._start:
            open_start = self._open_start and other._open_start
        elif start == self._start:
            open_start = self._open_start
        else:
            open_start = other._open_start

        if end == self._end and end == other._end:
            open_end = self._open_end and other._open_end
        elif end == self._end:
            open_end = self._open_end
        else:
            open_end = other._open_end

        return Interval(start, end, open_start=open_start, open_end=open_end)

    def difference(self, other: "Interval") -> Union["Interval", "IntervalSet"]:
        """
        Compute the difference of this interval minus another.

        Returns:
            - An Interval if the result is a single interval
            - A IntervalSet if the result is empty, multiple intervals, or a single point
        """
        # Import IntervalSet from below in this file

        if not self.overlaps(other):
            return self  # Return the original interval

        intersection = self.intersection(other)
        if (
            isinstance(intersection, IntervalSet) and intersection.is_empty()
        ):  # pragma: no cover
            return self  # No overlap, return original (defensive)

        # Handle the case where intersection is an interval
        if isinstance(intersection, Interval):
            int_start = intersection._start
            int_end = intersection._end
            int_open_start = intersection._open_start
            int_open_end = intersection._open_end
        else:  # pragma: no cover
            return self  # Shouldn't happen, but safety (defensive)

        result_intervals = []

        # Left part: [self.start, intersection.start)
        if self._start < int_start:
            result_intervals.append(
                Interval(
                    self._start,
                    int_start,
                    open_start=self._open_start,
                    open_end=not int_open_start,
                )
            )
        elif self._start == int_start and not self._open_start and int_open_start:
            # Case like [0, 2] - (0, 2): The point 0 is in the difference
            result_intervals.append(Point(self._start))

        # Right part: (intersection.end, self.end]
        if int_end < self._end:
            result_intervals.append(
                Interval(
                    int_end,
                    self._end,
                    open_start=not int_open_end,
                    open_end=self._open_end,
                )
            )
        elif int_end == self._end and int_open_end and not self._open_end:
            # Case like [0, 2] - (0, 2): The point 2 is in the difference
            result_intervals.append(Point(self._end))

        # Return appropriate type based on result
        if len(result_intervals) == 0:
            return _create_empty_set()  # Empty set
        elif len(result_intervals) == 1:
            return result_intervals[0]  # Single interval
        else:
            return _create_set(result_intervals)  # Multiple intervals

    # Comparison operators
    def __eq__(self, other) -> bool:
        """Check equality with another interval or set."""
        if hasattr(other, "is_interval") and other.is_interval():
            return other == self
        if not isinstance(other, Interval):
            return False
        return (
            self._start == other._start
            and self._end == other._end
            and self._open_start == other._open_start
            and self._open_end == other._open_end
        )

    def __hash__(self) -> int:
        """Hash function for use in sets and dicts."""
        return hash((self._start, self._end, self._open_start, self._open_end))

    def __lt__(self, other: "Interval") -> bool:
        """Check if this interval is completely to the left of another."""
        if not isinstance(other, Interval):
            return NotImplemented
        return self._end < other._start or (
            self._end == other._start and (self._open_end or other._open_start)
        )

    def __le__(self, other: "Interval") -> bool:
        """Check if this interval is to the left of or equal to another."""
        return self < other or self == other

    def __gt__(self, other: "Interval") -> bool:
        """Check if this interval is completely to the right of another."""
        if not isinstance(other, Interval):
            return NotImplemented
        return other < self

    def __ge__(self, other: "Interval") -> bool:
        """Check if this interval is to the right of or equal to another."""
        return self > other or self == other

    def __contains__(self, item) -> bool:
        """Support 'in' operator."""
        return self.contains(item)

    def interior(self) -> "Interval":
        """
        Return the interior of the interval.
        The interior of an interval is the set of its points except the boundary ones.
        Returns a new open interval.
        """
        if self.is_empty():
            return self
        return Interval(self.start, self.end, open_start=True, open_end=True)

    def closure(self) -> "Interval":
        """
        Return the closure of the interval.
        The closure of an interval is the smallest closed interval containing it.
        Returns a new closed interval.
        """
        if self.is_empty():
            return self
        return Interval(self.start, self.end, open_start=False, open_end=False)

    def boundary(self) -> "IntervalSet":
        """
        Return the topological boundary of the interval.
        For a non-empty bounded interval, the boundary is the set of its endpoints.
        """
        if self.is_empty():
            return _create_empty_set()

        # Collect finite endpoints
        points = []
        if not math.isinf(self.start):
            points.append(self.start)
        # Avoid duplicating point for degenerate intervals
        if not math.isinf(self.end) and self.end != self.start:
            points.append(self.end)

        return _create_set(points)

    def convex_hull(self) -> "Interval":
        """Return the smallest convex interval containing this interval."""
        return self

    def diameter(self) -> float:
        """Return the maximum distance between any two points in the interval."""
        if self.is_empty():
            return 0.0
        return self.end - self.start

    def __repr__(self) -> str:
        """String representation using mathematical notation."""
        if self.is_empty():
            return "∅"

        left = "(" if self._open_start else "["
        right = ")" if self._open_end else "]"
        return f"{left}{self._start}, {self._end}{right}"

    def __str__(self) -> str:
        """String representation."""
        return self.__repr__()

    # IntervalSet-like operators for intervals
    def minkowski_sum(self, other: Union["Interval", float]) -> "Interval":
        """
        Compute the Minkowski sum of this interval and another (dilation).
        A + B = {x + y : x in A, y in B}

        If other is a scalar, it performs a translation (shifting).
        """
        if self.is_empty():
            return self

        if isinstance(other, (int, float)):
            if math.isinf(other):
                # Shifting by infinity results in an empty set in our topology
                # because (inf, inf) and similar are normalized to empty.
                return Interval.empty()
            return Interval(
                self.start + other,
                self.end + other,
                open_start=self.open_start,
                open_end=self.open_end,
            )

        if not isinstance(other, Interval):
            raise TypeError(f"Minkowski sum requires Interval, got {type(other)}")

        if other.is_empty():
            return other

        return Interval(
            self.start + other.start,
            self.end + other.end,
            open_start=self.open_start or other.open_start,
            open_end=self.open_end or other.open_end,
        )

    def __add__(self, other: Union["Interval", float]) -> "Interval":
        """Minkowski sum operator +"""
        return self.minkowski_sum(other)

    def __radd__(self, other: float) -> "Interval":
        """Reverse add for scalar + Interval"""
        return self.minkowski_sum(other)

    def minkowski_difference(self, other: "Interval") -> "Interval":
        """
        Compute the Minkowski difference of this interval and another (erosion).
        A - B = {x : {x} + B is a subset of A}

        For intervals [a, b] and [c, d], this is [a-c, b-d] if boundaries allow.
        """
        if self.is_empty():
            return self

        if not isinstance(other, Interval):
            raise TypeError(
                f"Minkowski difference requires Interval, got {type(other)}"
            )

        if other.is_empty():
            # Any x + empty is empty, and empty is subset of any A.
            # So all x belong? No, Minkowski arithmetic with empty sets usually results in empty
            # unless we follow specific topological rules.
            # According to most definitions, A - empty is empty or universal?
            # Actually, erosion by empty set is usually the universal set?
            # Let's check literature. Usually it's defined as empty.
            return Interval.empty()

        start = self.start - other.start
        end = self.end - other.end

        if start > end:
            return Interval.empty()

        # Boundary logic:
        # Result is open ONLY IF A is open AND B is closed.
        open_start = self.open_start and not other.open_start
        open_end = self.open_end and not other.open_end

        # Check for degenerate points that might become empty due to boundary types
        if start == end and (open_start or open_end):
            return Interval.empty()

        return Interval(start, end, open_start=open_start, open_end=open_end)

    def dilate(self, other: Union["Interval", float]) -> "Interval":
        """Alias for minkowski_sum"""
        return self.minkowski_sum(other)

    def erode(self, other: "Interval") -> "Interval":
        """Alias for minkowski_difference"""
        return self.minkowski_difference(other)

    def __or__(self, other: "Interval") -> Union["Interval", "IntervalSet"]:
        """Union operator | for intervals"""
        return self.union(other)

    def __and__(self, other: "Interval") -> Union["Interval", "IntervalSet"]:
        """Intersection operator & for intervals"""
        return self.intersection(other)

    def __sub__(self, other: "Interval") -> Union["Interval", "IntervalSet"]:
        """Difference operator - for intervals"""
        return self.difference(other)

    def __xor__(self, other: "Interval") -> Union["Interval", "IntervalSet"]:
        """Symmetric difference operator ^ for intervals"""
        left_diff = self - other
        right_diff = other - self

        # Convert single intervals to sets for union
        # IntervalSet class is defined below in this same file
        if isinstance(left_diff, Interval):
            left_diff = _create_set([left_diff])
        if isinstance(right_diff, Interval):
            right_diff = _create_set([right_diff])

        return left_diff | right_diff


class Point(Interval):
    """
    Represents a single point on the real number line.

    A Point is a degenerate closed interval [value, value].
    It inherits from Interval and can be used in all set operations.
    """

    def __init__(self, value: float):
        """
        Create a new point.

        Args:
            value: The coordinate of the point.
        """
        # A point is a closed interval [value, value]
        super().__init__(value, value, open_start=False, open_end=False)

    @property
    def value(self) -> float:
        """The value of the point."""
        return self._start

    def __repr__(self) -> str:
        return f"Point({self._start})"


class IntervalSet:
    """
    Represents a set of disjoint intervals on the real number line.

    A IntervalSet can contain intervals, isolated points, or combinations of both.
    Internally, all elements are stored as non-overlapping intervals, with
    isolated points represented as degenerate intervals [p, p].

    Examples:
        >>> IntervalSet([Interval(0, 5), Interval(10, 15)])  # Two disjoint intervals
        >>> IntervalSet.point(7)                             # Single isolated point
        >>> IntervalSet.points([1, 3, 5])                    # Multiple isolated points
        >>> IntervalSet([Interval(0, 5), IntervalSet.point(7)])      # Mixed interval and point
        >>> IntervalSet()                                    # Empty set
    """

    def __init__(
        self, elements: Optional[Iterable[Union[Interval, float, "IntervalSet"]]] = None
    ):
        """
        Create a new set from a list of elements.

        Args:
            elements: List of Intervals, numeric values (points), or other Sets
        """
        self._intervals: List[Interval] = []

        if elements:
            for element in elements:
                self._add_element(element)

        # Sort and merge overlapping/adjacent intervals
        self._normalize()

    @property
    def isolated_points(self) -> List[Point]:
        """Get all isolated points in this set as Point objects."""
        return [
            i if isinstance(i, Point) else Point(i.start)
            for i in self._intervals
            if i.is_point()
        ]

    @property
    def continuous_intervals(self) -> List[Interval]:
        """Get all non-point intervals in this set."""
        result = []
        for i in self._intervals:
            if not i.is_point():
                result.append(i)
        return result

    @classmethod
    def point(cls, value: float) -> "IntervalSet":
        """
        Create a set containing a single isolated point.

        Args:
            value: The point value

        Returns:
            A IntervalSet containing just the point [value, value]
        """
        return cls([Interval.point(value)])

    @classmethod
    def points(cls, values: List[float]) -> "IntervalSet":
        """
        Create a set containing multiple isolated points.

        Args:
            values: List of point values

        Returns:
            A IntervalSet containing the points
        """
        return cls([Interval.point(v) for v in values])

    @classmethod
    def interval(
        cls,
        start: float,
        end: float,
        *,
        open_start: bool = False,
        open_end: bool = False,
    ) -> "IntervalSet":
        """
        Create a set containing a single interval.

        Args:
            start: Start of interval
            end: End of interval
            open_start: Whether start is open
            open_end: Whether end is open

        Returns:
            A IntervalSet containing the interval
        """
        return cls([Interval(start, end, open_start=open_start, open_end=open_end)])

    def _add_element(self, element: Union[Interval, float, "IntervalSet"]) -> None:
        """Add an element to this set (before normalization)."""
        if isinstance(element, (int, float)):
            self._intervals.append(Point(element))
        elif isinstance(element, Interval):
            if not element.is_empty():
                if element.is_point() and not isinstance(element, Point):
                    # Convert degenerate interval to Point
                    self._intervals.append(Point(element.start))
                else:
                    self._intervals.append(element)
        elif isinstance(element, IntervalSet):
            self._intervals.extend(element._intervals)
        else:
            raise TypeError(
                f"Cannot add element of type {type(element)} to IntervalSet"
            )

    def _normalize(self) -> None:
        """Sort intervals and merge overlapping/adjacent ones."""
        if not self._intervals:
            return

        # Sort by start point, then by end point
        self._intervals.sort(key=lambda i: (i.start, i.end, i.open_start, i.open_end))

        # Merge overlapping and adjacent intervals
        merged = []
        current = self._intervals[0]

        for next_interval in self._intervals[1:]:
            if current.overlaps(next_interval) or current.is_adjacent(next_interval):
                # Merge with current
                union_result = current.union(next_interval)
                if isinstance(union_result, Interval):
                    current = union_result
                else:  # pragma: no cover
                    # This shouldn't happen with overlapping/adjacent intervals (defensive)
                    merged.append(current)
                    current = next_interval
            else:
                # No overlap/adjacency, save current and move to next
                merged.append(current)
                current = next_interval

        merged.append(current)
        self._intervals = merged

    def is_empty(self) -> bool:
        """Check if this set is empty."""
        return len(self._intervals) == 0

    def is_point(self) -> bool:
        """Check if this set contains exactly one point."""
        return len(self._intervals) == 1 and self._intervals[0].is_point()

    def is_interval(self) -> bool:
        """Check if this set is exactly one interval."""
        return len(self._intervals) == 1

    def contains(self, value: Union[float, Interval, "IntervalSet"]) -> bool:
        """
        Check if this set contains a value, interval, or another set.

        Args:
            value: Value to check for containment

        Returns:
            True if the value is contained in this set
        """
        if isinstance(value, (int, float)):
            return any(interval.contains(value) for interval in self._intervals)
        elif isinstance(value, Interval):
            if value.is_empty():
                return True
            return any(interval.contains(value) for interval in self._intervals)
        elif isinstance(value, IntervalSet):
            if value.is_empty():
                return True
            return all(self.contains(interval) for interval in value._intervals)
        else:
            return False

    def overlaps(self, other: "IntervalSet") -> bool:
        """Check if this set overlaps with another set."""
        if self.is_empty() or other.is_empty():
            return False

        for our_interval in self._intervals:
            for their_interval in other._intervals:
                if our_interval.overlaps(their_interval):
                    return True
        return False

    def intersection(self, other: "IntervalSet") -> Union[Interval, "IntervalSet"]:
        """
        Compute the intersection of this set with another.

        Args:
            other: Another IntervalSet

        Returns:
            - An Interval if intersection is a single interval
            - A IntervalSet if intersection is empty or multiple intervals
        """
        if self.is_empty() or other.is_empty():
            return IntervalSet()

        result_intervals = []

        for our_interval in self._intervals:
            for their_interval in other._intervals:
                intersection = our_interval.intersection(their_interval)
                if isinstance(intersection, Interval):
                    result_intervals.append(intersection)
                elif (
                    isinstance(intersection, IntervalSet)
                    and not intersection.is_empty()
                ):  # pragma: no cover
                    result_intervals.extend(
                        intersection._intervals
                    )  # Unreachable: Interval.intersection never returns non-empty IntervalSet

        # Return appropriate type based on result
        filtered_intervals = [
            interval for interval in result_intervals if not interval.is_empty()
        ]
        if len(filtered_intervals) == 0:
            return IntervalSet()  # Empty set
        elif len(filtered_intervals) == 1:
            return filtered_intervals[0]  # Single interval
        else:
            return IntervalSet(filtered_intervals)  # Multiple intervals

    def union(self, other: "IntervalSet") -> Union[Interval, "IntervalSet"]:
        """
        Compute the union of this set with another.

        Args:
            other: Another IntervalSet

        Returns:
            - An Interval if union results in a single interval
            - A IntervalSet if union is empty or results in multiple intervals
        """
        if self.is_empty():
            if other.is_empty():
                return IntervalSet()
            elif len(other._intervals) == 1:
                return other._intervals[0]  # Single interval
            else:
                return IntervalSet(other._intervals)
        if other.is_empty():
            if len(self._intervals) == 1:
                return self._intervals[0]  # Single interval
            else:
                return IntervalSet(self._intervals)

        # Combine all intervals and let normalization handle merging
        all_intervals = self._intervals + other._intervals
        result = IntervalSet(all_intervals)

        # Return appropriate type
        if len(result._intervals) == 1:
            return result._intervals[0]  # Single interval
        else:
            return result  # Multiple intervals or empty

    def difference(self, other: "IntervalSet") -> Union[Interval, "IntervalSet"]:
        """
        Compute the difference of this set minus another.

        Args:
            other: IntervalSet to subtract

        Returns:
            - An Interval if the result is a single interval
            - A IntervalSet if the result is empty, multiple intervals, or contains points
        """
        if self.is_empty():
            return IntervalSet()
        if other.is_empty():
            if len(self._intervals) == 1:
                return self._intervals[0]  # Return single interval directly
            else:
                return IntervalSet(self._intervals)

        result_intervals = list(self._intervals)

        # Subtract each interval in other from our result
        for their_interval in other._intervals:
            new_result = []
            for our_interval in result_intervals:
                difference_result = our_interval.difference(their_interval)
                if isinstance(difference_result, Interval):
                    new_result.append(difference_result)
                else:
                    new_result.extend(difference_result._intervals)
            result_intervals = new_result

        # Return appropriate type based on result
        if len(result_intervals) == 0:
            return IntervalSet()  # Empty set
        elif len(result_intervals) == 1:
            return result_intervals[0]  # Single interval
        else:
            return IntervalSet(result_intervals)  # Multiple intervals

    def complement(
        self, universe: Optional["IntervalSet"] = None
    ) -> Union[Interval, "IntervalSet"]:
        """
        Compute the complement of this set.

        Args:
            universe: The universal set to complement against.
                     If None, uses (-∞, ∞) but this is not implemented yet.

        Returns:
            The complement set
        """
        # Use (-inf, inf) as default universe if not specified
        # Use (-inf, inf) as default universe if not specified
        if universe is None:
            raise NotImplementedError("Complement requires explicit universe set")

        return universe.difference(self)

    # IntervalSet operators
    def __or__(self, other: "IntervalSet") -> Union[Interval, "IntervalSet"]:
        """Union operator |"""
        return self.union(other)

    def __and__(self, other: "IntervalSet") -> Union[Interval, "IntervalSet"]:
        """Intersection operator &"""
        return self.intersection(other)

    def __sub__(self, other: "IntervalSet") -> Union[Interval, "IntervalSet"]:
        """Difference operator -"""
        return self.difference(other)

    def __xor__(self, other: "IntervalSet") -> Union[Interval, "IntervalSet"]:
        """Symmetric difference operator ^"""
        left_diff = self - other
        right_diff = other - self

        # Handle different return types from difference operations
        if isinstance(left_diff, Interval):
            left_diff = IntervalSet([left_diff])
        if isinstance(right_diff, Interval):
            right_diff = IntervalSet([right_diff])

        return left_diff | right_diff

    # In-place operators
    def __ior__(self, other: "IntervalSet") -> "IntervalSet":
        """In-place union |="""
        result = self.union(other)
        if isinstance(result, Interval):
            self._intervals = [result]
        else:
            self._intervals = result._intervals
        return self

    def __iand__(self, other: "IntervalSet") -> "IntervalSet":
        """In-place intersection &="""
        result = self.intersection(other)
        if isinstance(result, Interval):
            self._intervals = [result]
        else:
            self._intervals = result._intervals
        return self

    def __isub__(self, other: "IntervalSet") -> "IntervalSet":
        """In-place difference -="""
        result = self.difference(other)
        if isinstance(result, Interval):
            self._intervals = [result]
        else:
            self._intervals = result._intervals
        return self

    def __ixor__(self, other: "IntervalSet") -> "IntervalSet":
        """In-place symmetric difference ^="""
        result = self ^ other
        if isinstance(result, Interval):
            self._intervals = [result]
        else:
            self._intervals = result._intervals
        return self

    # Comparison operators
    def __eq__(self, other) -> bool:
        """Check equality with another set or interval."""
        if isinstance(other, Interval):
            return self.is_interval() and self._intervals[0] == other
        if not isinstance(other, IntervalSet):
            return False
        return self._intervals == other._intervals

    def __le__(self, other: "IntervalSet") -> bool:
        """Check if this set is a subset of another (⊆)."""
        return other.contains(self)

    def __lt__(self, other: "IntervalSet") -> bool:
        """Check if this set is a proper subset of another (⊂)."""
        return self <= other and self != other

    def __ge__(self, other: "IntervalSet") -> bool:
        """Check if this set is a superset of another (⊇)."""
        return self.contains(other)

    def __gt__(self, other: "IntervalSet") -> bool:
        """Check if this set is a proper superset of another (⊃)."""
        return self >= other and self != other

    def __contains__(self, item) -> bool:
        """Support 'in' operator."""
        return self.contains(item)

    def __len__(self) -> int:
        """Return the number of disjoint intervals in this set."""
        return len(self._intervals)

    def __iter__(self) -> Iterator[Interval]:
        """Iterate over the intervals in this set."""
        return iter(self._intervals)

    def __getitem__(self, index: int) -> Interval:
        """Get interval by index."""
        return self._intervals[index]

    def __bool__(self) -> bool:
        """Check if set is non-empty."""
        return not self.is_empty()

    def __hash__(self) -> int:
        """Hash function for use in sets and dicts."""
        return hash(tuple(self._intervals))

    def __repr__(self) -> str:
        """String representation."""
        if self.is_empty():
            return "∅"

        if len(self._intervals) == 1:
            return repr(self._intervals[0])

        interval_strs = [repr(interval) for interval in self._intervals]
        return "{" + ", ".join(interval_strs) + "}"

    def __str__(self) -> str:
        """String representation."""
        return self.__repr__()

    # Additional utility methods
    def intervals(self) -> List[Interval]:
        """Get a copy of the list of intervals in this set."""
        return list(self._intervals)

    def boundary_points(self) -> List[float]:
        """Get all boundary points of intervals in this set."""
        points = []
        for interval in self._intervals:
            points.append(interval.start)
            points.append(interval.end)
        return sorted(set(points))

    def measure(self) -> float:
        """
        Get the total measure (length) of this set.

        Returns:
            Sum of lengths of all intervals
        """
        return sum(interval.length() for interval in self._intervals)

    def volume(self) -> float:
        """
        Alias for measure() to maintain consistency with multi-dimensional Set.
        """
        return self.measure()

    def infimum(self) -> Optional[float]:
        """Get the infimum (greatest lower bound) of this set."""
        if self.is_empty():
            return None
        return min(interval.start for interval in self._intervals)

    def supremum(self) -> Optional[float]:
        """Get the supremum (least upper bound) of this set."""
        if self.is_empty():
            return None
        return max(interval.end for interval in self._intervals)

    def convex_hull(self) -> Interval:
        """Return the smallest convex interval containing this set."""
        if self.is_empty():
            return Interval.empty()
        # Since intervals are sorted and disjoint
        inf_int = self._intervals[0]
        sup_int = self._intervals[-1]
        return Interval(
            inf_int.start,
            sup_int.end,
            open_start=inf_int.open_start,
            open_end=sup_int.open_end,
        )

    def diameter(self) -> float:
        """Return the maximum distance between any two points in the set."""
        if self.is_empty():
            return 0.0
        # Since intervals are sorted, sup is in the last, inf is in the first
        return self._intervals[-1].end - self._intervals[0].start

    def is_bounded(self) -> bool:
        """Check if this set is bounded."""
        if self.is_empty():
            return True
        inf = self.infimum()
        sup = self.supremum()
        return (
            inf is not None
            and sup is not None
            and abs(inf) < float("inf")
            and abs(sup) < float("inf")
        )

    def is_connected(self) -> bool:
        """Check if this set is connected (single interval)."""
        return len(self._intervals) <= 1

    def connected_components(self) -> List["IntervalSet"]:
        """Get the connected components of this set."""
        return [IntervalSet([interval]) for interval in self._intervals]

    def is_open(self) -> bool:
        """Check if the set is open."""
        return not self.is_empty() and self == self.interior()

    def is_closed(self) -> bool:
        """Check if the set is closed."""
        return not self.is_empty() and self == self.closure()

    def is_compact(self) -> bool:
        """Check if the set is compact (closed and bounded)."""
        return self.is_closed() and self.is_bounded()

    def distance(self, other: "IntervalSet") -> float:
        """
        Compute the minimum distance between two sets (gap).
        """
        if self.is_empty() or other.is_empty():
            return float("inf")  # Standard convention? Or undefined?

        if self.overlaps(other):
            return 0.0

        # Brute force min distance between all pairs of intervals
        min_dist = float("inf")
        for i1 in self._intervals:
            for i2 in other._intervals:
                d = i1.distance(i2)
                if d < min_dist:
                    min_dist = d
        return min_dist

    def interior(self) -> "IntervalSet":
        """
        Return the interior of the set.
        The interior of a set is the union of the interiors of its component intervals.
        """
        if self.is_empty():
            return self
        # Create a new Set from the interiors of component intervals.
        # Normalization will merge them if necessary (though interiors of disjoint intervals should be disjoint).
        return IntervalSet([interval.interior() for interval in self._intervals])

    def closure(self) -> "IntervalSet":
        """
        Return the closure of the set.
        The closure of a set is the union of the closures of its component intervals.
        """
        if self.is_empty():
            return self
        return IntervalSet([interval.closure() for interval in self._intervals])

    def boundary(self) -> "IntervalSet":
        """
        Return the topological boundary of the set.
        Defined as: boundary(A) = closure(A) - interior(A)
        """
        if self.is_empty():
            return self

        # Use subtraction to find the boundary points
        # For [1, 2] | [3, 4], interior is (1, 2) | (3, 4)
        # Closure is [1, 2] | [3, 4]
        # Difference is {1, 2, 3, 4}
        diff = self.closure() - self.interior()
        if isinstance(diff, Interval):
            return IntervalSet([diff])
        return diff

    def minkowski_sum(
        self, other: Union["IntervalSet", Interval, float]
    ) -> "IntervalSet":
        """
        Compute the Minkowski sum of this set and another (dilation).
        A + B = {x + y : x in A, y in B}
        """
        if self.is_empty():
            return self

        if isinstance(other, (int, float)):
            # Shifting all intervals
            return IntervalSet(
                [interval.minkowski_sum(other) for interval in self._intervals]
            )

        if isinstance(other, Interval):
            if other.is_empty():
                return IntervalSet()
            return IntervalSet(
                [interval.minkowski_sum(other) for interval in self._intervals]
            )

        if not isinstance(other, IntervalSet):
            raise TypeError(
                f"Minkowski sum requires IntervalSet, Interval or scalar, got {type(other)}"
            )

        if other.is_empty():
            return other

        # Union of pairwise sums
        results = []
        for i_a in self._intervals:
            for i_b in other._intervals:
                results.append(i_a.minkowski_sum(i_b))
        return IntervalSet(results)

    def minkowski_difference(
        self, other: Union["IntervalSet", Interval]
    ) -> "IntervalSet":
        r"""
        Compute the Minkowski difference (erosion).
        A - B = {x : {x} + B is a subset of A}

        Formula: A - (B1 U B2) = (A - B1) \cap (A - B2)
        """
        if self.is_empty():
            return self

        if isinstance(other, Interval):
            if other.is_empty():
                return IntervalSet()
            # For connected B, A - B is union of components each eroded
            # Because x + B must be inside exactly one component
            results = []
            for i_a in self._intervals:
                res = i_a.minkowski_difference(other)
                if not res.is_empty():
                    results.append(res)
            return IntervalSet(results)

        if not isinstance(other, IntervalSet):
            raise TypeError(
                f"Minkowski difference requires IntervalSet or Interval, got {type(other)}"
            )

        if other.is_empty():
            return IntervalSet()

        # Intersection of erosion by each component of B
        # Intersection of erosion by each component of B
        current_res: Optional[Union["IntervalSet", Interval]] = None
        for i_b in other._intervals:
            res_b = self.minkowski_difference(i_b)
            # Intersection with current result
            if current_res is None:
                current_res = res_b
            else:
                # Note: IntervalSet & IntervalSet returns IntervalSet
                current_res = current_res & res_b  # type: ignore

            if (
                isinstance(current_res, (Interval, IntervalSet))
                and current_res.is_empty()
            ):
                break

        if current_res is None:
            return IntervalSet()

        if isinstance(current_res, Interval):
            return IntervalSet([current_res])
        return current_res

    def dilate(self, other: Union["IntervalSet", Interval, float]) -> "IntervalSet":
        """Alias for minkowski_sum"""
        return self.minkowski_sum(other)

    def erode(self, other: Union["IntervalSet", Interval]) -> "IntervalSet":
        """Alias for minkowski_difference"""
        return self.minkowski_difference(other)

    def __add__(self, other: Union["IntervalSet", Interval, float]) -> "IntervalSet":
        """Minkowski sum +"""
        return self.minkowski_sum(other)

    def __radd__(self, other: float) -> "IntervalSet":
        return self.minkowski_sum(other)

    def opening(self, other: Union["IntervalSet", Interval]) -> "IntervalSet":
        """
        Compute the morphological opening of this set by another.
        Opening(A, B) = dilation(erosion(A, B), B)
        """
        eroded = self.erode(other)
        return eroded.dilate(other)

    def closing(self, other: Union["IntervalSet", Interval]) -> "IntervalSet":
        """
        Compute the morphological closing of this set by another.
        Closing(A, B) = erosion(dilation(A, B), B)
        """
        dilated = self.dilate(other)
        return dilated.erode(other)

    def dilate_epsilon(self, epsilon: float) -> "IntervalSet":
        """
        Shortcut for dilation by a centered interval [-epsilon, epsilon].
        This expands the set in both directions.
        """
        if epsilon == 0:
            return self
        ebit = Interval.closed(-epsilon, epsilon)
        return self.dilate(ebit)

    def hausdorff_distance(self, other: "IntervalSet") -> float:
        """
        Compute the Hausdorff distance between two sets.
        d_H(A, B) = max( sup_{x in A} d(x, B), sup_{y in B} d(y, A) )
        """
        if self.is_empty() or other.is_empty():
            return float("inf")

        def directed_hausdorff(source: "IntervalSet", target: "IntervalSet") -> float:
            max_dist = 0.0
            for interval in source._intervals:
                # Check start endpoint
                if interval.start == float("-inf"):
                    # If target doesn't extend to -inf, distance is inf
                    if not any(i.start == float("-inf") for i in target._intervals):
                        return float("inf")
                    d_start = 0.0
                else:
                    d_start = target.distance_to_point(interval.start)

                # Check end endpoint
                if interval.end == float("inf"):
                    # If target doesn't extend to inf, distance is inf
                    if not any(i.end == float("inf") for i in target._intervals):
                        return float("inf")
                    d_end = 0.0
                else:
                    d_end = target.distance_to_point(interval.end)

                max_dist = max(max_dist, d_start, d_end)
            return max_dist

        return max(directed_hausdorff(self, other), directed_hausdorff(other, self))

    def distance_to_point(self, point: float) -> float:
        """Calculate minimum distance from a point to this set."""
        if self.is_empty():
            return float("inf")
        if self.contains(point):
            return 0.0

        min_dist = float("inf")
        for interval in self._intervals:
            # Distance to interval [s, e] is max(s - p, 0, p - e)
            # effectively: if p < s: s-p. if p > e: p-e. else 0.
            if point < interval.start:
                d = interval.start - point
            elif point > interval.end:
                d = point - interval.end
            else:
                d = 0.0

            if d < min_dist:
                min_dist = d
        return min_dist


# Helper functions to avoid circular imports
def _create_empty_set():
    """Create an empty IntervalSet."""
    return IntervalSet()


def _create_set(elements):
    """Create a IntervalSet with given elements."""
    return IntervalSet(elements)
