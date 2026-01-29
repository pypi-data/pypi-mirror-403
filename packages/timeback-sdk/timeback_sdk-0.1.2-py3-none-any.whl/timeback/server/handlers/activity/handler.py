"""Activity submission handler."""

from __future__ import annotations

import inspect
import re
from typing import TYPE_CHECKING, Any, cast

from starlette.responses import JSONResponse, Response

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
from timeback_core import TimebackClient

from ....shared.types import (
    ActivityCourseRef,
    CourseCodeRef,
    SubjectGradeCourseRef,
    TimebackGrade,
    TimebackSubject,
)
from ...lib.logger import create_scoped_logger
from ...lib.resolve import (
    ActivityCourseResolutionError,
    TimebackUserResolutionError,
    lookup_timeback_id_by_email,
    resolve_activity_course,
    resolve_status_for_user_resolution_error,
)
from ...lib.utils import map_env_for_api
from ...types import ActivityBeforeSendData, CustomIdentityConfig
from .gradebook import write_gradebook_entry

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request

    from ...timeback import AppConfig
    from ...types import ApiCredentials, Environment, IdentityConfig, TimebackHooks

log = create_scoped_logger("handlers:activity")


# ─────────────────────────────────────────────────────────────────────────────
# Types
# ─────────────────────────────────────────────────────────────────────────────


class ActivityUserInfo:
    """User identity info needed for activity submission."""

    def __init__(self, email: str, timeback_id: str | None = None) -> None:
        self.email = email
        self.timeback_id = timeback_id


class ValidatedActivityPayload:
    """Validated activity payload ready for submission."""

    def __init__(
        self,
        *,
        id: str,
        name: str,
        course: ActivityCourseRef,
        started_at: str,
        ended_at: str,
        elapsed_ms: int,
        paused_ms: int,
        metrics: dict[str, Any],
    ) -> None:
        self.id = id
        self.name = name
        self.course = course
        self.started_at = started_at
        self.ended_at = ended_at
        self.elapsed_ms = elapsed_ms
        self.paused_ms = paused_ms
        self.metrics = metrics


# ─────────────────────────────────────────────────────────────────────────────
# Validation Helpers
# ─────────────────────────────────────────────────────────────────────────────

# ISO 8601 datetime pattern (matches Z or timezone offset)
_ISO_DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _is_valid_iso_datetime(value: Any) -> bool:
    """Check if a value is a valid ISO 8601 datetime string."""
    if not isinstance(value, str):
        return False
    return _ISO_DATETIME_PATTERN.match(value) is not None


def _is_nonnegative_int(value: Any) -> bool:
    """Check if a value is a nonnegative integer."""
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    return value >= 0


