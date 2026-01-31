"""
Activity Handler Schema

Validation logic for activity submissions.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

from starlette.responses import JSONResponse

from ....shared.types import (
    ActivityCourseRef,
    CourseCodeRef,
    SubjectGradeCourseRef,
    TimebackGrade,
    TimebackSubject,
)
from ...lib.logger import create_scoped_logger
from ...types import (
    ActivityUserInfo,
    ValidatedActivityPayload,
    ValidationError,
    ValidationSuccess,
)
from .resolve import ActivityCourseResolutionError, resolve_activity_course

if TYPE_CHECKING:
    from ...timeback import AppConfig

log = create_scoped_logger("handlers:activity:schema")

__all__ = [
    "ActivityUserInfo",
    "ValidatedActivityPayload",
    "format_course_selector",
    "validate_activity_request",
]


# ─────────────────────────────────────────────────────────────────────────────
# Validation Helpers
# ─────────────────────────────────────────────────────────────────────────────

# ISO 8601 datetime pattern (matches Z or timezone offset)
_ISO_DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _error(field: str, message: str) -> ValidationError:
    """Create a validation error result."""
    return ValidationError(
        ok=False,
        response=JSONResponse(
            {
                "success": False,
                "error": "Invalid payload",
                "details": {"field": field, "message": message},
            },
            status_code=400,
        ),
    )


def _server_error(message: str) -> ValidationError:
    """Create a 500 server error result."""
    return ValidationError(
        ok=False,
        response=JSONResponse({"success": False, "error": message}, status_code=500),
    )


def _require_str(body: dict[str, Any], field: str) -> str | ValidationError:
    """Require a non-empty string field."""
    value = body.get(field)
    if not value or not isinstance(value, str):
        return _error(field, "Required")
    return value


def _require_iso_datetime(body: dict[str, Any], field: str) -> str | ValidationError:
    """Require a valid ISO 8601 datetime field."""
    value = body.get(field)
    if value is None:
        return _error(field, "Required")
    if not isinstance(value, str) or not _ISO_DATETIME_PATTERN.match(value):
        return _error(field, "Invalid datetime")
    return value


def _require_nonnegative_int(body: dict[str, Any], field: str) -> int | ValidationError:
    """Require a nonnegative integer field."""
    if field not in body:
        return _error(field, "Required")
    value = body.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return _error(field, "Expected nonnegative integer")
    return value


def _optional_nonnegative_int(metrics: dict[str, Any], field: str) -> int | None | ValidationError:
    """Validate an optional nonnegative integer metric."""
    value = metrics.get(field)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return _error(f"metrics.{field}", "Expected nonnegative integer")
    return value


def _optional_nonnegative_number(
    metrics: dict[str, Any], field: str
) -> int | float | None | ValidationError:
    """Validate an optional nonnegative number (int or float)."""
    value = metrics.get(field)
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool) or value < 0:
        return _error(f"metrics.{field}", "Expected nonnegative number")
    return value


# ─────────────────────────────────────────────────────────────────────────────
# Course Selector Validation
# ─────────────────────────────────────────────────────────────────────────────


def _validate_course_selector(course_data: dict[str, Any]) -> ActivityCourseRef | ValidationError:
    """
    Validate and build a course selector from request data.

    Supports two selector modes:
    - Grade-based: { subject, grade } — K-12 style
    - Code-based: { code } — grade-less (e.g., CS platforms)
    """
    has_code = "code" in course_data and course_data.get("code")
    has_grade = "grade" in course_data and course_data.get("grade") is not None

    # Code-based selector: { code }
    if has_code:
        code = course_data.get("code")
        if not isinstance(code, str) or not code:
            return _error("course.code", "Expected non-empty string")
        return CourseCodeRef(code=code)

    # Grade-based selector: { subject, grade }
    if not course_data.get("subject") or not isinstance(course_data.get("subject"), str):
        return _error("course.subject", "Required")

    if not has_grade:
        return _error(
            "course", "Must have either 'code' (grade-less) or 'subject'+'grade' (grade-based)"
        )

    grade = course_data.get("grade")
    if not isinstance(grade, int) or isinstance(grade, bool):
        return _error("course.grade", "Expected integer")

    # Validate subject enum
    valid_subjects = {"Math", "Reading", "Science", "Social Studies", "Writing", "Other"}
    if course_data["subject"] not in valid_subjects:
        return _error(
            "course.subject",
            f"Invalid enum value. Expected {' | '.join(repr(s) for s in sorted(valid_subjects))}",
        )

    # Validate grade range (0-12)
    if not (0 <= grade <= 12):
        return _error("course.grade", "Number must be between 0 and 12")

    return SubjectGradeCourseRef(
        subject=cast("TimebackSubject", course_data["subject"]),
        grade=cast("TimebackGrade", grade),
    )


def format_course_selector(course_ref: ActivityCourseRef) -> str:
    """Format course selector for logging/error messages."""
    if isinstance(course_ref, SubjectGradeCourseRef):
        return f"{course_ref.subject} grade {course_ref.grade}"
    return f'code "{course_ref.code}"'


# ─────────────────────────────────────────────────────────────────────────────
# Metrics Validation
# ─────────────────────────────────────────────────────────────────────────────


def _validate_metrics(body: dict[str, Any]) -> dict[str, Any] | ValidationError:
    """Validate the metrics object."""
    if "metrics" not in body:
        return _error("metrics", "Required")

    metrics = body.get("metrics")
    if not isinstance(metrics, dict):
        return _error("metrics", "Expected object")

    # Validate integer metrics
    for field in ("totalQuestions", "correctQuestions", "masteredUnits"):
        result = _optional_nonnegative_int(metrics, field)
        if isinstance(result, ValidationError):
            return result

    # Validate xpEarned (allows float)
    xp_result = _optional_nonnegative_number(metrics, "xpEarned")
    if isinstance(xp_result, ValidationError):
        return xp_result

    # Paired validation: totalQuestions and correctQuestions
    total = metrics.get("totalQuestions")
    correct = metrics.get("correctQuestions")
    has_total = total is not None
    has_correct = correct is not None

    if has_total != has_correct:
        return _error("metrics", "totalQuestions and correctQuestions must be provided together.")

    if has_total and has_correct and correct > total:
        return _error("metrics.correctQuestions", "correctQuestions cannot exceed totalQuestions.")

    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# Request Validation
# ─────────────────────────────────────────────────────────────────────────────


def validate_activity_request(
    body: dict[str, Any],
    app_config: AppConfig,
) -> ValidationSuccess | ValidationError:
    """
    Validate the activity request body and resolve config dependencies.

    Returns a discriminated union:
    - ValidationSuccess(ok=True, payload, course, sensor) on success
    - ValidationError(ok=False, response) on failure

    Validates:
    - Required fields: id, name, course, startedAt, endedAt, elapsedMs, pausedMs, metrics
    - Course selector: either {subject, grade} or {code}
    - ISO 8601 datetime format for startedAt and endedAt
    - Nonnegative integers for elapsedMs and pausedMs
    - Metrics constraints (paired fields, correct <= total)
    """
    # ── Required string fields ──
    activity_id = _require_str(body, "id")
    if isinstance(activity_id, ValidationError):
        return activity_id

    name = _require_str(body, "name")
    if isinstance(name, ValidationError):
        return name

    # ── Course selector ──
    if not body.get("course"):
        return _error("course", "Required")

    course_data = body.get("course", {})
    if not isinstance(course_data, dict):
        return _error("course", "Expected object")

    course_ref = _validate_course_selector(course_data)
    if isinstance(course_ref, ValidationError):
        return course_ref

    # ── Datetime fields ──
    started_at = _require_iso_datetime(body, "startedAt")
    if isinstance(started_at, ValidationError):
        return started_at

    ended_at = _require_iso_datetime(body, "endedAt")
    if isinstance(ended_at, ValidationError):
        return ended_at

    # ── Time fields ──
    elapsed_ms = _require_nonnegative_int(body, "elapsedMs")
    if isinstance(elapsed_ms, ValidationError):
        return elapsed_ms

    paused_ms = _require_nonnegative_int(body, "pausedMs")
    if isinstance(paused_ms, ValidationError):
        return paused_ms

    # ── pctComplete (optional, clamp to 0-100) ──
    pct_complete = body.get("pctComplete")
    if pct_complete is not None:
        if not isinstance(pct_complete, int | float) or isinstance(pct_complete, bool):
            return _error("pctComplete", "Expected number")
        body["pctComplete"] = max(0, min(100, pct_complete))

    # ── Metrics ──
    metrics = _validate_metrics(body)
    if isinstance(metrics, ValidationError):
        return metrics

    # ── Resolve course config ──
    try:
        course_config = resolve_activity_course(
            cast("list[dict[str, Any]]", app_config.courses), course_ref
        )
    except ActivityCourseResolutionError as e:
        selector_desc = e.format_selector()
        if e.code == "unknown_course":
            log.warning("Unknown course selector: %s", selector_desc)
            return ValidationError(
                ok=False,
                response=JSONResponse(
                    {"success": False, "error": f"Unknown course: {selector_desc}"},
                    status_code=400,
                ),
            )
        log.error("Ambiguous course selector: %s", selector_desc)
        return _server_error("Ambiguous course selector in timeback.config.json")

    # ── Resolve sensor ──
    sensor = course_config.get("sensor") or app_config.sensor
    if not sensor:
        selector_desc = format_course_selector(course_ref)
        log.error("Missing sensor for course: %s", selector_desc)
        return _server_error(
            f"Course '{selector_desc}' has no sensor configured. "
            "Set a top-level 'sensor' or per-course 'sensor' in timeback.config.json."
        )

    # ── Build validated payload ──
    payload = ValidatedActivityPayload(
        id=activity_id,
        name=name,
        course=course_ref,
        started_at=started_at,
        ended_at=ended_at,
        elapsed_ms=elapsed_ms,
        paused_ms=paused_ms,
        metrics=metrics,
    )

    return ValidationSuccess(ok=True, payload=payload, course=course_config, sensor=sensor)
