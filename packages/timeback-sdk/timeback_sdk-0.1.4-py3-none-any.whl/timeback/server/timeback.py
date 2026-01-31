"""
Timeback Server SDK

Factory function to create the Timeback server instance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypedDict
from urllib.parse import urlparse

from .handlers import Handlers, IdentityOnlyHandlers, create_handlers, create_identity_only_handlers
from .lib.utils import map_env_for_api

if TYPE_CHECKING:
    from .types import IdentityOnlyConfig, TimebackConfig


class CourseGoals(TypedDict, total=False):
    """Course goals metadata."""

    daily_xp: int
    daily_lessons: int
    daily_active_minutes: int
    daily_accuracy: int
    daily_mastered_units: int


class CourseMetrics(TypedDict, total=False):
    """Course metrics metadata for progress computation.

    These values define denominators for course-level progress calculations.
    """

    totalXp: int
    totalLessons: int
    totalGrades: int


class CourseIds(TypedDict, total=False):
    """Environment-specific course IDs."""

    staging: str
    production: str


class CourseMetadata(TypedDict, total=False):
    """Course metadata."""

    goals: CourseGoals
    metrics: CourseMetrics


class CourseEnvOverrides(TypedDict, total=False):
    """Environment-specific course overrides.

    Non-identity fields that can differ per environment.
    Excludes identity fields (subject, grade, course_code) and ids (already env-scoped).
    """

    level: str
    sensor: str
    # JSON config uses camelCase: overrides.staging.launchUrl
    launchUrl: str
    metadata: CourseMetadata


class CourseOverrides(TypedDict, total=False):
    """Per-environment course overrides.

    Allows staging and production to have different non-identity properties.
    """

    staging: CourseEnvOverrides
    production: CourseEnvOverrides


class CourseConfig(TypedDict, total=False):
    """Course configuration from timeback.config.json.

    Course identity is determined by one of:
    - **Grade-based**: `(subject, grade)` — traditional K-12 courses
    - **Grade-less**: `course_code` — apps without grade levels (e.g., CS platforms)

    At least one identity must be present:
    - If `grade` is provided, the course is identified by `(subject, grade)`.
    - If `grade` is omitted, `course_code` is required as the identifier.

    Sensor resolution:
    - Each course must have an effective sensor (either `sensor` or top-level `sensor`).

    Environment overrides:
    - Use `overrides.staging` or `overrides.production` to vary non-identity fields per env.
    """

    subject: str
    grade: int  # Optional for grade-less courses
    course_code: str  # Required when grade is omitted
    level: str
    ids: CourseIds | None
    metadata: CourseMetadata
    sensor: str  # Per-course sensor URL (overrides top-level sensor)
    launch_url: str  # LTI launch URL for this course
    overrides: CourseOverrides  # Environment-specific overrides


class ConfigValidationError(Exception):
    """Error raised when timeback.config.json fails validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class AppConfig:
    """App configuration from timeback.config.json.

    Sensor resolution: every course must have an effective sensor.
    - Set `sensor` at the top level as a default for all courses.
    - Override per course with `courses[].sensor`.
    """

    name: str
    sensor: str | None = None  # Default sensor URL for all courses
    launch_url: str | None = None  # Default LTI launch URL for all courses
    courses: list[CourseConfig] = field(default_factory=list)


@dataclass
class TimebackInstance:
    """Timeback SDK instance (framework-agnostic)."""

    config: TimebackConfig
    app_config: AppConfig
    handle: Handlers


@dataclass
class IdentityOnlyInstance:
    """Identity-only SDK instance (framework-agnostic).

    This instance only provides identity handlers and does not require
    Timeback API credentials or timeback.config.json.
    """

    config: IdentityOnlyConfig
    handle: IdentityOnlyHandlers


def _merge_metadata(
    base: CourseMetadata | None,
    override: CourseMetadata | None,
) -> CourseMetadata | None:
    """
    Deep merge two metadata objects.

    Merges top-level fields, and deep-merges `goals` so partial
    overrides don't require repeating unchanged values.

    Args:
        base: Base metadata
        override: Override metadata (takes precedence)

    Returns:
        Merged metadata
    """
    if not base and not override:
        return None
    if not base:
        return override
    if not override:
        return base

    result: CourseMetadata = {**base, **override}
    # Deep merge goals
    if base.get("goals") or override.get("goals"):
        result["goals"] = {**base.get("goals", {}), **override.get("goals", {})}
    return result


