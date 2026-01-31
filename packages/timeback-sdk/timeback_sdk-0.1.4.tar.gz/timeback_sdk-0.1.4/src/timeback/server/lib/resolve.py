"""
Resolution Utilities

Functions for resolving Timeback users.

User Resolution:
- resolveTimebackUserByEmail — Full user resolution returning profile + IdP claims.
  Used by SSO callback to build the authenticated user object.
- lookupTimebackIdByEmail — Simple lookup returning just the timebackId.
  Used by activity/user handlers when only the ID is needed.
- resolve_status_for_user_resolution_error — Maps error codes to HTTP status.
  Used by handlers to return appropriate status codes on resolution failure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .logger import create_scoped_logger
from .utils import map_env_for_api

if TYPE_CHECKING:
    from timeback_core import TimebackClient

    from ...shared.types import (
        Environment,
        IdentityClaims,
        TimebackAuthUser,
        TimebackUserResolutionErrorCode,
    )
    from ..types import ApiCredentials, OIDCUserInfo

log = create_scoped_logger("resolve")


# ─────────────────────────────────────────────────────────────────────────────
# User Resolution - Errors
# ─────────────────────────────────────────────────────────────────────────────


class TimebackUserResolutionError(Exception):
    """Error thrown when Timeback user resolution fails."""

    def __init__(self, message: str, code: TimebackUserResolutionErrorCode) -> None:
        super().__init__(message)
        self.code = code


def resolve_status_for_user_resolution_error(err: TimebackUserResolutionError) -> int:
    """
    Map a user resolution error to an HTTP status code.

    Args:
        err: Timeback user resolution error

    Returns:
        HTTP status code (409 for ambiguous, 404 otherwise)
    """
    return 409 if err.code == "timeback_user_ambiguous" else 404


# ─────────────────────────────────────────────────────────────────────────────
# User Resolution - Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _redact_email(email: str) -> str:
    """Redact email for logging."""
    if "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    if len(local) <= 2:
        return f"**@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def _format_person_name(given_name: str | None, family_name: str | None) -> str | None:
    """Format a person's full name from given and family names."""
    parts = [p for p in [given_name, family_name] if p]
    return " ".join(parts) if parts else None


def _build_identity_claims(user_info: OIDCUserInfo) -> IdentityClaims:
    """Build IdentityClaims from OIDC user info."""
    from ...shared.types import IdentityClaims

    return IdentityClaims(
        sub=user_info.get("sub", ""),
        email=user_info.get("email", ""),
        first_name=user_info.get("given_name"),
        last_name=user_info.get("family_name"),
        picture_url=user_info.get("picture"),
    )


async def _lookup_single_user_by_email(
    client: TimebackClient,
    email: str,
) -> dict[str, Any]:
    """
    Look up a single user by email, throwing on not-found or ambiguous.

    Args:
        client: Timeback client
        email: User's email address

    Returns:
        The matched OneRoster user with validated sourcedId

    Raises:
        TimebackUserResolutionError: If lookup fails
    """
    result = await client.oneroster.users.list(
        where={"email": email},
        limit=2,  # detect ambiguous matches
    )

    users = result.data

    if len(users) == 0:
        log.warning("No Timeback user found for email: %s", _redact_email(email))
        raise TimebackUserResolutionError(
            f"No Timeback user found with email: {email}",
            "timeback_user_not_found",
        )

    if len(users) > 1:
        log.error(
            "Multiple Timeback users found for email: %s (count: %d)",
            _redact_email(email),
            len(users),
        )
        raise TimebackUserResolutionError(
            f"Multiple Timeback users found with email: {email}",
            "timeback_user_ambiguous",
        )

    user = users[0]

    if not user.sourced_id:
        raise TimebackUserResolutionError(
            "Timeback user is missing sourcedId",
            "timeback_user_lookup_failed",
        )

    # Get primary org from roles if available
    primary_org = None
    if user.roles:
        for role in user.roles:
            if role.role_type == "primary" and role.org:
                primary_org = {
                    "sourcedId": role.org.sourced_id,
                    "name": getattr(role.org, "name", None),
                }
                break

    # Build orgs list from user.orgs
    orgs = None
    if user.orgs:
        orgs = [
            {"sourcedId": org.sourced_id, "name": getattr(org, "name", None)} for org in user.orgs
        ]

    return {
        "sourcedId": user.sourced_id,
        "email": user.email or email,
        "givenName": user.given_name,
        "familyName": user.family_name,
        "primaryOrg": primary_org,
        "orgs": orgs,
        "grades": user.grades,
    }