def _validation_error(field: str, message: str) -> Response:
    """Create a 400 validation error response.

    Returns a structured error with field and message for programmatic access:
    {
        "success": false,
        "error": "Invalid payload",
        "details": { "field": "<field>", "message": "<message>" }
    }

    Args:
        field: The field path that failed validation (e.g., "id", "course.subject")
        message: Human-readable error message
    """
    return JSONResponse(
        {
            "success": False,
            "error": "Invalid payload",
            "details": {"field": field, "message": message},
        },
        status_code=400,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────


def _validate_course_selector(
    course_data: dict[str, Any],
) -> tuple[ActivityCourseRef | None, Response | None]:
    """
    Validate and build a course selector from request data.

    Supports two selector modes:
    - Grade-based: { subject, grade } — K-12 style
    - Code-based: { code } — grade-less (e.g., CS platforms)

    Returns:
        Tuple of (course_ref, error_response).
    """
    has_code = "code" in course_data and course_data.get("code")
    has_grade = "grade" in course_data and course_data.get("grade") is not None

    if has_code:
        # Code-based selector: { code }
        code = course_data.get("code")
        if not isinstance(code, str) or not code:
            return None, _validation_error("course.code", "Expected non-empty string")
        return CourseCodeRef(code=code), None

    # Grade-based selector: { subject, grade }
    if not course_data.get("subject") or not isinstance(course_data.get("subject"), str):
        return None, _validation_error("course.subject", "Required")

    if not has_grade:
        return None, _validation_error(
            "course", "Must have either 'code' (grade-less) or 'subject'+'grade' (grade-based)"
        )

    grade = course_data.get("grade")
    if not isinstance(grade, int) or isinstance(grade, bool):
        return None, _validation_error("course.grade", "Expected integer")

    # Validate course.subject against valid subjects (matching TS @timeback/types)
    valid_subjects = {"Math", "Reading", "Science", "Social Studies", "Writing", "Other"}
    if course_data["subject"] not in valid_subjects:
        return None, _validation_error(
            "course.subject",
            f"Invalid enum value. Expected {' | '.join(repr(s) for s in sorted(valid_subjects))}",
        )

    # Validate course.grade is in valid range (0-12, matching TS @timeback/types)
    if not (0 <= grade <= 12):
        return None, _validation_error("course.grade", "Number must be between 0 and 12")

    return SubjectGradeCourseRef(
        subject=cast("TimebackSubject", course_data["subject"]),
        grade=cast("TimebackGrade", grade),
    ), None


def _format_course_selector(course_ref: ActivityCourseRef) -> str:
    """Format course selector for logging/error messages."""
    if isinstance(course_ref, SubjectGradeCourseRef):
        return f"{course_ref.subject} grade {course_ref.grade}"
    return f'code "{course_ref.code}"'


def _validate_activity_request(
    body: dict[str, Any],
    app_config: AppConfig,
) -> tuple[ValidatedActivityPayload | None, dict[str, Any] | None, str | None, Response | None]:
    """
    Validate the activity request body and resolve config dependencies.

    Validates:
    - Required fields: id, name, course
    - Course selector: either {subject, grade} or {code}
    - ISO 8601 datetime format for startedAt and endedAt
    - Nonnegative integers for elapsedMs and pausedMs
    - Nonnegative integers for metrics fields when present

    Returns:
        Tuple of (payload, course, sensor, error_response).
        If error_response is not None, return it immediately.
    """
    # Validate required string fields
    if not body.get("id") or not isinstance(body.get("id"), str):
        return (None, None, None, _validation_error("id", "Required"))

    if not body.get("name") or not isinstance(body.get("name"), str):
        return (None, None, None, _validation_error("name", "Required"))

    if not body.get("course"):
        return (None, None, None, _validation_error("course", "Required"))

    # Validate course object
    course_data = body.get("course", {})
    if not isinstance(course_data, dict):
        return (None, None, None, _validation_error("course", "Expected object"))

    # Validate and build course selector (supports grade-based and code-based)
    course_ref, course_error = _validate_course_selector(course_data)
    if course_error:
        return (None, None, None, course_error)
    if course_ref is None:
        return (None, None, None, _validation_error("course", "Invalid course selector"))

    # Validate ISO datetime fields (required to match TS SDK behavior)
    started_at = body.get("startedAt")
    if started_at is None:
        return (None, None, None, _validation_error("startedAt", "Required"))
    if not _is_valid_iso_datetime(started_at):
        return (None, None, None, _validation_error("startedAt", "Invalid datetime"))

    ended_at = body.get("endedAt")
    if ended_at is None:
        return (None, None, None, _validation_error("endedAt", "Required"))
    if not _is_valid_iso_datetime(ended_at):
        return (None, None, None, _validation_error("endedAt", "Invalid datetime"))

    # Validate nonnegative integer fields (required to match TS SDK behavior)
    if "elapsedMs" not in body:
        return (None, None, None, _validation_error("elapsedMs", "Required"))
    elapsed_ms = body.get("elapsedMs")
    if not _is_nonnegative_int(elapsed_ms):
        return (None, None, None, _validation_error("elapsedMs", "Expected nonnegative integer"))

    if "pausedMs" not in body:
        return (None, None, None, _validation_error("pausedMs", "Required"))
    paused_ms = body.get("pausedMs")
    if not _is_nonnegative_int(paused_ms):
        return (None, None, None, _validation_error("pausedMs", "Expected nonnegative integer"))

    # Validate metrics object (required to match TS SDK behavior)
    if "metrics" not in body:
        return (None, None, None, _validation_error("metrics", "Required"))
    metrics = body.get("metrics")
    if not isinstance(metrics, dict):
        return (None, None, None, _validation_error("metrics", "Expected object"))

    metric_fields = ["totalQuestions", "correctQuestions", "xpEarned", "masteredUnits"]
    for field_name in metric_fields:
        value = metrics.get(field_name)
        if value is not None and not _is_nonnegative_int(value):
            return (
                None,
                None,
                None,
                _validation_error(f"metrics.{field_name}", "Expected nonnegative integer"),
            )

    # Resolve course against config
    try:
        course_config = resolve_activity_course(
            cast("list[dict[str, Any]]", app_config.courses), course_ref
        )
    except ActivityCourseResolutionError as e:
        selector_desc = e.format_selector()
        if e.code == "unknown_course":
            log.warning("Unknown course selector: %s", selector_desc)
            return (
                None,
                None,
                None,
                JSONResponse(
                    {"success": False, "error": f"Unknown course: {selector_desc}"},
                    status_code=400,
                ),
            )
        log.error("Ambiguous course selector: %s", selector_desc)
        return (
            None,
            None,
            None,
            JSONResponse(
                {"success": False, "error": "Ambiguous course selector in timeback.config.json"},
                status_code=500,
            ),
        )

    # Resolve effective sensor: course.sensor overrides app_config.sensor
    sensor = course_config.get("sensor") or app_config.sensor
    if not sensor:
        # This should be prevented by config validation, but check anyway
        selector_desc = _format_course_selector(course_ref)
        log.error("Missing sensor for course: %s", selector_desc)
        return (
            None,
            None,
            None,
            JSONResponse(
                {
                    "success": False,
                    "error": f"Course '{selector_desc}' has no sensor configured. "
                    "Set a top-level 'sensor' or per-course 'sensor' in timeback.config.json.",
                },
                status_code=500,
            ),
        )

    # Build validated payload (all fields are now required after validation)
    # elapsed_ms and paused_ms are validated as nonnegative integers above
    assert isinstance(elapsed_ms, int), "elapsed_ms must be int after validation"
    assert isinstance(paused_ms, int), "paused_ms must be int after validation"

    payload = ValidatedActivityPayload(
        id=body["id"],
        name=body["name"],
        course=course_ref,
        started_at=started_at,
        ended_at=ended_at,
        elapsed_ms=elapsed_ms,
        paused_ms=paused_ms,
        metrics=metrics,
    )

    return payload, course_config, sensor, None


# ─────────────────────────────────────────────────────────────────────────────
# Event Building
# ─────────────────────────────────────────────────────────────────────────────


class MissingSyncedCourseIdError(Exception):
    """Error thrown when a course is missing a synced ID for the target environment."""

    def __init__(self, course_config: dict[str, Any], env: str) -> None:
        # Build course identifier for error message
        course_code = course_config.get("course_code") or course_config.get("courseCode")
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


def _get_course_code(course_config: dict[str, Any]) -> str | None:
    """Get course code from config, accepting both camelCase and snake_case keys.

    This ensures compatibility with both TS-style (courseCode) and Python-style
    (course_code) configuration files.
    """
    return course_config.get("courseCode") or course_config.get("course_code")


def _build_course_id(course_config: dict[str, Any], api_env: str) -> str:
    """
    Build a course ID for Caliper context.

    Requires a synced course ID — throws if missing.

    Args:
        course_config: Course config entry
        api_env: Target environment ('staging' or 'production')

    Returns:
        Course ID string

    Raises:
        MissingSyncedCourseIdError: If course is not synced for the environment
    """
    ids = course_config.get("ids") or {}
    course_id = ids.get(api_env)

    if not course_id:
        raise MissingSyncedCourseIdError(course_config, api_env)

    return course_id


def _build_course_name(course_config: dict[str, Any]) -> str:
    """
    Build a course name for Caliper context.

    Args:
        course_config: Course config entry

    Returns:
        Course name string
    """
    # Prefer course_code if available
    course_code = _get_course_code(course_config)
    if course_code:
        return course_code

    # Fallback: subject + grade (grade-based courses)
    if course_config.get("grade") is not None:
        return f"{course_config.get('subject')} G{course_config.get('grade')}"

    # Fallback: just subject (shouldn't happen with valid config)
    return course_config.get("subject", "Unknown")


class InvalidSensorUrlError(Exception):
    """Error thrown when the sensor URL is invalid."""

    def __init__(self, sensor: str) -> None:
        self.sensor = sensor
        super().__init__(
            f'Invalid sensor URL "{sensor}". Sensor must be a valid absolute URL '
            '(e.g., "https://sensor.example.com") to support slug-based activity IDs.'
        )


def _build_canonical_activity_url(
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

    Args:
        sensor: Sensor URL (must be a valid absolute URL)
        selector: Course selector from activity payload
        slug: Activity slug (will be URI-encoded)

    Returns:
        Canonical activity URL

    Raises:
        InvalidSensorUrlError: If sensor is not a valid absolute URL

    Examples:
        Grade-based:
        >>> _build_canonical_activity_url(
        ...     'https://sensor.example.com',
        ...     SubjectGradeCourseRef(subject='Math', grade=3),
        ...     'fractions-with-like-denominators'
        ... )
        'https://sensor.example.com/activities/Math/g3/fractions-with-like-denominators'

        Grade-less:
        >>> _build_canonical_activity_url(
        ...     'https://sensor.example.com',
        ...     CourseCodeRef(code='CS-101'),
        ...     'intro-to-loops'
        ... )
        'https://sensor.example.com/activities/CS-101/intro-to-loops'
    """
    from urllib.parse import quote, urlparse, urlunparse

    parsed = urlparse(sensor)

    # Validate it's an absolute URL with scheme and netloc
    if not parsed.scheme or not parsed.netloc:
        raise InvalidSensorUrlError(sensor)

    # Build path segment based on course selector type
    if isinstance(selector, SubjectGradeCourseRef):
        path_segment = f"{selector.subject}/g{selector.grade}"
    else:
        path_segment = selector.code

    # Strip trailing slashes from base path
    base_path = parsed.path.rstrip("/")

    # Construct full path: {basePath}/activities/{pathSegment}/{encodedSlug}
    new_path = f"{base_path}/activities/{path_segment}/{quote(slug, safe='')}"

    # Reconstruct URL
    return urlunparse((parsed.scheme, parsed.netloc, new_path, "", "", ""))


def _build_activity_context(
    payload: ValidatedActivityPayload,
    course_config: dict[str, Any],
    app_name: str,
    api_env: str,
    sensor: str,
) -> TimebackActivityContext:
    """Build a Timeback activity context for Caliper events.

    Handles both grade-based and grade-less courses:
    - Grade-based: uses subject + grade for IDs
    - Grade-less: uses code for IDs

    The `id` field (`object.id` in Caliper) is a canonical URL derived from the
    sensor, course selector, and activity slug. This enables upstream systems to
    process the activity as an "external URL" activity without requiring
    pre-synced OneRoster component resources.

    The `activity` field contains only the human-readable `name` (no `id`),
    since the canonical URL in `object.id` serves as the stable identifier.

    Args:
        payload: Validated activity payload
        course_config: Matched course config
        app_name: Timeback app display name
        api_env: Target Timeback API environment
        sensor: Sensor URL for building the canonical activity URL

    Returns:
        Caliper activity context payload

    Raises:
        MissingSyncedCourseIdError: If course is not synced for the environment
        InvalidSensorUrlError: If sensor is not a valid absolute URL
    """
    # Get subject from course config (handles both selector types)
    subject = course_config.get("subject", "Other")

    return TimebackActivityContext(
        id=_build_canonical_activity_url(sensor, payload.course, payload.id),
        type="TimebackActivityContext",
        subject=subject,
        app=TimebackApp(name=app_name),
        activity=TimebackActivity(name=payload.name),
        course=TimebackCourse(
            id=_build_course_id(course_config, api_env),
            name=_build_course_name(course_config),
        ),
        # The `process` flag is set to `False` here to ensure that gradebook handling
        # is performed in a controlled manner exclusively through the OneRoster integration.
        # This means that Caliper event processing does not automatically trigger any
        # gradebook updates or modifications.
        process=False,
    )


def _build_activity_metrics(metrics: dict[str, Any]) -> list[TimebackActivityMetric]:
    """Build Caliper activity metrics from the client payload."""
    result: list[TimebackActivityMetric] = []

    total_questions = metrics.get("totalQuestions") or metrics.get("total_questions")
    if total_questions is not None:
        result.append(TimebackActivityMetric(type="totalQuestions", value=total_questions))

    correct_questions = metrics.get("correctQuestions") or metrics.get("correct_questions")
    if correct_questions is not None:
        result.append(TimebackActivityMetric(type="correctQuestions", value=correct_questions))

    xp_earned = metrics.get("xpEarned") or metrics.get("xp_earned")
    if xp_earned is not None:
        result.append(TimebackActivityMetric(type="xpEarned", value=xp_earned))

    mastered_units = metrics.get("masteredUnits") or metrics.get("mastered_units")
    if mastered_units is not None:
        result.append(TimebackActivityMetric(type="masteredUnits", value=mastered_units))

    return result


def _build_time_spent_metrics(elapsed_ms: int, paused_ms: int) -> list[TimeSpentMetric]:
    """Build Caliper time spent metrics from elapsed and paused times."""
    result: list[TimeSpentMetric] = [
        TimeSpentMetric(type="active", value=max(0, elapsed_ms) // 1000)
    ]

    if paused_ms > 0:
        result.append(TimeSpentMetric(type="inactive", value=max(0, paused_ms) // 1000))

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Preview Response Helper
# ─────────────────────────────────────────────────────────────────────────────


def _build_preview_response(data: ActivityBeforeSendData) -> Response:
    """Build a preview response with the built events (not sent)."""
    return JSONResponse(
        {
            "success": True,
            "preview": True,
            "sensor": data.sensor,
            "actor": data.actor,
            "object": data.object.model_dump(by_alias=True)
            if hasattr(data.object, "model_dump")
            else data.object,
            "events": [
                e.model_dump(by_alias=True) if hasattr(e, "model_dump") else e for e in data.events
            ],
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Handler
# ─────────────────────────────────────────────────────────────────────────────


def create_activity_handler(
    *,
    env: Environment,
    api: ApiCredentials,
    identity: IdentityConfig,
    app_config: AppConfig,
    hooks: TimebackHooks | None = None,
) -> Callable[[Request], Awaitable[Response]]:
    """
    Create the activity POST handler.

    Args:
        env: Environment (local, staging, production)
        api: API credentials for Timeback API (required)
        identity: Identity configuration (SSO or custom mode)
        app_config: App configuration from timeback.config.json
        hooks: Optional hooks for customizing behavior

    Returns:
        The activity request handler
    """
    api_env = map_env_for_api(env)

    async def handler(request: Request) -> Response:
        # Check for preview mode
        preview_requested = (
            request.query_params.get("preview") == "1"
            or request.headers.get("x-timeback-preview") == "1"
        )

        # 1. Authenticate - get user info
        user_info: ActivityUserInfo | None = None

        if isinstance(identity, CustomIdentityConfig) or identity.mode == "custom":
            # Custom mode: get email
            get_email = identity.get_email
            if not get_email:
                return JSONResponse(
                    {"success": False, "error": "No getEmail configured"},
                    status_code=500,
                )
            result = get_email(request)
            email = await result if inspect.isawaitable(result) else result

            if not email:
                return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=401)

            user_info = ActivityUserInfo(email=email)

        else:
            # SSO mode: get user from session (should have timebackId)
            # Note: identity must be SsoIdentityConfig here since IdentityConfig is a union
            get_user = identity.get_user
            if not get_user:
                return JSONResponse(
                    {"success": False, "error": "No getUser configured"},
                    status_code=500,
                )
            result = get_user(request)
            user = await result if inspect.isawaitable(result) else result

            if not user:
                return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=401)

            user_info = ActivityUserInfo(email=user.email, timeback_id=user.id)

        # 2. Validate request
        body = await request.json()
        payload, course_config, sensor, error_response = _validate_activity_request(
            body, app_config
        )

        if error_response:
            return error_response

        if not payload or not course_config or not sensor:
            return JSONResponse(
                {"success": False, "error": "Validation failed"},
                status_code=500,
            )

        # 3. Submit events
        client = TimebackClient(
            env=api_env,
            client_id=api.client_id,
            client_secret=api.client_secret,
        )

        try:
            # Resolve timeback ID if not already known
            timeback_id = user_info.timeback_id
            if not timeback_id:
                try:
                    timeback_id = await lookup_timeback_id_by_email(
                        email=user_info.email,
                        client=client,
                    )
                except TimebackUserResolutionError as e:
                    log.warning("Failed to resolve Timeback user: %s", e.code)
                    return JSONResponse(
                        {"success": False, "error": "Unable to resolve Timeback identity"},
                        status_code=resolve_status_for_user_resolution_error(e),
                    )

            # Build actor
            actor = TimebackUser(
                id=f"urn:timeback:user:{timeback_id}",
                type="TimebackUser",
                email=user_info.email,
            )

            # Build activity context (may throw MissingSyncedCourseIdError, InvalidSensorUrlError)
            obj = _build_activity_context(
                payload,
                course_config,
                app_config.name,
                api_env,
                sensor,
            )

            # Build metrics
            activity_metrics = _build_activity_metrics(payload.metrics)
            time_spent_metrics = _build_time_spent_metrics(payload.elapsed_ms, payload.paused_ms)

            # Create events
            activity_event = create_activity_event(
                input=ActivityCompletedInput(
                    actor=actor,
                    object=obj,
                    metrics=activity_metrics,
                    event_time=payload.ended_at or None,
                )
            )

            time_spent_event = create_time_spent_event(
                input=TimeSpentInput(
                    actor=actor,
                    object=obj,
                    metrics=time_spent_metrics,
                    event_time=payload.ended_at or None,
                )
            )

            # Build before-send data for hooks/preview
            built_data = ActivityBeforeSendData(
                sensor=sensor,
                actor={"id": actor.id, "type": actor.type, "email": actor.email},
                object=obj,
                events=(activity_event, time_spent_event),
                payload=body,
                course=course_config,
                app_name=app_config.name,
                api_env=api_env,
                email=user_info.email,
                timeback_id=timeback_id,
            )

            # Call hook if provided
            hook_result = built_data
            if hooks and hooks.before_activity_send:
                hook_fn = hooks.before_activity_send
                result = hook_fn(built_data)
                hook_result = await result if inspect.isawaitable(result) else result

            effective_data = hook_result if hook_result is not None else built_data

            # Determine whether to skip send
            # - preview_requested: explicit request preview
            # - hook_result is None: hook chose to skip send (demo/test)
            skip_send = preview_requested or hook_result is None

            if skip_send:
                return _build_preview_response(effective_data)

            # Write gradebook entry (best-effort, non-blocking)
            # Extract courseId from the built context object if available
            course_id = None
            if hasattr(effective_data.object, "course") and effective_data.object.course:
                course_id = getattr(effective_data.object.course, "id", None)

            if course_id:
                await write_gradebook_entry(
                    client=client,
                    course_id=course_id,
                    activity_id=effective_data.payload.get("id", ""),
                    activity_name=effective_data.payload.get("name", ""),
                    timeback_id=effective_data.timeback_id,
                    ended_at=effective_data.payload.get("endedAt", ""),
                    metrics=effective_data.payload.get("metrics", {}),
                    pct_complete_app=effective_data.payload.get("pctCompleteApp"),
                    app_name=effective_data.app_name,
                )

            # Send both events in one envelope
            await client.caliper.events.send(
                effective_data.sensor,
                list(effective_data.events),
            )

            selector_desc = _format_course_selector(payload.course)
            log.debug("Submitted activity: course=%s, id=%s", selector_desc, payload.id)

            return JSONResponse({"success": True})

        except MissingSyncedCourseIdError as e:
            log.error("Course not synced: %s, env=%s", e.course, e.env)
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        except InvalidSensorUrlError as e:
            log.error("Invalid sensor URL: %s", e.sensor)
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        except Exception as e:
            selector_desc = _format_course_selector(payload.course)
            log.error(
                "Failed to submit activity: course=%s, id=%s, error=%s",
                selector_desc,
                payload.id,
                str(e),
            )
            return JSONResponse({"success": False, "error": str(e)}, status_code=502)

        finally:
            await client.close()

    return handler