def _resolve_course_for_env(
    course: CourseConfig,
    env: str,
) -> CourseConfig:
    """
    Resolve a course configuration for a specific environment.

    Applies merge precedence: course → overrides[env]

    Args:
        course: The course configuration
        env: Target environment ('staging' or 'production')

    Returns:
        Resolved course configuration with env-specific overrides applied
    """
    overrides = course.get("overrides")
    if not overrides:
        return course

    env_overrides = overrides.get(env)  # type: ignore[literal-required]
    if not env_overrides:
        return course

    # Create resolved course (copy base, apply overrides)
    resolved: CourseConfig = {**course}

    if env_overrides.get("level"):
        resolved["level"] = env_overrides["level"]
    if env_overrides.get("sensor"):
        resolved["sensor"] = env_overrides["sensor"]
    # Support both camelCase (JSON) and snake_case (internal) for overrides
    if env_overrides.get("launchUrl"):
        resolved["launch_url"] = env_overrides["launchUrl"]
    if env_overrides.get("launch_url"):
        resolved["launch_url"] = env_overrides["launch_url"]

    resolved_metadata = _merge_metadata(course.get("metadata"), env_overrides.get("metadata"))
    if resolved_metadata:
        resolved["metadata"] = resolved_metadata

    return resolved


def _derive_sensor_from_launch_url(launch_url: str) -> str | None:
    """Derive a Caliper sensor URL from a launch URL.

    Per `docs/arch/sensor.md`, the default sensor is derived from the launch URL origin:
    `new URL(launchUrl).origin` (JS) ~= `{scheme}://{netloc}` (Python).
    """

    parsed = urlparse(launch_url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _validate_config(app_config: AppConfig) -> None:
    """
    Validate app configuration.

    Raises:
        ConfigValidationError: When validation fails
    """
    courses = app_config.courses
    top_sensor = app_config.sensor

    # Track for uniqueness checks
    grade_based_keys: set[str] = set()
    course_codes: set[str] = set()

    for i, course in enumerate(courses):
        has_grade = "grade" in course and course.get("grade") is not None
        has_code = "course_code" in course and course.get("course_code")

        # 1. Each course must have either grade or course_code
        if not has_grade and not has_code:
            raise ConfigValidationError(
                f"Course at index {i} must have either 'grade' or 'course_code' (courseCode)"
            )

        # 2. Check uniqueness of (subject, grade) pairs
        if has_grade:
            key = f"{course.get('subject')}:{course.get('grade')}"
            if key in grade_based_keys:
                raise ConfigValidationError(
                    f"Duplicate (subject, grade) pair found: {course.get('subject')} grade {course.get('grade')}"
                )
            grade_based_keys.add(key)

        # 3. Check uniqueness of course_code
        if has_code:
            code = course.get("course_code")
            if code in course_codes:
                raise ConfigValidationError(f"Duplicate course_code found: {code}")
            course_codes.add(code)  # type: ignore[arg-type]

        # 4. Each course must have an effective sensor
        course_sensor = course.get("sensor")
        effective_launch_url = course.get("launch_url") or app_config.launch_url
        derived_sensor = (
            _derive_sensor_from_launch_url(effective_launch_url) if effective_launch_url else None
        )
        if not course_sensor and not top_sensor and not derived_sensor:
            identifier = (
                course.get("course_code")
                if has_code
                else f"{course.get('subject')} grade {course.get('grade')}"
            )
            raise ConfigValidationError(
                f"Course '{identifier}' has no effective sensor. "
                "Set a top-level 'sensor', per-course 'sensor', or provide a 'launchUrl' "
                "so the sensor can be derived from its origin."
            )


def _load_config(config_path: str | None = None) -> AppConfig:
    """
    Load app configuration from timeback.config.json.

    Looks for timeback.config.json in the current directory or uses config_path.

    The config file should be a JSON object with:
    - name: App display name
    - sensor: Default Caliper sensor URL for activity events
    - launchUrl: Default LTI launch URL for all courses
    - courses: List of course configurations with:
        - subject: Subject name (Math, Reading, etc.)
        - grade: Grade level (0-12), optional for grade-less courses
        - courseCode: Course code, required when grade is omitted
        - level: Optional level (e.g., "honors")
        - sensor: Optional per-course sensor URL (overrides top-level)
        - launchUrl: Optional per-course LTI launch URL
        - ids: Environment-specific course IDs (staging, production)
        - metadata: Optional metadata including goals

    Raises:
        ConfigValidationError: When config validation fails
    """
    import json
    from pathlib import Path

    path = Path(config_path) if config_path else Path.cwd() / "timeback.config.json"

    if not path.exists():
        raise ConfigValidationError(
            f"No timeback config found at {path}. "
            "Create a timeback.config.json file with your app configuration."
        )

    # Load the JSON config
    try:
        with path.open("r", encoding="utf-8") as f:
            config: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"Invalid JSON in {path}: {e}") from e

    # Parse courses
    raw_courses = config.get("courses", [])
    courses: list[CourseConfig] = []
    for raw_course in raw_courses:
        course: CourseConfig = {
            "subject": raw_course.get("subject", "Other"),
        }
        # Grade is optional for grade-less courses
        if "grade" in raw_course and raw_course.get("grade") is not None:
            course["grade"] = raw_course.get("grade")
        # Accept camelCase from JSON (courseCode -> course_code)
        if "courseCode" in raw_course:
            course["course_code"] = raw_course.get("courseCode")
        if "level" in raw_course:
            course["level"] = raw_course["level"]
        if "ids" in raw_course:
            course["ids"] = raw_course["ids"]
        if "metadata" in raw_course:
            course["metadata"] = raw_course["metadata"]
        # Per-course sensor URL
        if "sensor" in raw_course:
            course["sensor"] = raw_course["sensor"]
        # Per-course launch URL
        if "launchUrl" in raw_course:
            course["launch_url"] = raw_course["launchUrl"]
        # Environment-specific overrides
        if "overrides" in raw_course:
            course["overrides"] = raw_course["overrides"]
        courses.append(course)

    # Return config without validation (validation happens after env-specific resolution)
    return AppConfig(
        name=config.get("name", "Timeback App"),
        sensor=config.get("sensor"),
        launch_url=config.get("launchUrl"),
        courses=courses,
    )


