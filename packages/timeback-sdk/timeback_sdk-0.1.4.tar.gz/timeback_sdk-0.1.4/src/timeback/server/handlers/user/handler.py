"""User profile handler."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from starlette.responses import JSONResponse, Response

from timeback_core import TimebackClient

from ...lib.logger import create_scoped_logger
from ...lib.resolve import (
    TimebackUserResolutionError,
    resolve_timeback_user_by_email,
)
from ...lib.utils import map_env_for_api
from ...types import CustomIdentityConfig
from .profile import build_user_profile, profile_to_dict

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request

    from ...timeback import AppConfig
    from ...types import ApiCredentials, Environment, IdentityConfig

log = create_scoped_logger("handlers:user")


def create_user_handler(
    *,
    env: Environment,
    api: ApiCredentials,
    identity: IdentityConfig,
    app_config: AppConfig,
) -> Callable[[Request], Awaitable[Response]]:
    """
    Create the user profile handler.

    Returns the current user's profile, including identity and enriched data
    from the Timeback API.

    Args:
        env: Environment (local, staging, production)
        api: API credentials for Timeback API (required)
        identity: Identity configuration
        app_config: App configuration from timeback.config.json

    Returns:
        The user profile request handler
    """
    api_env = map_env_for_api(env)

    async def handler(request: Request) -> Response:
        try:
            # Get user identity based on identity mode
            user_email: str | None = None
            timeback_id: str | None = None

            if isinstance(identity, CustomIdentityConfig) or identity.mode == "custom":
                # Custom mode: get email and resolve user
                get_email = identity.get_email
                if not get_email:
                    return JSONResponse({"error": "No getEmail configured"}, status_code=500)

                result = get_email(request)
                user_email = await result if inspect.isawaitable(result) else result

                if not user_email:
                    return JSONResponse({"error": "Unauthorized"}, status_code=401)

            else:
                # SSO mode: get user from session (should have timebackId)
                # Note: identity must be SsoIdentityConfig here since IdentityConfig is a union
                get_user = identity.get_user
                if not get_user:
                    return JSONResponse({"error": "No getUser configured"}, status_code=500)

                result = get_user(request)
                user = await result if inspect.isawaitable(result) else result

                if not user:
                    return JSONResponse({"error": "Unauthorized"}, status_code=401)

                timeback_id = user.id
                user_email = user.email

            # Create Timeback client
            client = TimebackClient(
                env=api_env,
                client_id=api.client_id,
                client_secret=api.client_secret,
            )

            try:
                # Resolve timeback user if not already known
                if not timeback_id:
                    if not user_email:
                        return JSONResponse({"error": "No user email"}, status_code=401)

                    resolved = await resolve_timeback_user_by_email(
                        env=env,
                        api_credentials=api,
                        user_info={"sub": user_email, "email": user_email},
                        client=client,
                    )
                    profile_base = resolved
                else:
                    # We have timeback_id, but need to fetch full profile
                    resolved = await resolve_timeback_user_by_email(
                        env=env,
                        api_credentials=api,
                        user_info={"sub": timeback_id, "email": user_email or ""},
                        client=client,
                    )
                    profile_base = resolved

                # Build the enriched user profile
                profile = await build_user_profile(
                    client=client,
                    user=profile_base,
                    app_config=app_config,
                    api_env=api_env,
                )

                # Convert to dict for JSON response
                profile_dict = profile_to_dict(profile)
                return JSONResponse(profile_dict)

            except TimebackUserResolutionError as e:
                log.warning("Timeback user resolution failed: %s", e.code)
                # Map error code to appropriate HTTP status and message
                if e.code == "timeback_user_ambiguous":
                    return JSONResponse(
                        {"error": "Timeback user resolution ambiguous"},
                        status_code=409,
                    )
                if e.code == "timeback_user_not_found":
                    return JSONResponse(
                        {"error": "Timeback user not found"},
                        status_code=404,
                    )
                # Other resolution errors (missing_email, lookup_failed) → 502 to match TS
                log.error("Failed to build user profile: %s", str(e))
                return JSONResponse(
                    {"error": str(e)},
                    status_code=502,
                )

            finally:
                await client.close()

        except Exception as e:
            log.error("Unhandled error in user handler: %s", str(e))
            return JSONResponse({"error": str(e)}, status_code=500)

    return handler
