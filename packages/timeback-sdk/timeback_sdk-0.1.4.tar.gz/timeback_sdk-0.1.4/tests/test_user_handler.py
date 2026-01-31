"""Tests for user handler helper functions.

These tests verify that the SDK's user handler correctly handles:
- UTC day range calculation for XP queries
- Goals extraction from enrollment metadata
- XP aggregation from activity facts
- Course mapping from enrollments
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

# Import the helper functions from user handler
from timeback.server.handlers.user import (
    build_course_lookup,
    get_utc_day_range,
    map_enrollments_to_courses,
    pick_goals_from_enrollments,
    sum_xp,
)
from timeback_edubridge import (
    Enrollment,
    EnrollmentCourse,
    EnrollmentGoals,
    EnrollmentMetadata,
    EnrollmentSchool,
)

if TYPE_CHECKING:
    from timeback.server.timeback import CourseConfig


class TestUtcDayRange:
    """Tests for UTC day range calculation."""

    def test_day_range_start_is_midnight_utc(self) -> None:
        """Start of day should be 00:00:00 UTC."""
        date = datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC)
        start, _end = get_utc_day_range(date)

        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.microsecond == 0
        assert start.tzinfo == UTC

    def test_day_range_end_is_end_of_day_utc(self) -> None:
        """End of day should be 23:59:59.999999 UTC."""
        date = datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC)
        _start, end = get_utc_day_range(date)

        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59
        assert end.microsecond == 999999
        assert end.tzinfo == UTC

    def test_day_range_preserves_date(self) -> None:
        """Day range should preserve the year, month, day."""
        date = datetime(2024, 12, 25, 8, 0, 0, tzinfo=UTC)
        start, end = get_utc_day_range(date)

        assert start.year == 2024
        assert start.month == 12
        assert start.day == 25

        assert end.year == 2024
        assert end.month == 12
        assert end.day == 25

    def test_day_range_iso_format(self) -> None:
        """Day range should produce valid ISO format strings."""
        date = datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC)
        start, end = get_utc_day_range(date)

        # Should not raise - verifies both produce valid ISO strings
        start_iso = start.isoformat()
        end_iso = end.isoformat()

        # Python isoformat uses +00:00 for UTC, not Z
        assert "+00:00" in start_iso or "Z" in start_iso.upper()
        assert "+00:00" in end_iso or "Z" in end_iso.upper()


class TestGoalsExtraction:
    """Tests for extracting goals from enrollment metadata."""

    def _make_enrollment(self, goals: dict[str, Any] | None) -> Enrollment:
        """Create an enrollment with goals metadata."""
        metadata = None
        if goals is not None:
            metadata = EnrollmentMetadata(goals=EnrollmentGoals(**goals))

        return Enrollment(
            id="test-enrollment",
            role="student",
            metadata=metadata,
            course=EnrollmentCourse(id="test-course", title="Test Course", metadata={}),
            school=EnrollmentSchool(id="test-school", name="Test School"),
        )

    def test_picks_first_enrollment_with_goals(self) -> None:
        """Should return goals from first enrollment that has them."""
        goals = {"dailyXp": 100, "dailyLessons": 5}
        enrollments = [
            self._make_enrollment(None),  # No goals
            self._make_enrollment(goals),  # Has goals
        ]

        result = pick_goals_from_enrollments(enrollments)

        assert result is not None
        assert result.daily_xp == 100
        assert result.daily_lessons == 5

    def test_returns_none_when_no_enrollments_have_goals(self) -> None:
        """Should return None when no enrollment has goals."""
        enrollments = [
            self._make_enrollment(None),
            self._make_enrollment(None),
        ]

        result = pick_goals_from_enrollments(enrollments)

        assert result is None

    def test_returns_none_for_empty_enrollments(self) -> None:
        """Should return None for empty enrollments list."""
        result = pick_goals_from_enrollments([])

        assert result is None

    def test_extracts_all_goal_fields_camel_case(self) -> None:
        """Should extract all goal fields from camelCase keys."""
        goals = {
            "dailyXp": 100,
            "dailyLessons": 5,
            "dailyActiveMinutes": 30,
            "dailyAccuracy": 85,
            "dailyMasteredUnits": 2,
        }
        enrollments = [self._make_enrollment(goals)]

        result = pick_goals_from_enrollments(enrollments)

        assert result is not None
        assert result.daily_xp == 100
        assert result.daily_lessons == 5
        assert result.daily_active_minutes == 30
        assert result.daily_accuracy == 85
        assert result.daily_mastered_units == 2

    def test_extracts_all_goal_fields_snake_case(self) -> None:
        """Should extract all goal fields from snake_case keys."""
        goals = {
            "daily_xp": 200,
            "daily_lessons": 10,
            "daily_active_minutes": 60,
            "daily_accuracy": 90,
            "daily_mastered_units": 4,
        }
        enrollments = [self._make_enrollment(goals)]

        result = pick_goals_from_enrollments(enrollments)

        assert result is not None
        assert result.daily_xp == 200
        assert result.daily_lessons == 10
        assert result.daily_active_minutes == 60
        assert result.daily_accuracy == 90
        assert result.daily_mastered_units == 4

    def test_handles_partial_goals(self) -> None:
        """Should handle goals with only some fields set."""
        goals = {"dailyXp": 50}  # Only XP goal
        enrollments = [self._make_enrollment(goals)]

        result = pick_goals_from_enrollments(enrollments)

        assert result is not None
        assert result.daily_xp == 50
        assert result.daily_lessons is None
        assert result.daily_active_minutes is None


class TestXpAggregation:
    """Tests for XP aggregation from activity facts."""

    def test_sums_xp_across_dates(self) -> None:
        """Should sum XP across multiple dates."""
        facts = {
            "2024-06-14": {
                "Math": {"activityMetrics": {"xpEarned": 100}},
            },
            "2024-06-15": {
                "Math": {"activityMetrics": {"xpEarned": 150}},
            },
        }

        result = sum_xp(facts)

        assert result == 250

    def test_sums_xp_across_subjects(self) -> None:
        """Should sum XP across multiple subjects on same date."""
        facts = {
            "2024-06-15": {
                "Math": {"activityMetrics": {"xpEarned": 100}},
                "Reading": {"activityMetrics": {"xpEarned": 75}},
                "Science": {"activityMetrics": {"xpEarned": 50}},
            },
        }

        result = sum_xp(facts)

        assert result == 225

    def test_returns_zero_for_empty_facts(self) -> None:
        """Should return 0 for empty facts dict."""
        result = sum_xp({})

        assert result == 0

    def test_handles_missing_xp_earned(self) -> None:
        """Should handle missing xpEarned field gracefully."""
        facts = {
            "2024-06-15": {
                "Math": {"activityMetrics": {"totalQuestions": 10}},  # No xpEarned
            },
        }

        result = sum_xp(facts)

        assert result == 0

    def test_handles_missing_activity_metrics(self) -> None:
        """Should handle missing activityMetrics field gracefully."""
        facts = {
            "2024-06-15": {
                "Math": {"someOtherMetrics": {"value": 42}},
            },
        }

        result = sum_xp(facts)

        assert result == 0

    def test_handles_non_dict_subject_values(self) -> None:
        """Should handle non-dict values gracefully."""
        facts = {
            "2024-06-15": {
                "Math": "not a dict",  # Invalid
                "Reading": {"activityMetrics": {"xpEarned": 50}},  # Valid
            },
        }

        result = sum_xp(facts)

        assert result == 50

    def test_handles_non_dict_date_values(self) -> None:
        """Should handle non-dict date values gracefully."""
        facts = {
            "2024-06-14": "invalid",  # Not a dict
            "2024-06-15": {
                "Math": {"activityMetrics": {"xpEarned": 100}},
            },
        }

        result = sum_xp(facts)

        assert result == 100


class TestCourseLookup:
    """Tests for building course lookup from config."""

    def test_builds_lookup_by_environment_id(self) -> None:
        """Should build lookup keyed by environment-specific IDs."""
        courses = cast(
            "list[CourseConfig]",
            [
                {
                    "subject": "Math",
                    "grade": 5,
                    "ids": {"staging": "course-123", "production": "course-456"},
                },
                {"subject": "Reading", "grade": 5, "ids": {"staging": "course-789"}},
            ],
        )

        result = build_course_lookup(courses, "staging")

        assert "course-123" in result
        assert "course-789" in result
        assert result["course-123"].get("subject") == "Math"
        assert result["course-789"].get("subject") == "Reading"

    def test_uses_correct_environment(self) -> None:
        """Should only include IDs for the specified environment."""
        courses = cast(
            "list[CourseConfig]",
            [
                {
                    "subject": "Math",
                    "grade": 5,
                    "ids": {"staging": "staging-id", "production": "prod-id"},
                },
            ],
        )

        staging_result = build_course_lookup(courses, "staging")
        prod_result = build_course_lookup(courses, "production")

        assert "staging-id" in staging_result
        assert "prod-id" not in staging_result

        assert "prod-id" in prod_result
        assert "staging-id" not in prod_result

    def test_skips_courses_without_ids(self) -> None:
        """Should skip courses that don't have IDs for the environment."""
        courses = cast(
            "list[CourseConfig]",
            [
                {"subject": "Math", "grade": 5, "ids": {"production": "prod-only"}},
                {"subject": "Reading", "grade": 5},  # No ids at all
            ],
        )

        result = build_course_lookup(courses, "staging")

        assert len(result) == 0

    def test_handles_empty_courses(self) -> None:
        """Should return empty dict for empty courses list."""
        result = build_course_lookup([], "staging")

        assert result == {}

    def test_handles_none_ids(self) -> None:
        """Should handle courses with None ids gracefully."""
        courses = cast(
            "list[CourseConfig]",
            [
                {"subject": "Math", "grade": 5, "ids": None},
            ],
        )

        result = build_course_lookup(courses, "staging")

        assert len(result) == 0


