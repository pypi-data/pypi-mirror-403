"""
Integration tests for complex workflows and real-world scenarios.
"""

from src.intervals import Interval, IntervalSet


class TestScheduleManagementWorkflow:
    """Test the schedule management use case"""

    def test_find_available_time_slots(self, work_day, meetings):
        """Test finding available time slots in a work day"""
        # Find available time
        available = meetings.complement(IntervalSet([work_day]))

        # Should have 3 free slots
        assert len(available) == 3

        # Verify the specific time slots
        intervals = list(available)
        assert intervals[0] == Interval.open(10, 11)  # (10, 11)
        assert intervals[1] == Interval.open(12.5, 14)  # (12.5, 14)
        assert intervals[2] == Interval.left_open(16, 17)  # (16, 17]

    def test_schedule_conflict_detection(self, meetings):
        """Test detecting scheduling conflicts"""
        # Try to schedule a meeting that conflicts
        new_meeting = Interval(9.5, 10.5)
        conflicts = meetings & IntervalSet([new_meeting])

        # Should find a conflict with the 9-10 AM meeting
        assert not conflicts.is_empty()

    def test_meeting_consolidation(self):
        """Test automatic consolidation of adjacent meetings"""
        meetings = IntervalSet(
            [
                Interval(9, 10),
                Interval(10, 11),
                Interval(11, 12),
            ]
        )

        # Should automatically merge into one continuous meeting
        assert len(meetings) == 1
        assert list(meetings)[0] == Interval(9, 12)


class TestDataCoverageAnalysis:
    """Test data coverage analysis workflow"""

    def test_complete_coverage_analysis(self, data_ranges):
        """Test analyzing data coverage and finding gaps"""
        # Define the expected data universe
        expected = Interval(0, 4000)

        # Find gaps in data coverage
        gaps = data_ranges.complement(IntervalSet([expected]))

        # Should have 2 gaps
        assert len(gaps) == 2
        gaps_list = list(gaps)
        assert gaps_list[0] == Interval.open(1000, 1500)  # (1000, 1500)
        assert gaps_list[1] == Interval.open(2500, 2800)  # (2500, 2800)


class TestMathematicalProperties:
    """Test mathematical properties and edge cases"""

    def test_set_operations_commutativity(self):
        """Test that set operations are commutative"""
        a = IntervalSet([Interval(0, 5), Interval(10, 15)])
        b = IntervalSet([Interval(3, 12), Interval(20, 25)])

        # Union is commutative
        assert a | b == b | a

        # Intersection is commutative
        assert a & b == b & a

    def test_empty_set_properties(self):
        """Test properties of empty sets"""
        empty = IntervalSet()
        a = IntervalSet([Interval(0, 10)])

        # Empty set is identity for union - result should be equivalent to a
        union_result = a | empty
        # Union with empty set should return the original interval
        assert union_result == Interval(0, 10)

        union_result2 = empty | a
        assert union_result2 == Interval(0, 10)

        # Empty set is annihilator for intersection
        intersection_result = a & empty
        assert intersection_result.is_empty()
        intersection_result2 = empty & a
        assert intersection_result2.is_empty()
