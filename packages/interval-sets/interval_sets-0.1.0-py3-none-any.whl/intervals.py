"""Core classes for interval arithmetic and set operations."""

import math
from typing import Union, List, Optional, Iterator, Tuple, TYPE_CHECKING
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
        open_end: bool = False
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
        if math.isinf(start) or math.isinf(end):
            raise ValueError("Interval boundaries cannot be infinite")
            
        # Validate interval bounds
        if start > end:
            raise InvalidIntervalError(f"Invalid interval: start ({start}) must be <= end ({end})")
            
        # Validate open interval with same start/end (only (0,0) allowed for empty)
        if start == end and (open_start or open_end):
            if not (start == 0 and open_start and open_end):
                raise InvalidIntervalError("Cannot create open interval with start == end (except empty interval (0,0))")
        
        self._start = start
        self._end = end
        self._open_start = open_start
        self._open_end = open_end
    
    @classmethod
    def point(cls, value: float) -> 'Interval':
        """
        Create a degenerate interval representing a single point.
        
        Args:
            value: The point value
            
        Returns:
            An interval [value, value]
        """
        return Point(value)
    
    @classmethod
    def empty(cls) -> 'Interval':
        """
        Create an empty interval.
        
        Returns:
            The empty interval (0, 0)
        """
        return cls(0, 0, open_start=True, open_end=True)
    
    @classmethod
    def open(cls, start: float, end: float) -> 'Interval':
        """Create an open interval (start, end)."""
        return cls(start, end, open_start=True, open_end=True)
    
    @classmethod
    def closed(cls, start: float, end: float) -> 'Interval':
        """Create a closed interval [start, end]."""
        return cls(start, end, open_start=False, open_end=False)
    
    @classmethod
    def left_open(cls, start: float, end: float) -> 'Interval':
        """Create a left-open interval (start, end]."""
        return cls(start, end, open_start=True, open_end=False)
    
    @classmethod
    def right_open(cls, start: float, end: float) -> 'Interval':
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
        return (self._start == self._end == 0 and 
                self._open_start and self._open_end)
    
    def is_point(self) -> bool:
        """Check if this interval represents a single point."""
        return (self._start == self._end and 
                not self._open_start and not self._open_end and
                not self.is_empty())
    
    def length(self) -> float:
        """Get the length of the interval."""
        if self.is_empty():
            return 0.0
        return self._end - self._start
    
    def contains(self, value: Union[float, 'Interval']) -> bool:
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
    
    def _contains_interval(self, other: 'Interval') -> bool:
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
    
    def overlaps(self, other: 'Interval') -> bool:
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
    
    def is_adjacent(self, other: 'Interval') -> bool:
        """Check if intervals are adjacent (touching but not overlapping)."""
        return intervals_are_adjacent(self, other)
    
    def intersection(self, other: 'Interval') -> Union['Interval', 'Set']:
        """
        Compute the intersection of this interval with another.
        
        Returns:
            - An Interval if intersection is a single interval or point
            - A Set if intersection is empty
        """
        # Import Set from below in this file
        
        if not self.overlaps(other):
            return _create_empty_set()  # Empty set
        
        # Determine intersection bounds
        start = max(self._start, other._start)
        end = min(self._end, other._end)
        
        # Determine boundary conditions
        open_start = False
        open_end = False
        
        if start == self._start:
            open_start = self._open_start
        if start == other._start:
            open_start = open_start or other._open_start
            
        if end == self._end:
            open_end = self._open_end
        if end == other._end:
            open_end = open_end or other._open_end
        
        # If intersection is a single point, return appropriately
        if start == end:
            if not open_start and not open_end:
                return Point(start)  # Return point class instance
            return _create_empty_set()  # pragma: no cover
        
        return Interval(start, end, open_start=open_start, open_end=open_end)
    
    def union(self, other: 'Interval') -> Union['Interval', 'Set']:
        """
        Compute the union of this interval with another.
        
        Returns:  
            - An Interval if intervals are adjacent/overlapping (can be merged)
            - A Set containing both intervals if disjoint
        """
        # Import Set from below in this file
        
        if not (self.overlaps(other) or self.is_adjacent(other)):
            # Disjoint intervals - return Set containing both
            return _create_set([self, other])
        
        # Merge intervals
        start = min(self._start, other._start)
        end = max(self._end, other._end)
        
        # Use most inclusive boundaries
        open_start = False
        open_end = False
        
        if start == self._start:
            open_start = self._open_start
        if start == other._start:
            open_start = open_start and other._open_start
            
        if end == self._end:
            open_end = self._open_end
        if end == other._end:
            open_end = open_end and other._open_end
        
        return Interval(start, end, open_start=open_start, open_end=open_end)
    
    def difference(self, other: 'Interval') -> Union['Interval', 'Set']:
        """
        Compute the difference of this interval minus another.
        
        Returns:
            - An Interval if the result is a single interval
            - A Set if the result is empty, multiple intervals, or a single point
        """
        # Import Set from below in this file
        
        if not self.overlaps(other):
            return self  # Return the original interval
        
        intersection = self.intersection(other)
        if isinstance(intersection, Set) and intersection.is_empty():  # pragma: no cover
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
                Interval(self._start, int_start, 
                        open_start=self._open_start, 
                        open_end=not int_open_start)
            )
        elif self._start == int_start and self._open_start and not int_open_start:  # pragma: no cover
            # Edge case: self starts open, intersection starts closed (unreachable)
            pass  # No left part
        
        # Right part: (intersection.end, self.end]
        if int_end < self._end:
            result_intervals.append(
                Interval(int_end, self._end,
                        open_start=not int_open_end,
                        open_end=self._open_end)
            )
        elif int_end == self._end and not int_open_end and self._open_end:  # pragma: no cover
            # Edge case: intersection ends closed, self ends open (unreachable)
            pass  # No right part
        
        # Return appropriate type based on result
        if len(result_intervals) == 0:
            return _create_empty_set()  # Empty set
        elif len(result_intervals) == 1:
            return result_intervals[0]  # Single interval
        else:
            return _create_set(result_intervals)  # Multiple intervals
    
    # Comparison operators
    def __eq__(self, other) -> bool:
        """Check equality with another interval."""
        if not isinstance(other, Interval):
            return False
        return (self._start == other._start and 
                self._end == other._end and
                self._open_start == other._open_start and
                self._open_end == other._open_end)
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dicts."""
        return hash((self._start, self._end, self._open_start, self._open_end))
    
    def __lt__(self, other: 'Interval') -> bool:
        """Check if this interval is completely to the left of another."""
        if not isinstance(other, Interval):
            return NotImplemented
        return self._end < other._start or (
            self._end == other._start and (self._open_end or other._open_start)
        )
    
    def __le__(self, other: 'Interval') -> bool:
        """Check if this interval is to the left of or equal to another."""
        return self < other or self == other
    
    def __gt__(self, other: 'Interval') -> bool:
        """Check if this interval is completely to the right of another."""
        if not isinstance(other, Interval):
            return NotImplemented
        return other < self
    
    def __ge__(self, other: 'Interval') -> bool:
        """Check if this interval is to the right of or equal to another."""
        return self > other or self == other
    
    def __contains__(self, item) -> bool:
        """Support 'in' operator."""
        return self.contains(item)
    
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
    
    # Set-like operators for intervals
    def __or__(self, other: 'Interval') -> Union['Interval', 'Set']:
        """Union operator | for intervals"""
        return self.union(other)
    
    def __and__(self, other: 'Interval') -> Union['Interval', 'Set']:
        """Intersection operator & for intervals"""
        return self.intersection(other)
    
    def __sub__(self, other: 'Interval') -> Union['Interval', 'Set']:
        """Difference operator - for intervals"""
        return self.difference(other)
    
    def __xor__(self, other: 'Interval') -> Union['Interval', 'Set']:
        """Symmetric difference operator ^ for intervals"""
        left_diff = self - other
        right_diff = other - self
        
        # Convert single intervals to sets for union
        # Set class is defined below in this same file
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


class Set:
    """
    Represents any set on the real number line.
    
    A Set can contain intervals, isolated points, or combinations of both.
    Internally, all elements are stored as non-overlapping intervals, with 
    isolated points represented as degenerate intervals [p, p].
    
    Examples:
        >>> Set([Interval(0, 5), Interval(10, 15)])  # Two disjoint intervals
        >>> Set.point(7)                             # Single isolated point
        >>> Set.points([1, 3, 5])                    # Multiple isolated points  
        >>> Set([Interval(0, 5), Set.point(7)])      # Mixed interval and point
        >>> Set()                                    # Empty set
    """
    
    def __init__(self, elements: Optional[List[Union[Interval, float, 'Set']]] = None):
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
        return [i if isinstance(i, Point) else Point(i.start) 
                for i in self._intervals if i.is_point()]
                
    @property
    def continuous_intervals(self) -> List[Interval]:
        """Get all non-point intervals in this set."""
        result = []
        for i in self._intervals:
            if not i.is_point():
                result.append(i)
        return result
    
    @classmethod
    def point(cls, value: float) -> 'Set':
        """
        Create a set containing a single isolated point.
        
        Args:
            value: The point value
            
        Returns:
            A Set containing just the point [value, value]
        """
        return cls([Interval.point(value)])
    
    @classmethod
    def points(cls, values: List[float]) -> 'Set':
        """
        Create a set containing multiple isolated points.
        
        Args:
            values: List of point values
            
        Returns:
            A Set containing the points
        """
        return cls([Interval.point(v) for v in values])
    
    @classmethod
    def interval(cls, start: float, end: float, *, open_start: bool = False, open_end: bool = False) -> 'Set':
        """
        Create a set containing a single interval.
        
        Args:
            start: Start of interval
            end: End of interval  
            open_start: Whether start is open
            open_end: Whether end is open
            
        Returns:
            A Set containing the interval
        """
        return cls([Interval(start, end, open_start=open_start, open_end=open_end)])
    
    def _add_element(self, element: Union[Interval, float, 'Set']) -> None:
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
        elif isinstance(element, Set):
            self._intervals.extend(element._intervals)
        else:
            raise TypeError(f"Cannot add element of type {type(element)} to Set")
    
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
        return (len(self._intervals) == 1 and 
                self._intervals[0].is_point())
    
    def is_interval(self) -> bool:
        """Check if this set is exactly one interval."""
        return len(self._intervals) == 1
    
    def contains(self, value: Union[float, Interval, 'Set']) -> bool:
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
        elif isinstance(value, Set):
            if value.is_empty():
                return True
            return all(self.contains(interval) for interval in value._intervals)
        else:
            return False
    
    def overlaps(self, other: 'Set') -> bool:
        """Check if this set overlaps with another set."""
        if self.is_empty() or other.is_empty():
            return False
        
        for our_interval in self._intervals:
            for their_interval in other._intervals:
                if our_interval.overlaps(their_interval):
                    return True
        return False
    
    def intersection(self, other: 'Set') -> Union[Interval, 'Set']:
        """
        Compute the intersection of this set with another.
        
        Args:
            other: Another Set
            
        Returns:
            - An Interval if intersection is a single interval
            - A Set if intersection is empty or multiple intervals
        """
        if self.is_empty() or other.is_empty():
            return Set()
        
        result_intervals = []
        
        for our_interval in self._intervals:
            for their_interval in other._intervals:
                intersection = our_interval.intersection(their_interval)
                if isinstance(intersection, Interval):
                    result_intervals.append(intersection)
                elif isinstance(intersection, Set) and not intersection.is_empty():  # pragma: no cover
                    result_intervals.extend(intersection._intervals)  # Unreachable: Interval.intersection never returns non-empty Set
        
        # Return appropriate type based on result
        filtered_intervals = [interval for interval in result_intervals if not interval.is_empty()]
        if len(filtered_intervals) == 0:
            return Set()  # Empty set
        elif len(filtered_intervals) == 1:
            return filtered_intervals[0]  # Single interval
        else:
            return Set(filtered_intervals)  # Multiple intervals
    
    def union(self, other: 'Set') -> Union[Interval, 'Set']:
        """
        Compute the union of this set with another.
        
        Args:
            other: Another Set
            
        Returns:
            - An Interval if union results in a single interval
            - A Set if union is empty or results in multiple intervals
        """
        if self.is_empty():
            if other.is_empty():
                return Set()
            elif len(other._intervals) == 1:
                return other._intervals[0]  # Single interval
            else:
                return Set(other._intervals)
        if other.is_empty():
            if len(self._intervals) == 1:
                return self._intervals[0]  # Single interval
            else:
                return Set(self._intervals)
        
        # Combine all intervals and let normalization handle merging
        all_intervals = self._intervals + other._intervals
        result = Set(all_intervals)
        
        # Return appropriate type
        if len(result._intervals) == 1:
            return result._intervals[0]  # Single interval
        else:
            return result  # Multiple intervals or empty
    
    def difference(self, other: 'Set') -> Union[Interval, 'Set']:
        """
        Compute the difference of this set minus another.
        
        Args:
            other: Set to subtract
            
        Returns:
            - An Interval if the result is a single interval
            - A Set if the result is empty, multiple intervals, or contains points
        """
        if self.is_empty():
            return Set()
        if other.is_empty():
            if len(self._intervals) == 1:
                return self._intervals[0]  # Return single interval directly
            else:
                return Set(self._intervals)
        
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
            return Set()  # Empty set
        elif len(result_intervals) == 1:
            return result_intervals[0]  # Single interval
        else:
            return Set(result_intervals)  # Multiple intervals
    
    def complement(self, universe: Optional['Set'] = None) -> 'Set':
        """
        Compute the complement of this set.
        
        Args:
            universe: The universal set to complement against.
                     If None, uses (-∞, ∞) but this is not implemented yet.
                     
        Returns:
            The complement set
        """
        # For now, require explicit universe
        if universe is None:
            raise NotImplementedError("Complement requires explicit universe set")
        
        return universe.difference(self)
    
    # Set operators
    def __or__(self, other: 'Set') -> Union[Interval, 'Set']:
        """Union operator |"""
        return self.union(other)
    
    def __and__(self, other: 'Set') -> Union[Interval, 'Set']:
        """Intersection operator &"""
        return self.intersection(other)
    
    def __sub__(self, other: 'Set') -> Union[Interval, 'Set']:
        """Difference operator -"""
        return self.difference(other)
    
    def __xor__(self, other: 'Set') -> Union[Interval, 'Set']:
        """Symmetric difference operator ^"""
        left_diff = self - other
        right_diff = other - self
        
        # Handle different return types from difference operations
        if isinstance(left_diff, Interval):
            left_diff = Set([left_diff])
        if isinstance(right_diff, Interval):
            right_diff = Set([right_diff])
            
        return left_diff | right_diff
    
    # In-place operators
    def __ior__(self, other: 'Set') -> 'Set':
        """In-place union |="""
        result = self.union(other)
        if isinstance(result, Interval):
            self._intervals = [result]
        else:
            self._intervals = result._intervals
        return self
    
    def __iand__(self, other: 'Set') -> 'Set':
        """In-place intersection &="""
        result = self.intersection(other)
        if isinstance(result, Interval):
            self._intervals = [result]
        else:
            self._intervals = result._intervals
        return self
    
    def __isub__(self, other: 'Set') -> 'Set':
        """In-place difference -="""
        result = self.difference(other)
        if isinstance(result, Interval):
            self._intervals = [result]
        else:
            self._intervals = result._intervals
        return self
    
    def __ixor__(self, other: 'Set') -> 'Set':
        """In-place symmetric difference ^="""
        result = self ^ other
        if isinstance(result, Interval):
            self._intervals = [result]
        else:
            self._intervals = result._intervals
        return self
    
    # Comparison operators
    def __eq__(self, other) -> bool:
        """Check equality with another set."""
        if not isinstance(other, Set):
            return False
        return self._intervals == other._intervals
    
    def __le__(self, other: 'Set') -> bool:
        """Check if this set is a subset of another (⊆)."""
        return other.contains(self)
    
    def __lt__(self, other: 'Set') -> bool:
        """Check if this set is a proper subset of another (⊂)."""
        return self <= other and self != other
    
    def __ge__(self, other: 'Set') -> bool:
        """Check if this set is a superset of another (⊇)."""
        return self.contains(other)
    
    def __gt__(self, other: 'Set') -> bool:
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
    
    def is_bounded(self) -> bool:
        """Check if this set is bounded."""
        if self.is_empty():
            return True
        inf = self.infimum()
        sup = self.supremum()
        return inf is not None and sup is not None and abs(inf) < float('inf') and abs(sup) < float('inf')
    
    def is_connected(self) -> bool:
        """Check if this set is connected (single interval)."""
        return len(self._intervals) <= 1
    
    def connected_components(self) -> List['Set']:
        """Get the connected components of this set."""
        return [Set([interval]) for interval in self._intervals]

# Helper functions to avoid circular imports
def _create_empty_set():
    """Create an empty Set."""
    return Set()

def _create_set(elements):
    """Create a Set with given elements."""
    return Set(elements)



