"""
SDK Logger

Debug logging for the Timeback SDK server components.
Only logs when DEBUG=1 or DEBUG=true is set.
"""

from __future__ import annotations

import logging
import os

_configured = False


def _is_debug() -> bool:
    """Check if debug mode is enabled via DEBUG environment variable."""
    debug = os.environ.get("DEBUG", "")
    return debug in ("1", "true", "True")


def _configure_once() -> None:
    """Configure logging format once."""
    global _configured
    if _configured:
        return
    _configured = True

    level = logging.DEBUG if _is_debug() else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def create_scoped_logger(scope: str) -> logging.Logger:
    """
    Create a scoped logger for SDK components.

    Only logs debug/info when DEBUG=1 or DEBUG=true.

    Args:
        scope: Logger scope name (e.g., 'sso', 'oidc')

    Returns:
        Configured logger instance
    """
    _configure_once()
    logger = logging.getLogger(f"timeback:{scope}")
    logger.setLevel(logging.DEBUG if _is_debug() else logging.WARNING)
    return logger


# Logger for SSO/identity operations
sso_log = create_scoped_logger("sso")

# Logger for OIDC protocol operations
oidc_log = create_scoped_logger("oidc")
