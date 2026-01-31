"""Shared types used by both client and server."""

from dataclasses import dataclass, field
from typing import Literal

# Environment types
Environment = Literal["local", "staging", "production"]
ApiEnvironment = Literal["staging", "production"]

# Timeback subject and grade types
TimebackSubject = Literal["Math", "Reading", "Science", "Social Studies", "Writing", "Other"]
TimebackGrade = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


@dataclass
class TimebackUser:
    """
    Basic user identity.

    Kept for backwards compatibility. Prefer TimebackIdentity for new code.
    """

    id: str
    email: str
    name: str | None = None


@dataclass
class TimebackIdentity:
    """User identity returned from SSO."""

    id: str
    email: str
    name: str | None = None


@dataclass
class SchoolInfo:
    """School information."""

    id: str
    name: str


@dataclass
class CourseInfo:
    """Course information for profile."""

    id: str
    code: str
    name: str


@dataclass
class XpInfo:
    """XP information."""

    today: int
    """XP earned today (UTC day range)."""
    all: int
    """XP earned across all time."""


@dataclass
class GoalsInfo:
    """Goals and progress from course metadata."""

    daily_xp: int | None = None
    daily_lessons: int | None = None
    daily_active_minutes: int | None = None
    daily_accuracy: int | None = None
    daily_mastered_units: int | None = None


@dataclass
class TimebackProfile:
    """
    Timeback user profile with enriched data from the Timeback API.

    This is the full profile returned by /user/me and includes
    school info, grade, courses, goals, and XP data.
    """

    id: str
    """Timeback user ID."""
    email: str
    """User's email address."""
    name: str | None = None
    """User's display name."""
    school: SchoolInfo | None = None
    """School information."""
    grade: int | None = None
    """Grade level."""
    xp: XpInfo | None = None
    """XP earned on this app."""
    courses: list[CourseInfo] | None = None
    """Enrolled courses."""
    goals: GoalsInfo | None = None
    """Goals and progress."""


@dataclass
class TimebackSessionUser:
    """
    Recommended minimal user payload to persist in a session.

    This is a minimal, serializable subset of TimebackProfile designed
    for cookie-based sessions (small payload) while still carrying enough
    Timeback context for common UI affordances.
    """

    id: str
    email: str
    name: str | None = None
    school: SchoolInfo | None = None
    grade: int | None = None


@dataclass
class IdentityClaims:
    """
    Claims from the identity provider (IdP).

    Normalized subset of OIDC UserInfo claims.
    """

    sub: str
    """Subject identifier (unique user ID from IdP)."""
    email: str
    """User's email address."""
    first_name: str | None = None
    """User's first/given name."""
    last_name: str | None = None
    """User's last/family name."""
    picture_url: str | None = None
    """User's profile picture URL."""


@dataclass
class TimebackAuthUser(TimebackProfile):
    """
    Authenticated user with Timeback profile and IdP claims.

    This is the primary user object returned during SSO callback when using
    createTimeback(). The id field is the canonical timebackId (stable identifier).
    """

    claims: IdentityClaims = field(kw_only=True)
    """IdP claims (raw identity provider data). Always present after resolution."""


# ─────────────────────────────────────────────────────────────────────────────
# Activity Types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SubjectGradeCourseRef:
    """
    Course selector by subject and grade (grade-based apps).

    Use this for traditional K-12 apps where courses are identified by subject + grade.
    """

    subject: TimebackSubject
    grade: TimebackGrade


@dataclass
class CourseCodeRef:
    """
    Course selector by code (grade-less apps).

    Use this for apps without grade levels (e.g., CS platforms) where courses
    are identified by a unique course code.
    """

    code: str


# Union type for course selectors
ActivityCourseRef = SubjectGradeCourseRef | CourseCodeRef
"""
Course selector for activity tracking.

This should correspond to a unique course entry in `timeback.config.json`.

Two selector modes are supported:
- **Grade-based**: `SubjectGradeCourseRef(subject, grade)` — K-12 style
- **Grade-less**: `CourseCodeRef(code)` — CS/skill-based

Example (Grade-based):
    ```python
    SubjectGradeCourseRef(subject="Math", grade=3)
    ```

Example (Grade-less):
    ```python
    CourseCodeRef(code="CS-101")
    ```
"""


def is_subject_grade_course_ref(ref: ActivityCourseRef) -> bool:
    """
    Type guard: Check if a course ref uses subject+grade identity.

    Args:
        ref: Course reference to check

    Returns:
        True if grade-based selector (SubjectGradeCourseRef), False otherwise
    """
    return isinstance(ref, SubjectGradeCourseRef)


@dataclass
class ActivityParams:
    """Activity start parameters."""

    id: str
    """Unique identifier for the learning object."""
    name: str
    """Display name of the activity."""
    course: ActivityCourseRef
    """Course selector (must match a unique course in timeback.config.json)."""


@dataclass
class ActivityMetrics:
    """Activity metrics (optional performance data)."""

    total_questions: int | None = None
    """Total questions attempted."""
    correct_questions: int | None = None
    """Number of correct answers."""
    xp_earned: int | None = None
    """XP earned from this activity."""
    mastered_units: int | None = None
    """Number of units mastered."""


@dataclass
class ActivityEndPayload:
    """Activity state sent to the server when ending."""

    id: str
    """Unique identifier for the learning object."""
    name: str
    """Display name of the activity."""
    course: ActivityCourseRef
    """Course selector (must match a unique course in timeback.config.json)."""
    started_at: str
    """ISO 8601 timestamp when activity started."""
    ended_at: str
    """ISO 8601 timestamp when activity ended."""
    elapsed_ms: int
    """Active time in milliseconds (excluding paused time)."""
    paused_ms: int
    """Total paused time in milliseconds."""
    metrics: ActivityMetrics = field(default_factory=ActivityMetrics)
    """Activity metrics."""


@dataclass
class ActivityResponse:
    """Activity submission response."""

    success: bool
    error: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Error Types
# ─────────────────────────────────────────────────────────────────────────────

TimebackUserResolutionErrorCode = Literal[
    "missing_email",
    "timeback_user_not_found",
    "timeback_user_ambiguous",
    "timeback_user_lookup_failed",
]
