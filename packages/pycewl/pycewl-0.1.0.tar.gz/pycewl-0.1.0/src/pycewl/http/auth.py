"""HTTP authentication support for pycewl."""

from __future__ import annotations

import httpx

from pycewl.config import AuthConfig, AuthType


def create_auth(config: AuthConfig) -> httpx.Auth | None:
    """Create an httpx Auth object for Basic/Digest authentication.

    Args:
        config: Authentication configuration.

    Returns:
        An httpx Auth object, or None if no auth or using bearer tokens.

    Raises:
        ValueError: If auth type requires credentials but none provided.
    """
    if config.auth_type in (AuthType.NONE, AuthType.BEARER):
        return None

    if not config.username or not config.password:
        raise ValueError(
            f"Authentication type {config.auth_type.value} requires username and password"
        )

    if config.auth_type == AuthType.BASIC:
        return httpx.BasicAuth(username=config.username, password=config.password)

    if config.auth_type == AuthType.DIGEST:
        return httpx.DigestAuth(username=config.username, password=config.password)

    return None


def create_auth_headers(config: AuthConfig) -> dict[str, str]:
    """Create authentication headers for token-based auth.

    For Bearer/JWT tokens, the token is sent as an Authorization header.

    Args:
        config: Authentication configuration.

    Returns:
        Dictionary of auth headers (empty if not using token auth).

    Raises:
        ValueError: If bearer auth is selected but no token provided.
    """
    if config.auth_type != AuthType.BEARER:
        return {}

    if not config.token:
        raise ValueError("Authentication type bearer requires a token (--auth-token)")

    return {"Authorization": f"Bearer {config.token}"}
