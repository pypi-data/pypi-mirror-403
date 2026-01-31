"""
Activity Handler

Route handler for activity tracking and submission.
"""

from ...lib.utils import safe_id_segment
from ...types import (
    ActivityHandlerDeps,
    ActivityUserInfo,
    ValidatedActivityPayload,
    ValidationError,
    ValidationSuccess,
)
from .attempts import (
    compute_caliper_line_item_id,
    resolve_caliper_attempt_number,
)
from .caliper import (
    InvalidSensorUrlError,
    MissingSyncedCourseIdError,
    build_activity_context,
    build_activity_events,
    build_activity_metrics,
    build_canonical_activity_url,
    build_oneroster_course_url,
    build_oneroster_user_url,
    build_time_spent_metrics,
)
from .completion import maybe_write_completion_entry
from .handler import create_activity_handler
from .progress import (
    compute_progress,
    resolve_total_lessons,
)
from .resolve import (
    ActivityCourseResolutionError,
    resolve_activity_course,
)
from .schema import (
    format_course_selector,
    validate_activity_request,
)

__all__ = [
    "ActivityCourseResolutionError",
    "ActivityHandlerDeps",
    "ActivityUserInfo",
    "InvalidSensorUrlError",
    "MissingSyncedCourseIdError",
    "ValidatedActivityPayload",
    "ValidationError",
    "ValidationSuccess",
    "build_activity_context",
    "build_activity_events",
    "build_activity_metrics",
    "build_canonical_activity_url",
    "build_oneroster_course_url",
    "build_oneroster_user_url",
    "build_time_spent_metrics",
    "compute_caliper_line_item_id",
    "compute_progress",
    "create_activity_handler",
    "format_course_selector",
    "maybe_write_completion_entry",
    "resolve_activity_course",
    "resolve_caliper_attempt_number",
    "resolve_total_lessons",
    "safe_id_segment",
    "validate_activity_request",
]
