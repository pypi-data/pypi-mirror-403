"""Server-specific types."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypedDict
from urllib.parse import parse_qs, urlparse

if TYPE_CHECKING:
    from timeback_core import TimebackClient

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from ..shared.types import Environment, TimebackAuthUser, TimebackIdentity, TimebackUser

__all__ = [
    "ActivityBeforeSendData",
    "ActivityHandlerDeps",
    "ActivityUserInfo",
    "ApiCredentials",
    "BeforeActivitySendFn",
    "BuildStateContext",
    "BuildStateFn",
    "CallbackErrorContext",
    "CallbackSuccessContext",
    "CustomIdentityConfig",
    "Environment",
    "GetEmailFn",
    "GetUserFn",
    "IdentityConfig",
    "IdentityOnlyCallbackSuccessContext",
    "IdentityOnlyConfig",
    "IdentityOnlySsoConfig",
    "IdpData",
    "OIDCTokens",
    "OIDCUserInfo",
    "OnCallbackErrorFn",
    "OnCallbackSuccessFn",
    "OnIdentityOnlyCallbackSuccessFn",
    "ParsedUrl",
    "SearchParams",
    "SsoIdentityConfig",
    "TimebackConfig",
    "TimebackHooks",
    "TimebackUser",
    "ValidatedActivityPayload",
    "ValidationError",
    "ValidationSuccess",
]


@dataclass
class ApiCredentials:
    """API credentials for Timeback API calls."""

    client_id: str
    client_secret: str


class _OIDCTokensRequired(TypedDict):
    """Required OIDC token fields."""

    access_token: str
    """Access token for API calls (required)."""
    token_type: str
    """Token type, usually "Bearer" (required)."""


class OIDCTokens(_OIDCTokensRequired, total=False):
    """OIDC tokens from identity provider.

    access_token and token_type are required; other fields are optional.
    """

    id_token: str
    """ID token containing user claims."""
    refresh_token: str
    """Refresh token for obtaining new access tokens."""
    expires_in: int
    """Token expiration in seconds."""


class OIDCUserInfo(TypedDict, total=False):
    """User info claims from identity provider.

    This TypedDict defines common OIDC claims. Real IdPs may return additional
    claims not listed here; use dict access (e.g., user_info.get("custom_claim"))
    for non-standard claims.
    """

    sub: str
    """Subject identifier (unique user ID from IdP)."""
    email: str
    """User's email address."""
    email_verified: bool | str
    """Whether email is verified (some IdPs return string "true"/"false")."""
    name: str
    """User's full name."""
    given_name: str
    """User's given/first name."""
    family_name: str
    """User's family/last name."""
    picture: str
    """User's profile picture URL."""
    username: str
    """Username in the IdP."""
    identities: str | list[dict[str, Any]]
    """Linked identity providers (JSON string from Cognito or list of objects)."""


@dataclass
class IdpData:
    """Raw identity provider data (tokens and user info claims)."""

    tokens: OIDCTokens
    user_info: OIDCUserInfo


