"""
Edge case tests for achieving 100% code coverage.

This module contains tests for edge cases, boundary conditions, and less common
code paths that aren't covered by the main test suites. These tests ensure
comprehensive coverage of all reachable code in src/intervals.py.
"""

import pytest
from src.intervals import Interval, Set, _create_empty_set, _create_set
from src.errors import InvalidIntervalError


# ============================================================================
# Interval Edge Cases
# ============================================================================

class TestIntervalContainmentEdgeCases:
    """Edge cases for interval containment operations."""
    
    def test_contains_interval_open_end_boundary(self):
        """Test _contains_interval with open end boundary condition."""
        self_interval = Interval(0, 10, open_end=True)  # [0, 10)
        other_interval = Interval(5, 10)  # [5, 10]
        assert not self_interval.contains(other_interval)


class TestIntervalOverlapsEdgeCases:
    """Edge cases for interval overlap detection."""
    
    def test_overlaps_reverse_touch(self):
        """Test overlaps when other._end == self._start."""
        a = Interval(5, 10)
        b = Interval(0, 5)
        assert a.overlaps(b)
        
        # With open boundary, they shouldn't overlap
        a_open = Interval(5, 10, open_start=True)  # (5, 10]
        b_closed = Interval(0, 5)  # [0, 5]
        assert not a_open.overlaps(b_closed)


class TestIntervalComparisonOperators:
    """Edge cases for interval comparison operators."""
    
    def test_eq_with_non_interval(self):
        """Test equality with non-Interval type."""
        interval = Interval(0, 10)
        assert interval != "not an interval"
        assert interval != 5
        assert interval != None
    
    def test_lt_with_non_interval(self):
        """Test less than with non-Interval type."""
        interval = Interval(0, 10)
        result = interval.__lt__("not an interval")
        assert result == NotImplemented
    
    def test_gt_with_non_interval(self):
        """Test greater than with non-Interval type."""
        interval = Interval(0, 10)
        result = interval.__gt__("not an interval")
        assert result == NotImplemented
    
    def test_interval_gt_operator(self):
        """Test > operator."""
        a = Interval(10, 15)
        b = Interval(0, 5)
        assert a > b
        assert not (b > a)
    
    def test_interval_ge_operator(self):
        """Test >= operator."""
        a = Interval(10, 15)
        b = Interval(0, 5)
        c = Interval(10, 15)
        assert a >= b
        assert a >= c


class TestIntervalStringRepresentation:
    """Test interval string representation."""
    
    def test_str_method(self):
        """Test __str__ method."""
        interval = Interval(0, 10)
        assert str(interval) == "[0.0, 10.0]"
        
        empty = Interval.empty()
        assert str(empty) == "∅"


class TestIntervalSymmetricDifference:
    """Test interval symmetric difference operator."""
    
    def test_interval_xor_operator(self):
        """Test symmetric difference operator ^ for intervals."""
        a = Interval(0, 10)
        b = Interval(3, 7)
        result = a ^ b
        assert isinstance(result, (Interval, Set))


# ============================================================================
# Set Edge Cases
# ============================================================================

class TestSetAddElementEdgeCases:
    """Edge cases for Set._add_element."""
    
    def test_add_set_to_set(self):
        """Test adding a Set to another Set."""
        s1 = Set([Interval(0, 5)])
        s2 = Set([Interval(10, 15)])
        s3 = Set([s1, s2])
        assert len(s3) == 2
    
    def test_add_invalid_element_type(self):
        """Test adding invalid element type to Set."""
        with pytest.raises(TypeError, match="Cannot add element"):
            Set(["invalid"])
        
        with pytest.raises(TypeError, match="Cannot add element"):
            Set([None])


