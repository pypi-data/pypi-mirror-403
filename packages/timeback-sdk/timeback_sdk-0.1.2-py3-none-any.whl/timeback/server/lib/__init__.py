"""Internal server utilities."""

from .logger import create_scoped_logger, oidc_log, sso_log
from .oidc import OIDCClient
from .resolve import (
    ActivityCourseResolutionError,
    TimebackUserResolutionError,
    lookup_timeback_id_by_email,
    resolve_activity_course,
    resolve_status_for_user_resolution_error,
    resolve_timeback_user_by_email,
)
from .utils import decode_base64_url, encode_base64_url, map_env_for_api

__all__ = [
    "ActivityCourseResolutionError",
    "OIDCClient",
    "TimebackUserResolutionError",
    "create_scoped_logger",
    "decode_base64_url",
    "encode_base64_url",
    "lookup_timeback_id_by_email",
    "map_env_for_api",
    "oidc_log",
    "resolve_activity_course",
    "resolve_status_for_user_resolution_error",
    "resolve_timeback_user_by_email",
    "sso_log",
]
