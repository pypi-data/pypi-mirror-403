"""Shared constants."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Environment

# Default base path for Timeback API routes
DEFAULT_BASE_PATH = "/api/timeback"

# API routes
ROUTES = {
    "ACTIVITY": "/activity",
    "IDENTITY": {
        "SIGNIN": "/identity/signin",
        "CALLBACK": "/identity/callback",
        "SIGNOUT": "/identity/signout",
    },
    "USER": {
        "ME": "/user/me",
    },
}

# OIDC Issuer URLs (Cognito)
ISSUER_URLS = {
    "staging": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_5EUwTP9XD",
    "production": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_3uhuoRM3R",
}


def get_issuer(env: "Environment") -> str:
    """Get the Timeback IdP issuer URL for the given environment.

    Uses AWS Cognito User Pools as the identity provider.
    Matches TS SDK behavior: throws for 'local' environment.

    Args:
        env: The environment

    Returns:
        The issuer URL

    Raises:
        ValueError: If env is 'local' (not yet supported for OIDC)
    """
    if env == "local":
        raise ValueError("Local environment is not yet supported for OIDC")
    if env == "production":
        return ISSUER_URLS["production"]
    # Default to staging for any other value
    return ISSUER_URLS["staging"]
