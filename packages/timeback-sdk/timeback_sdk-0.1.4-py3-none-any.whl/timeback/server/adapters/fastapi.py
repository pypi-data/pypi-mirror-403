"""
FastAPI Adapter

Adapts Timeback handlers for FastAPI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload

from fastapi import APIRouter, Request

if TYPE_CHECKING:
    from starlette.responses import Response

    from ..handlers.factory import Handlers
    from ..timeback import IdentityOnlyInstance, TimebackInstance


# Type for flexible input (full or identity-only instance)
AnyTimebackInstance = "TimebackInstance | IdentityOnlyInstance"


@overload
def to_fastapi_router(
    timeback: TimebackInstance,
    *,
    callback_path: str | None = None,
) -> APIRouter: ...


@overload
def to_fastapi_router(
    timeback: IdentityOnlyInstance,
    *,
    callback_path: str | None = None,
) -> APIRouter: ...


def to_fastapi_router(
    timeback: TimebackInstance | IdentityOnlyInstance,
    *,
    callback_path: str | None = None,
) -> APIRouter:
    """
    Convert Timeback instance to FastAPI router.

    Supports both full SDK instances (from create_server()) and identity-only
    instances (from create_identity_only_server()).

    Args:
        timeback: Timeback instance (full or identity-only)
        callback_path: Custom callback path for OAuth redirects. If your IdP has
            a pre-registered callback URL that differs from the SDK default
            (/identity/callback), specify the path here. The path should be
            relative to the router mount point (e.g., "/auth/callback").

    Returns:
        FastAPI APIRouter with Timeback endpoints

    Example (Full SDK):
        ```python
        from timeback.server import create_server, TimebackConfig, SsoIdentityConfig
        from timeback.server.adapters.fastapi import to_fastapi_router

        timeback = await create_server(TimebackConfig(
            env="staging",
            api=ApiCredentials(client_id="...", client_secret="..."),
            identity=SsoIdentityConfig(
                mode="sso",
                client_id="...",
                client_secret="...",
                get_user=get_session_user,
                on_callback_success=lambda ctx: ctx.redirect("/"),
            ),
        ))

        app = FastAPI()
        app.include_router(to_fastapi_router(timeback), prefix="/api/timeback")
        ```

    Example (Identity-Only):
        ```python
        from timeback.server import (
            create_identity_only_server,
            IdentityOnlyConfig,
            IdentityOnlySsoConfig,
        )
        from timeback.server.adapters.fastapi import to_fastapi_router

        timeback = create_identity_only_server(IdentityOnlyConfig(
            env="staging",
            identity=IdentityOnlySsoConfig(
                mode="sso",
                client_id="...",
                client_secret="...",
                on_callback_success=lambda ctx: ctx.redirect("/dashboard"),
            ),
        ))

        app = FastAPI()
        app.include_router(to_fastapi_router(timeback), prefix="/api/auth")
        ```

    Example (Custom Callback Path):
        ```python
        # When your IdP requires a specific callback URL like:
        # https://example.com/api/auth/sso/callback/timeback

        timeback = create_identity_only_server(IdentityOnlyConfig(
            env="staging",
            identity=IdentityOnlySsoConfig(
                mode="sso",
                client_id="...",
                client_secret="...",
                redirect_uri="https://example.com/api/auth/sso/callback/timeback",
                on_callback_success=lambda ctx: ctx.redirect("/dashboard"),
            ),
        ))

        app = FastAPI()
        app.include_router(
            to_fastapi_router(timeback, callback_path="/sso/callback/timeback"),
            prefix="/api/auth",
        )
        ```
    """
    router = APIRouter()
    handle = timeback.handle

    # Determine if this is a full instance or identity-only
    is_full_instance = hasattr(handle, "activity") and hasattr(handle, "user")

    # Register identity routes
    @router.get("/identity/signin")
    async def identity_signin(request: Request) -> Response:
        return await handle.identity.sign_in(request)

    # Default callback path
    @router.get("/identity/callback")
    async def identity_callback(request: Request) -> Response:
        return await handle.identity.callback(request)

    # Custom callback path (if provided and different from default)
    if callback_path and callback_path != "/identity/callback":
        # Normalize path to ensure it starts with /
        normalized_path = callback_path if callback_path.startswith("/") else f"/{callback_path}"

        @router.get(normalized_path)
        async def identity_callback_custom(request: Request) -> Response:
            return await handle.identity.callback(request)

    @router.get("/identity/signout")
    async def identity_signout(_request: Request) -> Response:
        return handle.identity.sign_out()

    # Register full SDK routes only for full instances
    if is_full_instance:
        # Cast to Handlers since we've confirmed it has activity and user
        full_handle = cast("Handlers", handle)

        @router.post("/activity", response_model=None)
        async def submit_activity(request: Request) -> Response:
            return await full_handle.activity(request)

        @router.get("/user/me")
        async def user_me(request: Request) -> Response:
            return await full_handle.user.me(request)

        @router.get("/user/verify")
        async def user_verify(request: Request) -> Response:
            return await full_handle.user.verify(request)

    return router
