"""
Activity Progress Computation

Computes `pctComplete` by aggregating historical mastered units from EduBridge
enrollment analytics and combining with the current submission's mastered units.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from timeback_common import TimebackError
from timeback_edubridge import aggregate_activity_metrics

from ...lib.logger import create_scoped_logger
from ...lib.utils import map_env_for_api

if TYPE_CHECKING:
    from timeback_core import TimebackClient

    from ...types import Environment

log = create_scoped_logger("handlers:activity:progress")


def resolve_total_lessons(
    course_config: dict[str, Any],
    env: Environment,
) -> int | None:
    """
    Resolve the total lessons denominator from course config.

    Checks env-specific overrides first, then falls back to base metadata.
    """
    api_env = map_env_for_api(env)

    # Check env-specific overrides first
    overrides = course_config.get("overrides") or {}
    env_overrides = overrides.get(api_env) or {}
    env_metadata = env_overrides.get("metadata") or {}
    env_metrics = env_metadata.get("metrics") or {}

    total_lessons = env_metrics.get("totalLessons")
    if total_lessons is not None:
        return int(total_lessons) if isinstance(total_lessons, int | float) else None

    # Fall bakck to base metadata
    base_metadata = course_config.get("metadata") or {}
    base_metrics = base_metadata.get("metrics") or {}
    base_total_lessons = base_metrics.get("totalLessons")

    if base_total_lessons is not None:
        return int(base_total_lessons) if isinstance(base_total_lessons, int | float) else None

    return None


def _compute_percentage(total_mastered: int, total_lessons: int) -> int:
    """Compute progress percentage from mastered units (clamped 0-100)."""
    raw_pct = (total_mastered / total_lessons) * 100

    return min(100, max(0, round(raw_pct)))


async def compute_progress(
    *,
    client: TimebackClient,
    course_id: str,
    timeback_id: str,
    payload: dict[str, Any],
    course_config: dict[str, Any],
    env: Environment,
) -> int | None:
    """
    Compute pctComplete for an activity submission.

    Uses EduBridge enrollment analytics to aggregate historical mastered units,
    then combines with the current submission's mastered units.

    Only computes when:
    - `totalLessons` is configured (> 0) for the course
    - `metrics.masteredUnits` is present and > 0 in the payload
    - `pctComplete` is not already provided by the client
    """
    log.debug(
        "compute_progress called: course_id=%s, timeback_id=%s, env=%s",
        course_id,
        timeback_id,
        env,
    )

    if payload.get("pctComplete") is not None:
        log.debug("Skipping: pctComplete already provided in payload")
        return None

    metrics = payload.get("metrics") or {}
    current_mastered_units = metrics.get("masteredUnits")

    if not isinstance(current_mastered_units, int | float) or current_mastered_units <= 0:
        log.debug("Skipping: masteredUnits not present or <= 0, got: %s", current_mastered_units)
        return None

    current_mastered_units = int(current_mastered_units)
    log.debug("Current masteredUnits: %d", current_mastered_units)

    total_lessons = resolve_total_lessons(course_config, env)

    if not total_lessons or total_lessons <= 0:
        log.debug(
            "Skipping progress computation: totalLessons not configured, course_id=%s", course_id
        )
        return None

    log.debug("totalLessons resolved: %d", total_lessons)

    enrollment_id: str | None = None

    try:
        log.debug("Fetching enrollments for user: %s", timeback_id)
        enrollments = await client.edubridge.enrollments.list(user_id=timeback_id)
        log.debug("Found %d enrollments", len(enrollments))

        for enrollment in enrollments:
            log.debug(
                "Checking enrollment: id=%s, course.id=%s (looking for %s)",
                enrollment.id,
                enrollment.course.id,
                course_id,
            )
            if enrollment.course.id == course_id:
                enrollment_id = enrollment.id
                log.debug("Found matching enrollment: %s", enrollment_id)
                break
    except TimebackError as err:
        # Expected API failures (network, auth, not found, etc.) - log and continue
        log.warning(
            "Failed to fetch enrollments for progress computation: course_id=%s, timeback_id=%s, error=%s",
            course_id,
            timeback_id,
            err,
        )
        return None
    except Exception as err:
        # Unexpected errors (SDK bugs, parsing errors) - log and re-raise
        log.error(
            "Unexpected error fetching enrollments: course_id=%s, timeback_id=%s, error=%s",
            course_id,
            timeback_id,
            err,
            exc_info=True,
        )
        raise

    if not enrollment_id:
        log.warning(
            "Skipping progress computation: enrollment not found for student/course: course_id=%s, timeback_id=%s",
            course_id,
            timeback_id,
        )
        return None

    log.debug("Using enrollment_id: %s", enrollment_id)

    historical_mastered_units = 0

    try:
        facts = await client.edubridge.analytics.get_enrollment_facts(enrollment_id)
        aggregated = aggregate_activity_metrics(facts)
        historical_mastered_units = aggregated.mastered_units
    except TimebackError as err:
        # Expected API failures (network, auth, not found, etc.) - log and continue
        log.warning(
            "Failed to fetch enrollment facts for progress computation: course_id=%s, timeback_id=%s, enrollment_id=%s, error=%s",
            course_id,
            timeback_id,
            enrollment_id,
            err,
        )
        return None
    except Exception as err:
        # Unexpected errors (SDK bugs, parsing errors) - log and re-raise
        log.error(
            "Unexpected error fetching enrollment facts: course_id=%s, timeback_id=%s, enrollment_id=%s, error=%s",
            course_id,
            timeback_id,
            enrollment_id,
            err,
            exc_info=True,
        )
        raise

    # ─────────────────────────────────────────────────────────────────────────
    # Retry-safety / idempotency
    #
    # On a retry (e.g. first request succeeded but the response was lost),
    # EduBridge enrollment facts may already include this activity's metrics.
    # If we blindly add `current_mastered_units` again, we can inflate pctComplete
    # and prematurely trigger completion entry writes.
    #
    # We detect this by querying weekly facts for a record with matching activityId
    # and course/enrollment context. If we can't determine (e.g. weekly facts error),
    # we conservatively assume it's already processed to avoid premature 100%.
    # ─────────────────────────────────────────────────────────────────────────
    should_include_current_mastered_units = True
    activity_id = payload.get("id")
    ended_at = payload.get("endedAt")

    if activity_id and ended_at:
        try:
            weekly_facts = await client.edubridge.analytics.get_weekly_facts(
                student_id=timeback_id,
                week_date=ended_at,
            )

            already_processed = False
            for fact in weekly_facts:
                fact_activity_id = (
                    getattr(fact, "activity_id", None) or fact.get("activityId")
                    if isinstance(fact, dict)
                    else getattr(fact, "activity_id", None)
                )
                fact_enrollment_id = getattr(fact, "enrollment_id", None) or (
                    fact.get("enrollmentId") if isinstance(fact, dict) else None
                )
                fact_course_id = getattr(fact, "course_id", None) or (
                    fact.get("courseId") if isinstance(fact, dict) else None
                )

                if fact_activity_id != activity_id:
                    continue

                # Activity ID matches - check if it's for this enrollment/course
                if fact_enrollment_id and fact_enrollment_id == enrollment_id:
                    already_processed = True
                    break
                if fact_course_id and fact_course_id == course_id:
                    already_processed = True
                    break

            if already_processed:
                log.debug(
                    "Activity already processed, skipping current masteredUnits: activity_id=%s, enrollment_id=%s",
                    activity_id,
                    enrollment_id,
                )
                should_include_current_mastered_units = False
        except TimebackError as err:
            # On error, conservatively assume already processed to avoid premature 100%
            log.warning(
                "Failed to fetch weekly facts for retry-safe progress computation, assuming already processed: course_id=%s, activity_id=%s, error=%s",
                course_id,
                activity_id,
                err,
            )
            should_include_current_mastered_units = False
        except Exception as err:
            # Unexpected errors - log and conservatively assume processed
            log.warning(
                "Unexpected error fetching weekly facts, assuming already processed: course_id=%s, activity_id=%s, error=%s",
                course_id,
                activity_id,
                err,
            )
            should_include_current_mastered_units = False

    total_mastered = historical_mastered_units + (
        current_mastered_units if should_include_current_mastered_units else 0
    )

    pct_complete = _compute_percentage(total_mastered, total_lessons)

    log.debug(
        "Computed pctComplete: course_id=%s, timeback_id=%s, enrollment_id=%s, historical=%d, current=%d, should_include_current=%s, total=%d, totalLessons=%d, pct=%d",
        course_id,
        timeback_id,
        enrollment_id,
        historical_mastered_units,
        current_mastered_units,
        should_include_current_mastered_units,
        total_mastered,
        total_lessons,
        pct_complete,
    )

    return pct_complete