class TestEnrollmentMapping:
    """Tests for mapping enrollments to course info."""

    def _make_enrollment(self, course_id: str, course_title: str) -> Enrollment:
        """Create an enrollment with course data."""
        return Enrollment(
            id="test-enrollment",
            role="student",
            metadata=None,
            course=EnrollmentCourse(id=course_id, title=course_title, metadata={}),
            school=EnrollmentSchool(id="test-school", name="Test School"),
        )

    def test_maps_enrollment_to_course_info(self) -> None:
        """Should map enrollment data to CourseInfo."""
        enrollments = [self._make_enrollment("course-123", "Math Grade 5")]
        course_lookup = cast("dict[str, CourseConfig]", {"course-123": {"course_code": "MATH5"}})

        result = map_enrollments_to_courses(enrollments, course_lookup)

        assert len(result) == 1
        assert result[0].id == "course-123"
        assert result[0].code == "MATH5"
        assert result[0].name == "Math Grade 5"

    def test_uses_course_id_as_fallback_code(self) -> None:
        """Should use course ID as code when not in lookup."""
        enrollments = [self._make_enrollment("course-xyz", "Unknown Course")]
        course_lookup = {}  # Not in lookup

        result = map_enrollments_to_courses(enrollments, course_lookup)

        assert result[0].code == "course-xyz"

    def test_handles_multiple_enrollments(self) -> None:
        """Should map multiple enrollments."""
        enrollments = [
            self._make_enrollment("course-1", "Math"),
            self._make_enrollment("course-2", "Reading"),
            self._make_enrollment("course-3", "Science"),
        ]
        course_lookup = cast(
            "dict[str, CourseConfig]",
            {
                "course-1": {"course_code": "MATH"},
                "course-2": {"course_code": "READ"},
            },
        )

        result = map_enrollments_to_courses(enrollments, course_lookup)

        assert len(result) == 3
        assert result[0].code == "MATH"
        assert result[1].code == "READ"
        assert result[2].code == "course-3"  # Fallback

    def test_handles_empty_enrollments(self) -> None:
        """Should return empty list for no enrollments."""
        result = map_enrollments_to_courses([], {})

        assert result == []
