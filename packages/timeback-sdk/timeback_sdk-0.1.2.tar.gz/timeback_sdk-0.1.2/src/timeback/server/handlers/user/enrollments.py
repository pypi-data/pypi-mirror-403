"""
User Enrollment Utilities

Helpers for processing enrollments and building profile data.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ....shared.types import CourseInfo, GoalsInfo

if TYPE_CHECKING:
    from timeback_edubridge import Enrollment

    from ...timeback import CourseConfig


def build_course_lookup(
    courses: list[CourseConfig],
    api_env: str,
) -> dict[str, CourseConfig]:
    """
    Build a lookup for configured courses keyed by their environment-specific IDs.

    Args:
        courses: App course config
        api_env: Target Timeback API environment

    Returns:
        Map of courseId → course config
    """
    course_by_id: dict[str, CourseConfig] = {}
    for course in courses:
        ids = course.get("ids") or {}
        course_id = ids.get(api_env)
        if course_id:
            course_by_id[course_id] = course
    return course_by_id


def get_course_code(course_config: CourseConfig | None) -> str | None:
    """
    Get course code from config, accepting both camelCase and snake_case keys.

    This ensures compatibility with both TS-style (courseCode) and Python-style
    (course_code) configuration files.

    Args:
        course_config: Course configuration or None

    Returns:
        Course code string or None
    """
    if course_config is None:
        return None
    return course_config.get("courseCode") or course_config.get("course_code")


def map_enrollments_to_courses(
    enrollments: list[Enrollment],
    course_by_id: dict[str, CourseConfig],
) -> list[CourseInfo]:
    """
    Map enrollments to the TimebackProfile course shape.

    Args:
        enrollments: Enrollment list
        course_by_id: Lookup for configured courses

    Returns:
        Normalized course list for profile
    """
    result: list[CourseInfo] = []
    for enrollment in enrollments:
        course = enrollment.course
        course_id = course.id
        course_title = course.title

        configured_course = course_by_id.get(course_id) if course_id else None
        code = get_course_code(configured_course) or course_id

        result.append(
            CourseInfo(
                id=course_id or "unknown",
                code=code or course_id or "unknown",
                name=course_title or "Unknown Course",
            )
        )
    return result


def pick_goals_from_enrollments(enrollments: list[Enrollment]) -> GoalsInfo | None:
    """
    Pick a goals object from enrollments, if present.

    Args:
        enrollments: Enrollment list

    Returns:
        Goals metadata or None
    """
    for enrollment in enrollments:
        if enrollment.metadata and enrollment.metadata.goals:
            goals = enrollment.metadata.goals
            return GoalsInfo(
                daily_xp=goals.daily_xp,
                daily_lessons=goals.daily_lessons,
                daily_active_minutes=goals.daily_active_minutes,
                daily_accuracy=goals.daily_accuracy,
                daily_mastered_units=goals.daily_mastered_units,
            )
    return None


def get_utc_day_range(date: datetime) -> tuple[datetime, datetime]:
    """
    Calculate UTC day range for a given date.

    Args:
        date: Date to anchor the range

    Returns:
        Tuple of (start, end) timestamps for the UTC day
    """
    start = datetime(date.year, date.month, date.day, tzinfo=UTC)
    end = datetime(date.year, date.month, date.day, 23, 59, 59, 999999, tzinfo=UTC)
    return start, end


def sum_xp(facts: dict[str, Any]) -> int:
    """
    Sum XP values from Edubridge activity facts.

    Args:
        facts: Activity facts by date and subject

    Returns:
        Total XP
    """
    total = 0
    for _date, subjects in facts.items():
        if not isinstance(subjects, dict):
            continue
        for _subject, metrics in subjects.items():
            if not isinstance(metrics, dict):
                continue
            activity_metrics = metrics.get("activityMetrics", {})
            total += activity_metrics.get("xpEarned", 0)
    return total