class TestSetPropertyMethods:
    """Test Set property methods."""
    
    def test_is_point(self):
        """Test Set.is_point() method."""
        s = Set.point(5)
        assert s.is_point()
        
        s2 = Set([Interval(0, 10)])
        assert not s2.is_point()
        
        s3 = Set([Interval.point(5), Interval.point(10)])
        assert not s3.is_point()
    
    def test_is_interval(self):
        """Test Set.is_interval() method."""
        s = Set([Interval(0, 10)])
        assert s.is_interval()
        
        s2 = Set([Interval(0, 5), Interval(10, 15)])
        assert not s2.is_interval()
        
        s3 = Set()
        assert not s3.is_interval()


class TestSetContainsEdgeCases:
    """Edge cases for Set.contains."""
    
    def test_contains_empty_interval(self):
        """Test Set contains empty interval."""
        s = Set([Interval(0, 10)])
        empty = Interval.empty()
        assert s.contains(empty)
    
    def test_contains_empty_set(self):
        """Test Set contains empty set."""
        s = Set([Interval(0, 10)])
        empty_set = Set()
        assert s.contains(empty_set)
    
    def test_contains_invalid_type(self):
        """Test Set contains with invalid type."""
        s = Set([Interval(0, 10)])
        assert not s.contains("invalid")
        assert not s.contains(None)
        assert not s.contains([5])


class TestSetOverlapsComplete:
    """Complete coverage for Set.overlaps."""
    
    def test_overlaps_multiple_intervals(self):
        """Test overlaps with multiple intervals in each set."""
        s1 = Set([Interval(0, 5), Interval(10, 15), Interval(20, 25)])
        s2 = Set([Interval(3, 7), Interval(12, 17), Interval(30, 35)])
        assert s1.overlaps(s2)
        
        s3 = Set([Interval(0, 5), Interval(10, 15)])
        s4 = Set([Interval(6, 8), Interval(16, 20)])
        assert not s3.overlaps(s4)


class TestSetOperationReturnTypes:
    """Test Set operation return type handling."""
    
    def test_union_empty_sets(self):
        """Test union when both sets are empty."""
        s1 = Set()
        s2 = Set()
        result = s1.union(s2)
        assert isinstance(result, Set)
        assert result.is_empty()
    
    def test_union_empty_with_multiple_intervals(self):
        """Test union of empty set with multi-interval set."""
        s1 = Set()
        s2 = Set([Interval(0, 5), Interval(10, 15)])
        result = s1.union(s2)
        assert isinstance(result, Set)
        assert len(result) == 2
    
    def test_difference_empty_sets(self):
        """Test difference with empty sets."""
        s1 = Set()
        s2 = Set([Interval(0, 10)])
        result = s1.difference(s2)
        assert isinstance(result, Set)
        assert result.is_empty()


class TestSetComplement:
    """Test Set.complement."""
    
    def test_complement_without_universe(self):
        """Test complement without explicit universe raises NotImplementedError."""
        s = Set([Interval(0, 10)])
        with pytest.raises(NotImplementedError, match="requires explicit universe"):
            s.complement()


class TestSetSymmetricDifference:
    """Test Set symmetric difference operator."""
    
    def test_set_xor_operator(self):
        """Test symmetric difference operator ^ for sets."""
        s1 = Set([Interval(0, 10)])
        s2 = Set([Interval(5, 15)])
        result = s1 ^ s2
        assert isinstance(result, (Interval, Set))


