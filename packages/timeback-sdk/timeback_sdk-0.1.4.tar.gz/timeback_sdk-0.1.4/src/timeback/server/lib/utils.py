"""
Server Utilities

Internal utility functions for the server SDK.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

if TYPE_CHECKING:
    from ...shared.types import ApiEnvironment, Environment


# ─────────────────────────────────────────────────────────────────────────────
# Cryptographic Helpers
# ─────────────────────────────────────────────────────────────────────────────


def sha256_hex(value: str) -> str:
    """
    Compute SHA-256 hash and return as hex string.

    Used for deterministic ID generation.

    Args:
        value: String to hash

    Returns:
        Hex-encoded SHA-256 digest
    """
    return hashlib.sha256(value.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Course Structure IDs
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CourseStructureIds:
    """IDs for OneRoster course structure entities."""

    course: str
    component: str
    resource: str
    component_resource: str


def derive_course_structure_ids(course_id: str) -> CourseStructureIds:
    """
    Derive standard course structure IDs from a course sourcedId.

    These IDs follow a deterministic pattern used by the sync process.

    Args:
        course_id: Course sourcedId

    Returns:
        CourseStructureIds with all derived IDs
    """
    return CourseStructureIds(
        course=course_id,
        component=f"{course_id}-component",
        resource=f"{course_id}-resource",
        component_resource=f"{course_id}-cr",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ID Helpers
# ─────────────────────────────────────────────────────────────────────────────


def safe_id_segment(value: str) -> str:
    """
    Build a safe ID segment from a string (URL-safe, no colons).

    URL-encodes the value then replaces % with _ for safe IDs.

    Args:
        value: The value to make safe

    Returns:
        A safe ID segment
    """
    return quote(value, safe="").replace("%", "_")


def _parse_iso_datetime(value: str) -> datetime | None:
    """
    Parse an ISO 8601 datetime string.

    Accepts both `Z` and offset forms (e.g. `+00:00`). Returns None if the
    value cannot be parsed.
    """
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        return datetime.fromisoformat(normalized)
    except Exception:
        return None


def same_instant(a: str, b: str) -> bool:
    """
    Compare two datetime strings, tolerating minor formatting differences.

    Falls back to string equality if either value is not parseable.
    """
    da = _parse_iso_datetime(a)
    db = _parse_iso_datetime(b)
    if da is not None and db is not None:
        return da == db
    return a == b


def hash_suffix_64_base36(value: str) -> str:
    """
    Create a compact deterministic hash suffix for IDs.

    Uses 64-bit FNV-1a over the input string and returns a base36-encoded suffix.
    This is **not** cryptographic, but is stable and compact for ID disambiguation.

    Args:
        value: String to hash

    Returns:
        Base36 hash suffix (lowercase alphanumeric, up to 12 chars)
    """
    # 64-bit FNV-1a parameters
    hash_val = 0xCBF29CE484222325
    prime = 0x100000001B3
    mod64 = 0xFFFFFFFFFFFFFFFF

    for char in value:
        hash_val ^= ord(char)
        hash_val = (hash_val * prime) & mod64

    # Convert to base36
    if hash_val == 0:
        base36 = "0"
    else:
        digits = "0123456789abcdefghijklmnopqrstuvwxyz"
        base36 = ""
        n = hash_val
        while n:
            base36 = digits[n % 36] + base36
            n //= 36

    # Use last 12 base36 chars to keep it short but collision-resistant enough
    return base36[-12:] if len(base36) > 12 else base36


# ─────────────────────────────────────────────────────────────────────────────
# Environment Mapping
# ─────────────────────────────────────────────────────────────────────────────


def map_env_for_api(env: Environment) -> ApiEnvironment:
    """
    Map SDK environment to the environment used for outbound Timeback API calls.

    The SDK's env config controls runtime mode, but for outbound service calls
    (OneRoster, Caliper, etc.) we need a real Timeback environment:

      - local      → staging (local dev uses staging services)
      - staging    → staging
      - production → production

    Args:
        env: SDK environment setting

    Returns:
        Environment to use for TimebackClient
    """
    if env == "local" or env == "staging":
        return "staging"
    return "production"


def encode_base64_url(data: Any) -> str:
    """
    Encode an object to a base64url-safe string.

    Used for OIDC state parameter.

    Args:
        data: Data to encode

    Returns:
        Base64url encoded string
    """
    json_str = json.dumps(data)
    return base64.urlsafe_b64encode(json_str.encode()).decode().rstrip("=")


def decode_base64_url(encoded: str) -> Any:
    """
    Decode a base64url string back to an object.

    Args:
        encoded: Base64url encoded string

    Returns:
        Decoded object
    """
    # Add back padding if needed
    padding = 4 - (len(encoded) % 4)
    if padding != 4:
        encoded += "=" * padding
    json_str = base64.urlsafe_b64decode(encoded.encode()).decode()
    return json.loads(json_str)
