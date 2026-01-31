"""User verification handler.

Lightweight endpoint to check whether the current user can be resolved in Timeback.

This is intentionally cheaper than `/user/me`:
- In custom identity mode, it resolves the Timeback user by **email**.
- In SSO mode, it expects your app session to provide a **TimebackIdentity** (including the
  *Timeback* user id) via `getUser()`. Note: the IdP's `sub` from Cognito/OIDC userinfo is
  *not* the Timeback user id — we only get the Timeback id after resolving via the Timeback API
  in the SSO callback (`onCallbackSuccess`).
- It does NOT fetch enrollments/analytics or build an enriched profile
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from starlette.responses import JSONResponse, Response

from timeback_core import TimebackClient

from ...lib.logger import create_scoped_logger
from ...lib.resolve import TimebackUserResolutionError, resolve_timeback_user_by_email
from ...lib.utils import map_env_for_api
from ...types import CustomIdentityConfig

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request

    from ...types import ApiCredentials, Environment, IdentityConfig

log = create_scoped_logger("handlers:user:verify")


def create_user_verify_handler(
    *,
    env: Environment,
    api: ApiCredentials,
    identity: IdentityConfig,
) -> Callable[[Request], Awaitable[Response]]:
    """Create a lightweight user verification handler.

    Returns:
        200 with `{ "verified": true, "timebackId": "..." }` if the user can be resolved.
        200 with `{ "verified": false }` if the user does not exist in Timeback
        409 if ambiguous
        401 if the request is not authenticated / missing email (custom mode)
    """
    api_env = map_env_for_api(env)

    async def handler(request: Request) -> Response:
        user_email: str | None = None
        timeback_id: str | None = None

        if isinstance(identity, CustomIdentityConfig) or identity.mode == "custom":
            get_email = identity.get_email
            if not get_email:
                return JSONResponse(
                    {"verified": False, "error": "No getEmail configured"}, status_code=500
                )

            result = get_email(request)
            user_email = await result if inspect.isawaitable(result) else result

            if not user_email:
                return JSONResponse({"verified": False, "error": "Unauthorized"}, status_code=401)
        else:
            get_user = identity.get_user
            if not get_user:
                return JSONResponse(
                    {"verified": False, "error": "No getUser configured"}, status_code=500
                )

            result = get_user(request)
            user = await result if inspect.isawaitable(result) else result

            if not user:
                return JSONResponse({"verified": False, "error": "Unauthorized"}, status_code=401)

            # In SSO mode, `getUser()` should return the *Timeback* identity you stored
            # during the SSO callback (onCallbackSuccess). This is not the IdP `sub`.
            timeback_id = user.id
            user_email = user.email

        client = TimebackClient(
            env=api_env,
            client_id=api.client_id,
            client_secret=api.client_secret,
        )

        try:
            # Resolve timeback user
            if not timeback_id:
                if not user_email:
                    return JSONResponse(
                        {"verified": False, "error": "No user email"}, status_code=401
                    )
                resolved = await resolve_timeback_user_by_email(
                    env=env,
                    api_credentials=api,
                    user_info={"sub": user_email, "email": user_email},
                    client=client,
                )
            else:
                resolved = await resolve_timeback_user_by_email(
                    env=env,
                    api_credentials=api,
                    user_info={"sub": timeback_id, "email": user_email or ""},
                    client=client,
                )

            return JSONResponse({"verified": True, "timebackId": resolved.id})
        except TimebackUserResolutionError as e:
            log.warning("Timeback user resolution failed: %s", e.code)
            if e.code == "timeback_user_ambiguous":
                return JSONResponse(
                    {"verified": False, "error": "Timeback user resolution ambiguous"},
                    status_code=409,
                )
            if e.code == "timeback_user_not_found":
                # "Not a Timeback user" is a valid outcome for gating flows; return 200
                # so clients can treat it as a normal boolean check.
                return JSONResponse({"verified": False})
            # Other resolution errors (missing_email, lookup_failed) → 502 to match other handlers
            return JSONResponse({"verified": False, "error": str(e)}, status_code=502)
        except Exception as e:
            log.error("Unhandled error in verify handler: %s", str(e))
            return JSONResponse({"verified": False, "error": str(e)}, status_code=500)
        finally:
            await client.close()

    return handler