class TestSetInPlaceOperators:
    """Test Set in-place operators."""
    
    def test_ior_inplace_union(self):
        """Test |= in-place union operator."""
        s1 = Set([Interval(0, 5)])
        s2 = Set([Interval(10, 15)])
        s1 |= s2
        assert len(s1) == 2
        
        s3 = Set([Interval(0, 5)])
        s4 = Set([Interval(5, 10)])
        s3 |= s4
        assert len(s3) == 1
    
    def test_iand_inplace_intersection(self):
        """Test &= in-place intersection operator."""
        s1 = Set([Interval(0, 10)])
        s2 = Set([Interval(5, 15)])
        s1 &= s2
        assert isinstance(s1, Set)
    
    def test_isub_inplace_difference(self):
        """Test -= in-place difference operator."""
        s1 = Set([Interval(0, 10)])
        s2 = Set([Interval(5, 15)])
        s1 -= s2
        assert isinstance(s1, Set)
    
    def test_ixor_inplace_symmetric_difference(self):
        """Test ^= in-place symmetric difference operator."""
        # Test when result is an Interval
        s1 = Set([Interval(0, 10)])
        s2 = Set([Interval(0, 5)])
        s1 ^= s2
        assert isinstance(s1, Set)
        
        # Test when result is a Set
        s3 = Set([Interval(0, 10)])
        s4 = Set([Interval(5, 15)])
        s3 ^= s4
        assert isinstance(s3, Set)


class TestSetComparisonOperators:
    """Test Set comparison operators."""
    
    def test_eq_with_non_set(self):
        """Test equality with non-Set type."""
        s = Set([Interval(0, 10)])
        assert s != "not a set"
        assert s != 5
        assert s != None
    
    def test_le_subset_operator(self):
        """Test <= subset operator."""
        s1 = Set([Interval(0, 5)])
        s2 = Set([Interval(0, 10)])
        assert s1 <= s2
    
    def test_lt_proper_subset_operator(self):
        """Test < proper subset operator."""
        s1 = Set([Interval(0, 5)])
        s2 = Set([Interval(0, 10)])
        assert s1 < s2
        
        s3 = Set([Interval(0, 5)])
        assert not (s1 < s3)
    
    def test_ge_superset_operator(self):
        """Test >= superset operator."""
        s1 = Set([Interval(0, 10)])
        s2 = Set([Interval(0, 5)])
        assert s1 >= s2
    
    def test_gt_proper_superset_operator(self):
        """Test > proper superset operator."""
        s1 = Set([Interval(0, 10)])
        s2 = Set([Interval(0, 5)])
        assert s1 > s2
        
        s3 = Set([Interval(0, 10)])
        assert not (s1 > s3)


class TestSetUtilityMethods:
    """Test Set utility methods."""
    
    def test_str_method(self):
        """Test Set __str__ method."""
        s = Set([Interval(0, 10)])
        assert str(s) == "[0.0, 10.0]"
        
        s2 = Set([Interval(0, 5), Interval(10, 15)])
        str_repr = str(s2)
        assert "{" in str_repr
    
    def test_intervals_method(self):
        """Test Set.intervals() method."""
        s = Set([Interval(0, 5), Interval(10, 15)])
        intervals_copy = s.intervals()
        assert len(intervals_copy) == 2
        assert isinstance(intervals_copy, list)
        assert intervals_copy is not s._intervals
    
    def test_boundary_points_method(self):
        """Test Set.boundary_points() method."""
        s = Set([Interval(0, 5), Interval(10, 15), Interval(20, 25)])
        boundary_pts = s.boundary_points()
        assert boundary_pts == [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]


class TestSetInfimumSupremum:
    """Test Set infimum and supremum."""
    
    def test_infimum_empty_set(self):
        """Test infimum of empty set."""
        s = Set()
        assert s.infimum() is None
    
    def test_infimum_non_empty_set(self):
        """Test infimum of non-empty set."""
        s = Set([Interval(5, 10), Interval(0, 3)])
        assert s.infimum() == 0.0
    
    def test_supremum_empty_set(self):
        """Test supremum of empty set."""
        s = Set()
        assert s.supremum() is None
    
    def test_supremum_non_empty_set(self):
        """Test supremum of non-empty set."""
        s = Set([Interval(0, 5), Interval(10, 15)])
        assert s.supremum() == 15.0


class TestSetIsBounded:
    """Test Set.is_bounded() method."""
    
    def test_is_bounded_empty_set(self):
        """Test is_bounded for empty set."""
        s = Set()
        assert s.is_bounded()
    
    def test_is_bounded_non_empty_set(self):
        """Test is_bounded for non-empty set."""
        s = Set([Interval(0, 10), Interval(20, 30)])
        assert s.is_bounded()


