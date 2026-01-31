"""Internal server utilities."""

from .logger import create_scoped_logger, oidc_log, sso_log
from .oidc import OIDCClient
from .resolve import (
    TimebackUserResolutionError,
    lookup_timeback_id_by_email,
    resolve_status_for_user_resolution_error,
    resolve_timeback_user_by_email,
)
from .utils import (
    CourseStructureIds,
    decode_base64_url,
    derive_course_structure_ids,
    encode_base64_url,
    map_env_for_api,
    sha256_hex,
)

__all__ = [
    "CourseStructureIds",
    "OIDCClient",
    "TimebackUserResolutionError",
    "create_scoped_logger",
    "decode_base64_url",
    "derive_course_structure_ids",
    "encode_base64_url",
    "lookup_timeback_id_by_email",
    "map_env_for_api",
    "oidc_log",
    "resolve_status_for_user_resolution_error",
    "resolve_timeback_user_by_email",
    "sha256_hex",
    "sso_log",
]
