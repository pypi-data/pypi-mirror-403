"""Handler factory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .activity import create_activity_handler
from .identity import IdentityHandlers, create_identity_handlers
from .user import create_user_handler, create_user_verify_handler

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

    from ..timeback import AppConfig
    from ..types import ApiCredentials, Environment, IdentityConfig, TimebackHooks


@dataclass
class UserHandlers:
    """User-related handlers."""

    me: Callable[[Request], Awaitable[Response]]
    verify: Callable[[Request], Awaitable[Response]]


@dataclass
class Handlers:
    """All SDK handlers."""

    activity: Callable[[Request], Awaitable[Response]]
    identity: IdentityHandlers
    user: UserHandlers


def create_handlers(
    *,
    env: Environment,
    api: ApiCredentials,
    identity: IdentityConfig,
    app_config: AppConfig,
    hooks: TimebackHooks | None = None,
) -> Handlers:
    """Create all SDK handlers.

    Args:
        env: Environment (local, staging, production)
        api: API credentials (required for full SDK)
        identity: Identity configuration
        app_config: App configuration from timeback.config.json
        hooks: Optional hooks for customizing behavior

    Returns:
        All SDK handlers
    """
    return Handlers(
        activity=create_activity_handler(
            env=env,
            api=api,
            identity=identity,
            app_config=app_config,
            hooks=hooks,
        ),
        identity=create_identity_handlers(
            env=env,
            identity=identity,
            api=api,
        ),
        user=UserHandlers(
            me=create_user_handler(
                env=env,
                api=api,
                identity=identity,
                app_config=app_config,
            ),
            verify=create_user_verify_handler(
                env=env,
                api=api,
                identity=identity,
            ),
        ),
    )