class TestSetIsConnected:
    """Test Set.is_connected() method."""
    
    def test_is_connected(self):
        """Test Set.is_connected() method."""
        s1 = Set([Interval(0, 10)])
        assert s1.is_connected()
        
        s2 = Set([Interval(0, 5), Interval(10, 15)])
        assert not s2.is_connected()
        
        s3 = Set()
        assert s3.is_connected()


class TestSetConnectedComponents:
    """Test Set.connected_components() method."""
    
    def test_connected_components(self):
        """Test Set.connected_components() method."""
        s = Set([Interval(0, 5), Interval(10, 15), Interval(20, 25)])
        components = s.connected_components()
        assert len(components) == 3
        
        for component in components:
            assert isinstance(component, Set)
            assert component.is_connected()


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_create_empty_set(self):
        """Test _create_empty_set helper function."""
        empty = _create_empty_set()
        assert isinstance(empty, Set)
        assert empty.is_empty()
    
    def test_create_set(self):
        """Test _create_set helper function."""
        s = _create_set([Interval(0, 5), Interval(10, 15)])
        assert isinstance(s, Set)
        assert len(s) == 2


# ============================================================================
# Additional Tests for 100% Coverage
# ============================================================================

class TestIntervalIntersectionPoint:
    """Test intersection returning a single point (lines 263-264)."""
    
    def test_intersection_returns_point(self):
        """Test intersection that results in a single closed point."""
        # Two intervals that touch at exactly one point, both closed
        a = Interval(0, 5)  # [0, 5]
        b = Interval(5, 10)  # [5, 10]
        
        result = a.intersection(b)
        # Should return Interval.point(5) at line 264
        assert isinstance(result, Interval)
        assert result.is_point()
        assert result == Interval.point(5)


class TestIntervalXorBranches:
    """Test Interval XOR operator branches (lines 436, 438)."""
    
    def test_interval_xor_both_branches(self):
        """Test XOR when both differences return Intervals."""
        # Create intervals where both left_diff and right_diff are Intervals
        a = Interval(0, 10)
        b = Interval(3, 7)
        
        # left_diff = [0, 3) + (7, 10] (two intervals, so a Set)
        # right_diff = empty
        # But we need both to be Intervals to hit lines 436 and 438
        
        # Try different intervals
        a = Interval(0, 5)
        b = Interval(10, 15)
        
        # left_diff = [0, 5] (Interval)
        # right_diff = [10, 15] (Interval)
        result = a ^ b
        # Lines 436 and 438 should be hit
        assert isinstance(result, Set)


class TestSetDifferenceElseBranch:
    """Test Set difference else branch (line 691)."""
    
    def test_set_difference_multiple_intervals(self):
        """Test difference when self has multiple intervals and other is empty."""
        s1 = Set([Interval(0, 5), Interval(10, 15)])
        s2 = Set()  # Empty
        
        result = s1.difference(s2)
        # Line 691: else branch when multiple intervals
        assert isinstance(result, Set)
        assert len(result) == 2


class TestInPlaceOperatorElseBranches:
    """Test in-place operators else branches (lines 773, 782)."""
    
    def test_iand_else_branch(self):
        """Test &= when result is Set, not Interval (line 773)."""
        s1 = Set([Interval(0, 5), Interval(10, 15)])
        s2 = Set([Interval(2, 3), Interval(11, 12)])
        
        s1 &= s2
        # Line 773: else branch when result is Set
        assert isinstance(s1, Set)
    
    def test_isub_else_branch(self):
        """Test -= when result is Set, not Interval (line 782)."""
        s1 = Set([Interval(0, 10)])
        s2 = Set([Interval(3, 7)])
        
        s1 -= s2
        # Line 782: else branch when result is Set
        assert isinstance(s1, Set)