class SearchParams:
    """
    Query parameters accessor with URLSearchParams-style interface.

    Provides .get() and .get_all() methods for accessing query parameters.
    """

    def __init__(self, params: dict[str, list[str]]) -> None:
        self._params = params

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get the first value for a query parameter."""
        values = self._params.get(key)
        return values[0] if values else default

    def get_all(self, key: str) -> list[str]:
        """Get all values for a query parameter."""
        return self._params.get(key, [])

    def has(self, key: str) -> bool:
        """Check if a query parameter exists."""
        return key in self._params

    def keys(self) -> list[str]:
        """Get all query parameter keys."""
        return list(self._params.keys())


class ParsedUrl:
    """
    Parsed URL object with convenient search params access.

    Example:
        ```python
        def build_state(ctx: BuildStateContext) -> dict:
            return_to = ctx.parsed_url.search_params.get("returnTo", "/")
            return {"returnTo": return_to}
        ```
    """

    def __init__(self, url: str) -> None:
        self._url = url
        self._parsed = urlparse(url)
        self._search_params = parse_qs(self._parsed.query)

    @property
    def href(self) -> str:
        """Full URL string."""
        return self._url

    @property
    def origin(self) -> str:
        """URL origin (scheme + netloc)."""
        return f"{self._parsed.scheme}://{self._parsed.netloc}"

    @property
    def pathname(self) -> str:
        """URL path."""
        return self._parsed.path

    @property
    def search(self) -> str:
        """URL query string (including leading ?)."""
        return f"?{self._parsed.query}" if self._parsed.query else ""

    @property
    def search_params(self) -> SearchParams:
        """Query parameters accessor (similar to TS URLSearchParams)."""
        return SearchParams(self._search_params)

    def __str__(self) -> str:
        return self._url


@dataclass
class BuildStateContext:
    """Context passed to build_state hook.

    Provides access to the incoming request and URL. The `parsed_url` property
    provides TS-like URL object ergonomics for accessing query parameters.

    Example:
        ```python
        def build_state(ctx: BuildStateContext) -> dict:
            # Access query params similar to TS: url.searchParams.get('returnTo')
            return_to = ctx.parsed_url.search_params.get("returnTo", "/dashboard")
            invite_id = ctx.parsed_url.search_params.get("inviteId")
            return {"returnTo": return_to, "inviteId": invite_id}
        ```
    """

    request: Request
    url: str
    """URL string (for backwards compatibility)."""

    @property
    def parsed_url(self) -> ParsedUrl:
        """Parsed URL object with TS-like searchParams access."""
        return ParsedUrl(self.url)


@dataclass
class CallbackSuccessContext:
    """
    Context passed to on_callback_success hook for full SDK.

    When using create_server() with SSO mode, the user field contains the
    enriched TimebackAuthUser with timebackId as the canonical identifier.
    Raw IdP data is available under idp.
    """

    user: TimebackAuthUser
    """Authenticated user with Timeback profile and IdP claims."""
    idp: IdpData
    """Raw identity provider data (tokens and user info)."""
    state: Any
    """State data from build_state (if provided)."""
    request: Request
    """The incoming callback request."""

    def redirect(self, url: str, headers: dict[str, str] | None = None) -> Response:
        """Create a redirect response."""
        response = RedirectResponse(url=url, status_code=302)
        if headers:
            for key, value in headers.items():
                response.headers[key] = value
        return response

    def json(self, data: Any, status: int = 200) -> Response:
        """Create a JSON response."""
        return JSONResponse(content=data, status_code=status)


@dataclass
class CallbackErrorContext:
    """Context passed to on_callback_error hook."""

    error: Exception
    error_code: str | None
    state: Any
    request: Request

    def redirect(self, url: str, headers: dict[str, str] | None = None) -> Response:
        """Create a redirect response."""
        response = RedirectResponse(url=url, status_code=302)
        if headers:
            for key, value in headers.items():
                response.headers[key] = value
        return response

    def json(self, data: Any, status: int = 200) -> Response:
        """Create a JSON response."""
        return JSONResponse(content=data, status_code=status)


# Type aliases for callbacks
GetUserFn = (
    Callable[[Request], TimebackIdentity | None]
    | Callable[[Request], Awaitable[TimebackIdentity | None]]
)
"""
Get the current user from the request.

This is called by the activity handler to associate activities with users.
Read your session cookie/JWT and return the user, or None if not authenticated.

For SSO mode: return { id: timebackId, email: userEmail }
"""

GetEmailFn = Callable[[Request], str | None] | Callable[[Request], Awaitable[str | None]]
"""
Get the current user's email from the request.

For custom identity mode, read your session cookie/JWT and return the user's email,
or None if not authenticated. The SDK resolves the Timeback user by email.
"""

OnCallbackSuccessFn = Callable[[CallbackSuccessContext], Response | Awaitable[Response]]
OnCallbackErrorFn = Callable[[CallbackErrorContext], Response | Awaitable[Response]]
BuildStateFn = Callable[[BuildStateContext], Any]


@dataclass
class SsoIdentityConfig:
    """
    SSO identity configuration for full SDK.

    When using create_server() with SSO mode, the callback provides an enriched
    TimebackAuthUser with timebackId as the canonical identifier. The SDK resolves
    the Timeback user by email using server API credentials.

    Required fields (must be provided):
    - client_id, client_secret: OIDC credentials
    - get_user: Callback to get current user from request
    - on_callback_success: Callback after successful SSO
    """

    # Required fields (no defaults) - must come first in dataclass
    client_id: str
    """OIDC client ID (required)."""
    client_secret: str
    """OIDC client secret (required)."""
    get_user: GetUserFn
    """
    Get the current user from the request (required).

    This is called by the activity/user handlers to associate data with users.
    Read your session cookie/JWT and return the user identity.

    For SSO mode, you typically store the timebackId after successful SSO:
        get_user=lambda req: get_session(req)  # returns { id, email }
    """
    on_callback_success: OnCallbackSuccessFn
    """
    Called after successful OIDC authentication and Timeback user resolution (required).

    The user field contains the enriched TimebackAuthUser with:
    - id: Timeback user ID (canonical stable identifier)
    - email, name: User profile data
    - claims: Raw IdP claims (sub, firstName, lastName, pictureUrl)

    Raw IdP data (tokens, userInfo) is available under idp.
    """

    # Optional fields (have defaults)
    mode: Literal["sso"] = "sso"
    issuer: str | None = None
    """Custom OIDC issuer URL. Override the default Timeback IdP URL."""
    redirect_uri: str | None = None
    """Custom OAuth redirect URI."""
    on_callback_error: OnCallbackErrorFn | None = None
    """Called when OIDC authentication fails."""
    build_state: BuildStateFn | None = None
    """Build custom state to pass through the OIDC flow."""


@dataclass
class CustomIdentityConfig:
    """
    Custom identity configuration (bring your own auth).

    Use when you have your own auth system (Clerk, Auth0, etc.).

    Required fields:
    - get_email: Callback to get current user's email from request
    """

    # Required field (no default) - must come first
    get_email: GetEmailFn
    """
    Get the current user's email from the request (required).

    Read your session cookie/JWT and return the user's email, or None if
    not authenticated. The SDK resolves the Timeback user by email.
    """

    # Optional field
    mode: Literal["custom"] = "custom"


IdentityConfig = SsoIdentityConfig | CustomIdentityConfig


# ─────────────────────────────────────────────────────────────────────────────
# Activity Handler Types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ActivityUserInfo:
    """User identity info needed for activity submission."""

    email: str
    """User's email address."""
    timeback_id: str | None = None
    """Timeback ID if already resolved (SSO mode). When present, skip lookup."""


