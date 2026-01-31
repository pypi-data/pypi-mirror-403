"""Identity handlers (sign-in, callback, sign-out) with Timeback user resolution."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING

from starlette.responses import JSONResponse, RedirectResponse, Response

from ....shared.constants import get_issuer
from ...lib.logger import sso_log
from ...lib.oidc import OIDCClient
from ...lib.resolve import TimebackUserResolutionError, resolve_timeback_user_by_email
from ...types import (
    BuildStateContext,
    CallbackErrorContext,
    CallbackSuccessContext,
    CustomIdentityConfig,
    IdpData,
    SsoIdentityConfig,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request

    from ...types import ApiCredentials, Environment, IdentityConfig


@dataclass
class IdentityHandlers:
    """Identity-related handlers."""

    sign_in: Callable[[Request], Awaitable[Response]]
    callback: Callable[[Request], Awaitable[Response]]
    sign_out: Callable[[], Response]


def create_identity_handlers(
    *,
    env: Environment,
    identity: IdentityConfig,
    api: ApiCredentials | None = None,
) -> IdentityHandlers:
    """
    Create identity handlers.

    Args:
        env: Environment (local, staging, production)
        identity: Identity configuration (SSO or custom mode)
        api: API credentials for Timeback API (required for SSO mode user resolution)

    Returns:
        Identity handlers for sign-in, callback, and sign-out
    """
    if isinstance(identity, CustomIdentityConfig) or identity.mode == "custom":
        # Custom mode: SSO endpoints return errors
        async def no_sso_signin(_request: Request) -> Response:
            return JSONResponse({"error": "SSO not configured"}, status_code=400)

        async def no_sso_callback(_request: Request) -> Response:
            return JSONResponse({"error": "SSO not configured"}, status_code=400)

        def no_sso_signout() -> Response:
            return RedirectResponse(url="/", status_code=302)

        return IdentityHandlers(
            sign_in=no_sso_signin, callback=no_sso_callback, sign_out=no_sso_signout
        )

    # SSO mode
    sso_config: SsoIdentityConfig = identity
    # Use explicit issuer if provided, otherwise resolve from env (throws for 'local')
    issuer = sso_config.issuer or get_issuer(env)
    oidc = OIDCClient(
        issuer=issuer,
        client_id=sso_config.client_id,
        client_secret=sso_config.client_secret,
    )

    async def sso_signin(request: Request) -> Response:
        # Build callback URL
        callback_url = sso_config.redirect_uri
        if not callback_url:
            base = str(request.base_url).rstrip("/")
            # Derive from current path: /api/timeback/identity/signin -> /api/timeback/identity/callback
            path = str(request.url.path)
            callback_path = path.replace("/signin", "/callback")
            callback_url = f"{base}{callback_path}"

        sso_log.debug(
            "SSO sign-in initiated, env=%s, issuer=%s, client_id=%s",
            env,
            issuer,
            sso_config.client_id,
        )

        # Build state - default to {} (state always decodes to object)
        state_data: dict | None = {}
        if sso_config.build_state:
            ctx = BuildStateContext(
                request=request,
                url=str(request.url),
            )
            state_data = sso_config.build_state(ctx)

        # Generate auth URL
        auth_url = await oidc.get_authorization_url(redirect_uri=callback_url, state=state_data)
        return RedirectResponse(url=auth_url, status_code=302)

    async def sso_callback(request: Request) -> Response:
        code = request.query_params.get("code")
        state_param = request.query_params.get("state")
        error = request.query_params.get("error")

        sso_log.debug("Received callback from IdP, has_code=%s, error=%s", bool(code), error)

        # Parse state early for error context
        state = oidc.decode_state(state_param) if state_param else None

        if error:
            error_desc = request.query_params.get("error_description")
            sso_log.error("IdP returned error: %s, description=%s", error, error_desc)

            error_ctx = CallbackErrorContext(
                error=Exception(error_desc or error),
                error_code=error,
                state=state,
                request=request,
            )
            if sso_config.on_callback_error:
                result = sso_config.on_callback_error(error_ctx)
                return await result if inspect.isawaitable(result) else result
            return JSONResponse({"error": error}, status_code=400)

        if not code:
            sso_log.error("Missing authorization code in callback")
            error_ctx = CallbackErrorContext(
                error=Exception("Missing authorization code"),
                error_code="missing_code",
                state=state,
                request=request,
            )
            if sso_config.on_callback_error:
                result = sso_config.on_callback_error(error_ctx)
                return await result if inspect.isawaitable(result) else result
            return JSONResponse({"error": "Missing authorization code"}, status_code=400)

        try:
            # Build callback URL (same as signin)
            callback_url = sso_config.redirect_uri
            if not callback_url:
                base = str(request.base_url).rstrip("/")
                path = str(request.url.path)
                callback_url = f"{base}{path}"

            sso_log.debug("Exchanging auth code for tokens, issuer=%s", issuer)

            # Exchange code for tokens
            tokens = await oidc.exchange_code(code=code, redirect_uri=callback_url)
            user_info = await oidc.get_user_info(tokens["access_token"])

            sso_log.debug("SSO completed, resolving Timeback user")

            # Resolve the Timeback user via API
            if api is None:
                raise ValueError(
                    "API credentials required for SSO mode. "
                    "Pass api=ApiCredentials(...) to TimebackConfig."
                )

            auth_user = await resolve_timeback_user_by_email(
                env=env,
                api_credentials=api,
                user_info=user_info,
            )

            sso_log.debug("Timeback user resolved, timeback_id=%s", auth_user.id)

            # Build the success context with enriched user
            success_ctx = CallbackSuccessContext(
                user=auth_user,
                idp=IdpData(tokens=tokens, user_info=user_info),
                state=state,
                request=request,
            )

            if sso_config.on_callback_success:
                result = sso_config.on_callback_success(success_ctx)
                return await result if inspect.isawaitable(result) else result

            return RedirectResponse(url="/", status_code=302)

        except TimebackUserResolutionError as e:
            sso_log.error("SSO callback failed: %s, code=%s", str(e), e.code)
            error_ctx = CallbackErrorContext(
                error=e,
                error_code=e.code,
                state=state,
                request=request,
            )
            if sso_config.on_callback_error:
                result = sso_config.on_callback_error(error_ctx)
                return await result if inspect.isawaitable(result) else result
            return JSONResponse({"error": str(e)}, status_code=500)

        except Exception as e:
            sso_log.error("SSO callback failed: %s", str(e))
            error_ctx = CallbackErrorContext(
                error=e,
                error_code="token_exchange_failed",
                state=state,
                request=request,
            )
            if sso_config.on_callback_error:
                result = sso_config.on_callback_error(error_ctx)
                return await result if inspect.isawaitable(result) else result
            return JSONResponse({"error": str(e)}, status_code=500)

    def sso_signout() -> Response:
        # Just redirect; actual session clearing is app's responsibility
        return RedirectResponse(url="/", status_code=302)

    return IdentityHandlers(sign_in=sso_signin, callback=sso_callback, sign_out=sso_signout)
