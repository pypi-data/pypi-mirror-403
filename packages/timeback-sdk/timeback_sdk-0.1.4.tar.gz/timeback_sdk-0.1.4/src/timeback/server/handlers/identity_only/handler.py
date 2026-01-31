"""Identity-only handlers (sign-in, callback, sign-out) without Timeback user resolution."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING

from starlette.responses import JSONResponse, RedirectResponse, Response

from ....shared.constants import get_issuer
from ...lib.logger import sso_log
from ...lib.oidc import OIDCClient
from ...types import (
    BuildStateContext,
    CallbackErrorContext,
    IdentityOnlyCallbackSuccessContext,
    IdentityOnlySsoConfig,
)
from ..identity.handler import IdentityHandlers

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request

    from ...types import Environment


@dataclass
class IdentityOnlyHandlers:
    """Identity-only handlers (no Timeback API integration)."""

    sign_in: Callable[[Request], Awaitable[Response]]
    callback: Callable[[Request], Awaitable[Response]]
    sign_out: Callable[[], Response]

    @property
    def identity(self) -> IdentityHandlers:
        """Provides consistent access pattern with full Handlers."""
        return IdentityHandlers(
            sign_in=self.sign_in,
            callback=self.callback,
            sign_out=self.sign_out,
        )


def create_identity_only_handlers(
    *,
    env: Environment,
    identity: IdentityOnlySsoConfig,
) -> IdentityOnlyHandlers:
    """
    Create identity-only handlers (no Timeback API integration).

    This mode provides SSO authentication without resolving users against the
    Timeback API. The callback returns raw OIDC tokens and user info claims.

    Use this when you only need SSO authentication and don't need activity
    tracking or Timeback user profile enrichment.

    Args:
        env: Environment (local, staging, production)
        identity: Identity-only SSO configuration

    Returns:
        Identity-only handlers for sign-in, callback, and sign-out

    Raises:
        ValueError: If identity.mode is not "sso"
    """
    if identity.mode != "sso":
        raise ValueError('Identity-only mode requires identity.mode == "sso"')

    # Use explicit issuer if provided, otherwise resolve from env (throws for 'local')
    issuer = identity.issuer or get_issuer(env)
    oidc = OIDCClient(
        issuer=issuer,
        client_id=identity.client_id,
        client_secret=identity.client_secret,
    )

    async def identity_only_signin(request: Request) -> Response:
        # Build callback URL
        callback_url = identity.redirect_uri
        if not callback_url:
            base = str(request.base_url).rstrip("/")
            # Derive from current path: /api/timeback/identity/signin -> /api/timeback/identity/callback
            path = str(request.url.path)
            callback_path = path.replace("/signin", "/callback")
            callback_url = f"{base}{callback_path}"

        sso_log.debug(
            "SSO sign-in initiated (identity-only), env=%s, issuer=%s, client_id=%s",
            env,
            issuer,
            identity.client_id,
        )

        # Build state - default to {} (state always decodes to object)
        state_data: dict | None = {}
        if identity.build_state:
            ctx = BuildStateContext(
                request=request,
                url=str(request.url),
            )
            state_data = identity.build_state(ctx)

        # Generate auth URL
        auth_url = await oidc.get_authorization_url(redirect_uri=callback_url, state=state_data)
        return RedirectResponse(url=auth_url, status_code=302)

    async def identity_only_callback(request: Request) -> Response:
        code = request.query_params.get("code")
        state_param = request.query_params.get("state")
        error = request.query_params.get("error")

        sso_log.debug(
            "Received callback from IdP (identity-only), has_code=%s, error=%s", bool(code), error
        )

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
            if identity.on_callback_error:
                result = identity.on_callback_error(error_ctx)
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
            if identity.on_callback_error:
                result = identity.on_callback_error(error_ctx)
                return await result if inspect.isawaitable(result) else result
            return JSONResponse({"error": "Missing authorization code"}, status_code=400)

        try:
            # Build callback URL (same as signin)
            callback_url = identity.redirect_uri
            if not callback_url:
                base = str(request.base_url).rstrip("/")
                path = str(request.url.path)
                callback_url = f"{base}{path}"

            sso_log.debug("Exchanging auth code for tokens (identity-only), issuer=%s", issuer)

            # Exchange code for tokens
            tokens = await oidc.exchange_code(code=code, redirect_uri=callback_url)
            user_info = await oidc.get_user_info(tokens["access_token"])

            sso_log.debug("SSO completed (identity-only), user=%s", user_info.get("email"))

            # Build the success context with raw OIDC data (no Timeback resolution)
            success_ctx = IdentityOnlyCallbackSuccessContext(
                tokens=tokens,
                user=user_info,
                state=state,
                request=request,
            )

            if identity.on_callback_success:
                result = identity.on_callback_success(success_ctx)
                return await result if inspect.isawaitable(result) else result

            return RedirectResponse(url="/", status_code=302)

        except Exception as e:
            sso_log.error("SSO callback failed (identity-only): %s", str(e))
            error_ctx = CallbackErrorContext(
                error=e,
                error_code="token_exchange_failed",
                state=state,
                request=request,
            )
            if identity.on_callback_error:
                result = identity.on_callback_error(error_ctx)
                return await result if inspect.isawaitable(result) else result
            return JSONResponse({"error": str(e)}, status_code=500)

    def identity_only_signout() -> Response:
        # Just redirect; actual session clearing is app's responsibility
        return RedirectResponse(url="/", status_code=302)

    return IdentityOnlyHandlers(
        sign_in=identity_only_signin,
        callback=identity_only_callback,
        sign_out=identity_only_signout,
    )