@dataclass
class ValidatedActivityPayload:
    """Validated activity payload ready for submission.

    All fields are guaranteed present and type-checked after validation.
    """

    id: str
    """Activity slug/identifier."""
    name: str
    """Human-readable activity name."""
    course: Any
    """Course selector (SubjectGradeCourseRef or CourseCodeRef)."""
    started_at: str
    """ISO 8601 timestamp when activity started."""
    ended_at: str
    """ISO 8601 timestamp when activity ended."""
    elapsed_ms: int
    """Active time in milliseconds."""
    paused_ms: int
    """Paused/inactive time in milliseconds."""
    metrics: dict[str, Any]
    """Activity metrics (totalQuestions, correctQuestions, xpEarned, masteredUnits)."""


@dataclass
class ValidationSuccess:
    """Successful validation result."""

    ok: Literal[True]
    """Discriminant — always True for success."""
    payload: ValidatedActivityPayload
    """Validated payload ready for submission."""
    course: dict[str, Any]
    """Matched course config from timeback.config.json."""
    sensor: str
    """Resolved sensor URL for Caliper events."""


@dataclass
class ValidationError:
    """Failed validation result."""

    ok: Literal[False]
    """Discriminant — always False for errors."""
    response: Response
    """HTTP error response to return to client."""


# ─────────────────────────────────────────────────────────────────────────────
# Activity Hooks Types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ActivityBeforeSendData:
    """
    Data provided to `hooks.before_activity_send`.

    This is the payload the client POSTed plus the Caliper events the SDK built.
    Returning `None` from the hook skips sending.
    """

    sensor: str
    """Sensor URL selected for the event submission."""
    actor: dict[str, Any]
    """Actor object used in generated Caliper events (id, type, email)."""
    object: Any
    """Caliper context object."""
    events: tuple[Any, Any]
    """Built events (ActivityEvent, TimeSpentEvent)."""
    payload: dict[str, Any]
    """Original payload posted by the client."""
    course: dict[str, Any]
    """Matched course from `timeback.config.json`."""
    app_name: str
    """App name (from config)."""
    api_env: str
    """API environment used for resolution."""
    email: str
    """User email."""
    timeback_id: str
    """Canonical Timeback user id."""


BeforeActivitySendFn = (
    Callable[[ActivityBeforeSendData], ActivityBeforeSendData | None]
    | Callable[[ActivityBeforeSendData], Awaitable[ActivityBeforeSendData | None]]
)
"""
Called after Caliper events are built, right before sending.

- Return the (optionally modified) data to proceed with sending
- Return `None` to skip sending (handler still returns success)
- Throw to fail the request
"""


@dataclass
class TimebackHooks:
    """
    Optional hooks for customizing SDK handler behavior.

    These are primarily useful for testing, demos, and advanced integrations.
    """

    before_activity_send: BeforeActivitySendFn | None = None
    """
    Called after Caliper events are built, right before sending.

    - Return the (optionally modified) data to proceed with sending
    - Return `None` to skip sending (handler still returns success)
    - Throw to fail the request
    """


# ─────────────────────────────────────────────────────────────────────────────
# Activity Handler Dependencies (for testing)
# ─────────────────────────────────────────────────────────────────────────────


