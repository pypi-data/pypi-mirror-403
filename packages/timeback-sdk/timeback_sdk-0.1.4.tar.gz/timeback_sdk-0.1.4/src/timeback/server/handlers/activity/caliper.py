"""
Caliper Event Building

Build and send Caliper events for activity submissions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlparse, urlunparse

from timeback_caliper import (
    ActivityCompletedInput,
    TimebackActivity,
    TimebackActivityContext,
    TimebackActivityMetric,
    TimebackApp,
    TimebackCourse,
    TimebackUser,
    TimeSpentInput,
    TimeSpentMetric,
    create_activity_event,
    create_time_spent_event,
)

from ....shared.types import (
    ActivityCourseRef,
    SubjectGradeCourseRef,
)

if TYPE_CHECKING:
    from timeback_caliper import ActivityCompletedEvent, TimeSpentEvent


# ─────────────────────────────────────────────────────────────────────────────
# Errors
# ─────────────────────────────────────────────────────────────────────────────


class MissingSyncedCourseIdError(Exception):
    """Error thrown when a course is missing a synced ID for the target environment."""

    def __init__(self, course_config: dict[str, Any], env: str) -> None:
        course_code = course_config.get("course_code")

        if course_code:
            identifier = course_code
        elif course_config.get("grade") is not None:
            identifier = f"{course_config.get('subject')} grade {course_config.get('grade')}"
        else:
            identifier = course_config.get("subject", "Unknown")

        super().__init__(
            f'Course "{identifier}" is missing a synced ID for {env}. Run `timeback sync` first.'
        )

        self.course = course_config
        self.env = env


class InvalidSensorUrlError(Exception):
    """Error thrown when the sensor URL is invalid."""

    def __init__(self, sensor: str) -> None:
        self.sensor = sensor
        super().__init__(
            f'Invalid sensor URL "{sensor}". Sensor must be a valid absolute URL '
            '(e.g., "https://sensor.example.com") to support slug-based activity IDs.'
        )


# ─────────────────────────────────────────────────────────────────────────────
# URL Builders
# ─────────────────────────────────────────────────────────────────────────────


def _join_url(base_url: str, path: str) -> str:
    """Join a base URL with a path, handling trailing/leading slashes."""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def build_oneroster_course_url(
    *, base_url: str, rostering_path: str, course_sourced_id: str
) -> str:
    """Build a OneRoster course URL from components."""
    return _join_url(base_url, f"{rostering_path}/courses/{course_sourced_id}")


def build_oneroster_user_url(*, base_url: str, rostering_path: str, user_sourced_id: str) -> str:
    """Build a OneRoster user URL from components."""
    return _join_url(base_url, f"{rostering_path}/users/{user_sourced_id}")


# ─────────────────────────────────────────────────────────────────────────────
# Course Building
# ─────────────────────────────────────────────────────────────────────────────


def build_course_id(course_config: dict[str, Any], api_env: str) -> str:
    """
    Build a course ID for Caliper context.

    Requires a synced course ID — throws MissingSyncedCourseIdError if missing.
    """
    ids = course_config.get("ids") or {}
    course_id = ids.get(api_env)

    if not course_id:
        raise MissingSyncedCourseIdError(course_config, api_env)

    return course_id


def build_course_name(course_config: dict[str, Any]) -> str:
    """Build a course name for Caliper context."""
    # Prefer course_code if available (normalized from JSON courseCode)
    course_code = course_config.get("course_code")
    if course_code:
        return course_code

    # Fallback: subject + grade (grade-based courses)
    if course_config.get("grade") is not None:
        return f"{course_config.get('subject')} G{course_config.get('grade')}"

    # Fallback: just subject (shouldn't happen with valid config)
    return course_config.get("subject", "Unknown")


# ─────────────────────────────────────────────────────────────────────────────
# Activity URL Building
# ─────────────────────────────────────────────────────────────────────────────


def build_canonical_activity_url(
    sensor: str,
    selector: ActivityCourseRef,
    slug: str,
) -> str:
    """
    Build a canonical activity URL from sensor, course selector, and activity slug.

    The resulting URL uniquely identifies the activity and allows upstream systems
    to process it as an "external URL" activity without requiring pre-synced
    OneRoster component resources.

    URL structure:
    - Grade-based: `{sensor}/activities/{subject}/g{grade}/{slug}`
    - Grade-less: `{sensor}/activities/{code}/{slug}`

    Examples:
        >>> build_canonical_activity_url(
        ...     'https://sensor.example.com',
        ...     SubjectGradeCourseRef(subject='Math', grade=3),
        ...     'fractions-with-like-denominators'
        ... )
        'https://sensor.example.com/activities/Math/g3/fractions-with-like-denominators'

        >>> build_canonical_activity_url(
        ...     'https://sensor.example.com',
        ...     CourseCodeRef(code='CS-101'),
        ...     'intro-to-loops'
        ... )
        'https://sensor.example.com/activities/CS-101/intro-to-loops'
    """
    parsed = urlparse(sensor)

    if not parsed.scheme or not parsed.netloc:
        raise InvalidSensorUrlError(sensor)

    # Determine the path segment for the activity URL based on the type of course selector:
    # - For grade-based courses (SubjectGradeCourseRef), construct the path as "{subject}/g{grade}"
    # - For grade-less courses (CourseCodeRef), use the course code directly as the path segment
    if isinstance(selector, SubjectGradeCourseRef):
        path_segment = f"{selector.subject}/g{selector.grade}"
    else:
        path_segment = selector.code

    base_path = parsed.path.rstrip("/")
    new_path = f"{base_path}/activities/{path_segment}/{quote(slug, safe='')}"

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            new_path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Context Building
# ─────────────────────────────────────────────────────────────────────────────


def build_activity_context(
    *,
    activity_id: str,
    activity_name: str,
    course_selector: ActivityCourseRef,
    course_config: dict[str, Any],
    app_name: str,
    api_env: str,
    sensor: str,
    oneroster_base_url: str,
    oneroster_rostering_path: str,
) -> TimebackActivityContext:
    """
    Build a Timeback activity context for Caliper events.

    Handles both grade-based and grade-less courses:
    - Grade-based: uses subject + grade for IDs
    - Grade-less: uses code for IDs

    The `id` field (`object.id` in Caliper) is a canonical URL derived from the
    sensor, course selector, and activity slug. This enables upstream systems to
    process the activity as an "external URL" activity without requiring
    pre-synced OneRoster component resources.

    The `activity` field contains only the human-readable `name` (no `id`),
    since the canonical URL in `object.id` serves as the stable identifier.
    """
    course_url = build_oneroster_course_url(
        base_url=oneroster_base_url,
        rostering_path=oneroster_rostering_path,
        course_sourced_id=build_course_id(course_config, api_env),
    )

    return TimebackActivityContext(
        id=build_canonical_activity_url(sensor, course_selector, activity_id),
        type="TimebackActivityContext",
        subject=course_config.get("subject", "Other"),
        app=TimebackApp(name=app_name),
        activity=TimebackActivity(name=activity_name),
        course=TimebackCourse(
            id=course_url,
            name=build_course_name(course_config),
        ),
        process=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Metrics Building
# ─────────────────────────────────────────────────────────────────────────────


def build_activity_metrics(metrics: dict[str, Any]) -> list[TimebackActivityMetric]:
    """Build Caliper activity metrics from the client payload."""
    result: list[TimebackActivityMetric] = []

    if metrics.get("totalQuestions") is not None:
        result.append(
            TimebackActivityMetric(type="totalQuestions", value=metrics["totalQuestions"])
        )

    if metrics.get("correctQuestions") is not None:
        result.append(
            TimebackActivityMetric(type="correctQuestions", value=metrics["correctQuestions"])
        )

    if metrics.get("xpEarned") is not None:
        result.append(TimebackActivityMetric(type="xpEarned", value=metrics["xpEarned"]))

    if metrics.get("masteredUnits") is not None:
        result.append(TimebackActivityMetric(type="masteredUnits", value=metrics["masteredUnits"]))

    return result


def build_time_spent_metrics(elapsed_ms: int, paused_ms: int) -> list[TimeSpentMetric]:
    """Build Caliper time spent metrics from elapsed and paused times."""
    result: list[TimeSpentMetric] = [
        TimeSpentMetric(type="active", value=max(0, elapsed_ms) / 1000)
    ]

    if paused_ms > 0:
        result.append(TimeSpentMetric(type="inactive", value=max(0, paused_ms) / 1000))

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Event Building
# ─────────────────────────────────────────────────────────────────────────────


def build_activity_events(
    *,
    actor: TimebackUser,
    activity_context: TimebackActivityContext,
    activity_metrics: list[TimebackActivityMetric],
    time_spent_metrics: list[TimeSpentMetric],
    event_time: str | None,
    attempt: int | None = None,
    generated_extensions: dict[str, object] | None = None,
    event_extensions: dict[str, object] | None = None,
) -> tuple[ActivityCompletedEvent, TimeSpentEvent]:
    """Build Caliper activity and time spent events."""

    activity_event = create_activity_event(
        input=ActivityCompletedInput(
            actor=actor,
            object=activity_context,
            metrics=activity_metrics,
            event_time=event_time,
            attempt=attempt,
            generated_extensions=generated_extensions,
            extensions=event_extensions,
        )
    )

    time_spent_event = create_time_spent_event(
        input=TimeSpentInput(
            actor=actor,
            object=activity_context,
            metrics=time_spent_metrics,
            event_time=event_time,
            extensions=event_extensions,
        )
    )

    return activity_event, time_spent_event
