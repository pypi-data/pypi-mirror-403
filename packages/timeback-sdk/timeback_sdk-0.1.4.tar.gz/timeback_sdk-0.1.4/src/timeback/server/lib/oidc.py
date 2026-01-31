"""OIDC client for SSO authentication."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import httpx

from .logger import oidc_log
from .utils import decode_base64_url, encode_base64_url

if TYPE_CHECKING:
    from ..types import OIDCTokens, OIDCUserInfo


class OIDCClient:
    """OpenID Connect client for Timeback SSO."""

    def __init__(
        self,
        *,
        issuer: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._issuer = issuer.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._config: dict[str, Any] | None = None
        self._http = httpx.AsyncClient(timeout=30.0)

    async def _get_config(self) -> dict[str, Any]:
        """Fetch OIDC discovery document."""
        if self._config is None:
            url = f"{self._issuer}/.well-known/openid-configuration"
            oidc_log.debug("Fetching OIDC discovery document from %s", url)
            response = await self._http.get(url)
            response.raise_for_status()
            config: dict[str, Any] = response.json()
            self._config = config
        return self._config

    async def get_authorization_url(
        self,
        *,
        redirect_uri: str,
        state: Any = None,
        scope: str = "openid email profile",
    ) -> str:
        """Build authorization URL for sign-in redirect.

        Note: state is always base64url-encoded JSON. If state is None, defaults
        to empty dict {} so callback always decodes to an object (never None).
        """
        config = await self._get_config()
        auth_endpoint = config["authorization_endpoint"]

        # Always encode state as base64url JSON.
        # Default to {} if not provided, so callback state decodes to {} not None.
        state_data = state if state is not None else {}
        state_param = encode_base64_url(state_data)

        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "scope": scope,
            "redirect_uri": redirect_uri,
            "state": state_param,
        }

        return f"{auth_endpoint}?{urlencode(params)}"

    async def exchange_code(
        self,
        *,
        code: str,
        redirect_uri: str,
    ) -> OIDCTokens:
        """Exchange authorization code for tokens."""
        config = await self._get_config()
        token_endpoint = config["token_endpoint"]

        response = await self._http.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_user_info(self, access_token: str) -> OIDCUserInfo:
        """Fetch user info from userinfo endpoint."""
        config = await self._get_config()
        userinfo_endpoint = config["userinfo_endpoint"]

        response = await self._http.get(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()

    def decode_state(self, state: str) -> Any:
        """Decode state from URL-safe base64 JSON.

        Returns decoded object, or None if decoding fails.
        """
        try:
            return decode_base64_url(state)
        except Exception:
            oidc_log.warning("Failed to decode state")
            return None

    async def close(self) -> None:
        """Close HTTP client."""
        await self._http.aclose()