# ─────────────────────────────────────────────────────────────────────────────
# User Resolution - Public API
# ─────────────────────────────────────────────────────────────────────────────


async def resolve_timeback_user_by_email(
    *,
    env: Environment,
    api_credentials: ApiCredentials,
    user_info: OIDCUserInfo,
    client: TimebackClient | None = None,
) -> TimebackAuthUser:
    """
    Resolve a full TimebackAuthUser by email.

    Use case: SSO callback — after OIDC authentication, look up the Timeback
    user and return a complete auth object with profile data and IdP claims.

    Args:
        env: Environment (staging/production)
        api_credentials: API credentials for Timeback API
        user_info: OIDC user info from the IdP
        client: Optional pre-configured Timeback client

    Returns:
        TimebackAuthUser with profile and IdP claims

    Raises:
        TimebackUserResolutionError: If resolution fails
    """
    from timeback_core import TimebackClient as TBClient

    from ...shared.types import SchoolInfo, TimebackAuthUser

    email = user_info.get("email")

    if not email:
        log.error("Missing email in IdP user info, sub=%s", user_info.get("sub"))
        raise TimebackUserResolutionError(
            "IdP did not return an email address, which is required to resolve Timeback identity",
            "missing_email",
        )

    log.debug("Resolving Timeback user by email: %s, env=%s", _redact_email(email), env)

    provided_client = client
    api_env = map_env_for_api(env)

    if provided_client is None:
        client = TBClient(
            env=api_env,
            client_id=api_credentials.client_id,
            client_secret=api_credentials.client_secret,
        )
    else:
        client = provided_client

    try:
        user = await _lookup_single_user_by_email(client, email)

        # Build school info from primaryOrg dict
        school = None
        primary_org = user.get("primaryOrg")
        if primary_org:
            org_id = primary_org.get("sourcedId")
            org_name = primary_org.get("name")
            if org_id:
                school = SchoolInfo(id=org_id, name=org_name or org_id)

        # Get grade (max of grades array)
        grades = user.get("grades")
        grade = max(grades) if grades else None

        # Build profile
        auth_user = TimebackAuthUser(
            id=user["sourcedId"],
            email=user.get("email") or email,
            name=_format_person_name(user.get("givenName"), user.get("familyName")),
            school=school,
            grade=grade,
            claims=_build_identity_claims(user_info),
        )

        return auth_user

    except TimebackUserResolutionError:
        raise
    except Exception as e:
        message = str(e)
        log.error("Failed to lookup Timeback user: %s, error=%s", _redact_email(email), message)
        raise TimebackUserResolutionError(
            f"Failed to lookup Timeback user: {message}",
            "timeback_user_lookup_failed",
        ) from e
    finally:
        if provided_client is None and client is not None:
            await client.close()


async def lookup_timeback_id_by_email(
    *,
    email: str,
    client: TimebackClient,
) -> str:
    """
    Look up the Timeback user ID by email.

    Use case: Activity/user handlers — when you only need the timebackId,
    not the full auth object.

    Args:
        email: User's email address
        client: Pre-configured Timeback client

    Returns:
        The Timeback user ID (sourcedId)

    Raises:
        TimebackUserResolutionError: If lookup fails
    """
    log.debug("Looking up Timeback user ID by email: %s", _redact_email(email))

    try:
        user = await _lookup_single_user_by_email(client, email)
        return user["sourcedId"]
    except TimebackUserResolutionError:
        raise
    except Exception as e:
        message = str(e)
        log.error("Failed to lookup Timeback user: %s, error=%s", _redact_email(email), message)
        raise TimebackUserResolutionError(
            f"Failed to lookup Timeback user: {message}",
            "timeback_user_lookup_failed",
        ) from e