class ComputeProgressFn(Protocol):
    """Protocol for compute_progress dependency."""

    async def __call__(
        self,
        *,
        client: TimebackClient,
        course_id: str,
        timeback_id: str,
        payload: dict[str, Any],
        course_config: dict[str, Any],
        env: Environment,
    ) -> int | None: ...


class MaybeWriteCompletionEntryFn(Protocol):
    """Protocol for maybe_write_completion_entry dependency."""

    async def __call__(
        self,
        *,
        client: TimebackClient,
        course_id: str,
        timeback_id: str,
        pct_complete: int | None,
        app_name: str,
    ) -> None: ...


@dataclass
class ActivityHandlerDeps:
    """
    Internal dependencies for activity handler.

    This interface enables unit tests to inject mock implementations of
    compute_progress and maybe_write_completion_entry without mocking the
    entire TimebackClient.

    Not part of the public API — only exposed for testing purposes.
    """

    compute_progress: ComputeProgressFn
    """Compute pctComplete from EduBridge enrollment analytics."""
    maybe_write_completion_entry: MaybeWriteCompletionEntryFn
    """Write mastery completion entry when pctComplete reaches 100."""


@dataclass
class TimebackConfig:
    """Full SDK configuration.

    All fields are required except config_path and hooks. This prevents runtime errors
    in /activity and /user/me handlers.

    Required fields:
    - env: Environment (local, staging, production)
    - api: API credentials for Timeback API
    - identity: Identity configuration (SSO or custom mode)
    """

    env: Environment
    api: ApiCredentials
    identity: IdentityConfig
    config_path: str | None = None  # Path to timeback.config.json
    hooks: TimebackHooks | None = None  # Optional hooks for customizing behavior


# ─────────────────────────────────────────────────────────────────────────────
# Identity-Only Types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class IdentityOnlyCallbackSuccessContext:
    """
    Context passed to on_callback_success hook for identity-only SDK.

    When using create_identity_only_server(), the user field contains raw OIDC
    user info claims (no Timeback profile enrichment). This mode does not require
    Timeback API credentials and does not resolve users against the Timeback API.
    """

    tokens: OIDCTokens
    """OIDC tokens from the identity provider."""
    user: OIDCUserInfo
    """User info claims from the identity provider."""
    state: Any
    """State data from build_state (if provided)."""
    request: Request
    """The incoming callback request."""

    def redirect(self, url: str, headers: dict[str, str] | None = None) -> Response:
        """Create a redirect response."""
        response = RedirectResponse(url=url, status_code=302)
        if headers:
            for key, value in headers.items():
                response.headers[key] = value
        return response

    def json(self, data: Any, status: int = 200) -> Response:
        """Create a JSON response."""
        return JSONResponse(content=data, status_code=status)


# Type alias for identity-only callback
OnIdentityOnlyCallbackSuccessFn = Callable[
    [IdentityOnlyCallbackSuccessContext], Response | Awaitable[Response]
]


@dataclass
class IdentityOnlySsoConfig:
    """
    SSO identity configuration for identity-only SDK.

    When using create_identity_only_server(), the callback provides raw OIDC
    tokens and user info without Timeback profile resolution. This is useful
    for SSO-only deployments that don't need activity tracking.

    Required fields:
    - client_id, client_secret: OIDC credentials
    - on_callback_success: Callback after successful SSO
    """

    # Required fields (no defaults) - must come first
    client_id: str
    """OIDC client ID (required)."""
    client_secret: str
    """OIDC client secret (required)."""
    on_callback_success: OnIdentityOnlyCallbackSuccessFn
    """
    Called after successful OIDC authentication (required).

    The user field contains raw OIDC claims (no Timeback resolution):
    - sub: IdP subject identifier
    - email, name: User profile data from IdP
    - Other OIDC claims as returned by the IdP

    Tokens (access_token, id_token, refresh_token) are available under tokens.
    """

    # Optional fields
    mode: Literal["sso"] = "sso"
    issuer: str | None = None
    """Custom OIDC issuer URL. Override the default Timeback IdP URL."""
    redirect_uri: str | None = None
    """Custom OAuth redirect URI."""
    get_user: GetUserFn | None = None
    """Get the current user from the request (for downstream handlers, not used by identity-only)."""
    on_callback_error: OnCallbackErrorFn | None = None
    """Called when OIDC authentication fails."""
    build_state: BuildStateFn | None = None
    """Build custom state to pass through the OIDC flow."""


@dataclass
class IdentityOnlyConfig:
    """
    Identity-only SDK configuration.

    Use this when you only need SSO authentication without activity tracking
    or Timeback API integration. Does not require timeback.config.json or API credentials.

    Required fields:
    - env: Environment (local, staging, production)
    - identity: SSO identity configuration
    """

    env: Environment
    identity: IdentityOnlySsoConfig
