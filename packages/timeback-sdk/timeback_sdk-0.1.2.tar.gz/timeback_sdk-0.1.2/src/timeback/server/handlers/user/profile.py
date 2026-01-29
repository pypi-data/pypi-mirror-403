"""
User Profile Building

Utilities for building enriched user profile data.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ....shared.types import TimebackProfile, XpInfo
from .enrollments import (
    build_course_lookup,
    get_utc_day_range,
    map_enrollments_to_courses,
    pick_goals_from_enrollments,
    sum_xp,
)

if TYPE_CHECKING:
    from timeback_core import TimebackClient

    from ....shared.types import TimebackAuthUser
    from ...timeback import AppConfig


async def build_user_profile(
    client: TimebackClient,
    user: TimebackAuthUser,
    app_config: AppConfig,
    api_env: str,
) -> TimebackProfile:
    """
    Build enriched user profile from Timeback data.

    Fetches enrollments and analytics to build a complete profile.

    Args:
        client: Timeback API client
        user: Resolved user info
        app_config: App configuration
        api_env: API environment

    Returns:
        Enriched user profile
    """
    enrollments = await client.edubridge.enrollments.list(user_id=user.id)

    course_by_id = build_course_lookup(app_config.courses, api_env)
    courses = map_enrollments_to_courses(enrollments, course_by_id)
    goals = pick_goals_from_enrollments(enrollments)

    today = datetime.now(UTC)
    today_start, today_end = get_utc_day_range(today)

    today_facts = await client.edubridge.analytics.get_activity(
        student_id=user.id,
        start_date=today_start.isoformat(),
        end_date=today_end.isoformat(),
    )
    all_facts = await client.edubridge.analytics.get_activity(
        student_id=user.id,
        start_date="2000-01-01",
        end_date=today_end.isoformat(),
    )

    return TimebackProfile(
        id=user.id,
        email=user.email,
        name=user.name,
        school=user.school,
        grade=user.grade,
        courses=courses if courses else None,
        goals=goals,
        xp=XpInfo(
            today=sum_xp(today_facts),
            all=sum_xp(all_facts),
        ),
    )


def profile_to_dict(profile: TimebackProfile) -> dict[str, Any]:
    """
    Convert TimebackProfile to a JSON-serializable dict.

    Args:
        profile: User profile

    Returns:
        JSON-serializable dictionary
    """
    result: dict[str, Any] = {
        "id": profile.id,
        "email": profile.email,
    }

    if profile.name:
        result["name"] = profile.name

    if profile.school:
        result["school"] = {
            "id": profile.school.id,
            "name": profile.school.name,
        }

    if profile.grade is not None:
        result["grade"] = profile.grade

    if profile.courses:
        result["courses"] = [{"id": c.id, "code": c.code, "name": c.name} for c in profile.courses]

    if profile.goals:
        goals_dict: dict[str, Any] = {}
        if profile.goals.daily_xp is not None:
            goals_dict["dailyXp"] = profile.goals.daily_xp
        if profile.goals.daily_lessons is not None:
            goals_dict["dailyLessons"] = profile.goals.daily_lessons
        if profile.goals.daily_active_minutes is not None:
            goals_dict["dailyActiveMinutes"] = profile.goals.daily_active_minutes
        if profile.goals.daily_accuracy is not None:
            goals_dict["dailyAccuracy"] = profile.goals.daily_accuracy
        if profile.goals.daily_mastered_units is not None:
            goals_dict["dailyMasteredUnits"] = profile.goals.daily_mastered_units
        if goals_dict:
            result["goals"] = goals_dict

    if profile.xp:
        result["xp"] = {
            "today": profile.xp.today,
            "all": profile.xp.all,
        }

    return result