async def create_server(config: TimebackConfig) -> TimebackInstance:
    """
    Create a Timeback server instance.

    Returns a framework-agnostic instance with raw handlers.
    Use an adapter to integrate with your framework:
    - `to_fastapi_router()` for FastAPI
    - `to_django_urls()` for Django (coming soon)

    Args:
        config: Server configuration

    Returns:
        Timeback instance with handlers

    Example:
        ```python
        from timeback.server import create_server, TimebackConfig, SsoIdentityConfig

        timeback = await create_server(TimebackConfig(
            env="staging",
            api=ApiCredentials(
                client_id=os.environ["TIMEBACK_API_CLIENT_ID"],
                client_secret=os.environ["TIMEBACK_API_CLIENT_SECRET"],
            ),
            identity=SsoIdentityConfig(
                mode="sso",
                client_id=os.environ["AWS_COGNITO_CLIENT_ID"],
                client_secret=os.environ["AWS_COGNITO_CLIENT_SECRET"],
                get_user=get_session_user,
                on_callback_success=handle_sso_success,
            ),
        ))

        # For FastAPI
        from timeback.server.adapters.fastapi import to_fastapi_router
        app.include_router(to_fastapi_router(timeback), prefix="/api/timeback")
        ```
    """
    raw_app_config = _load_config(config.config_path if hasattr(config, "config_path") else None)

    env_for_overrides = map_env_for_api(config.env)

    resolved_courses = [
        _resolve_course_for_env(course, env_for_overrides) for course in raw_app_config.courses
    ]

    app_config = AppConfig(
        name=raw_app_config.name,
        sensor=raw_app_config.sensor,
        launch_url=raw_app_config.launch_url,
        courses=resolved_courses,
    )

    # Ensure every course has an effective sensor by deriving from launchUrl when needed.
    # Resolution order (docs/arch/sensor.md):
    # 1) env override (already merged into course.sensor)
    # 2) course.sensor
    # 3) top-level app_config.sensor
    # 4) derived from effective launchUrl origin
    if not app_config.sensor:
        for course in app_config.courses:
            if course.get("sensor"):
                continue
            effective_launch_url = course.get("launch_url") or app_config.launch_url
            if not effective_launch_url:
                continue
            derived = _derive_sensor_from_launch_url(effective_launch_url)
            if derived:
                course["sensor"] = derived

    # Validate configuration (after env-specific resolution)
    _validate_config(app_config)

    handlers = create_handlers(
        env=config.env,
        api=config.api,
        identity=config.identity,
        app_config=app_config,
        hooks=config.hooks if hasattr(config, "hooks") else None,
    )

    return TimebackInstance(
        config=config,
        app_config=app_config,
        handle=handlers,
    )


def create_identity_only_server(config: IdentityOnlyConfig) -> IdentityOnlyInstance:
    """
    Create an identity-only Timeback server instance.

    Use this when you only need SSO authentication without activity tracking
    or Timeback API integration. Does not require timeback.config.json or API credentials.

    Returns a framework-agnostic instance with identity-only handlers.
    Use an adapter to integrate with your framework:
    - `to_fastapi_router()` for FastAPI (with identity_only=True)

    Args:
        config: Identity-only configuration

    Returns:
        Identity-only Timeback instance with handlers

    Example:
        ```python
        from timeback.server import (
            create_identity_only_server,
            IdentityOnlyConfig,
            IdentityOnlySsoConfig,
        )

        timeback = create_identity_only_server(IdentityOnlyConfig(
            env="staging",
            identity=IdentityOnlySsoConfig(
                mode="sso",
                client_id=os.environ["COGNITO_CLIENT_ID"],
                client_secret=os.environ["COGNITO_CLIENT_SECRET"],
                on_callback_success=lambda ctx: ctx.redirect("/dashboard"),
                on_callback_error=lambda ctx: ctx.redirect("/login?error=sso_failed"),
            ),
        ))

        # For FastAPI
        from timeback.server.adapters.fastapi import to_fastapi_router
        app.include_router(
            to_fastapi_router(timeback, identity_only=True),
            prefix="/api/timeback",
        )
        ```
    """
    handlers = create_identity_only_handlers(
        env=config.env,
        identity=config.identity,
    )

    return IdentityOnlyInstance(
        config=config,
        handle=handlers,
    )
