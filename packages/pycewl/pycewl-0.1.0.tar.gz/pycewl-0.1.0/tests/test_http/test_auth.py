"""Tests for HTTP authentication."""

from __future__ import annotations

import httpx
import pytest

from pycewl.config import AuthConfig, AuthType
from pycewl.http.auth import create_auth, create_auth_headers


class TestCreateAuth:
    """Tests for create_auth function."""

    def test_no_auth(self) -> None:
        """Test that no auth returns None."""
        config = AuthConfig(auth_type=AuthType.NONE)
        auth = create_auth(config)

        assert auth is None

    def test_basic_auth(self) -> None:
        """Test basic auth creation."""
        config = AuthConfig(
            auth_type=AuthType.BASIC,
            username="user",
            password="pass",
        )
        auth = create_auth(config)

        assert isinstance(auth, httpx.BasicAuth)

    def test_digest_auth(self) -> None:
        """Test digest auth creation."""
        config = AuthConfig(
            auth_type=AuthType.DIGEST,
            username="user",
            password="pass",
        )
        auth = create_auth(config)

        assert isinstance(auth, httpx.DigestAuth)

    def test_basic_auth_missing_credentials(self) -> None:
        """Test basic auth raises error without credentials."""
        config = AuthConfig(auth_type=AuthType.BASIC)

        with pytest.raises(ValueError, match="requires username and password"):
            create_auth(config)

    def test_digest_auth_missing_username(self) -> None:
        """Test digest auth raises error without username."""
        config = AuthConfig(
            auth_type=AuthType.DIGEST,
            password="pass",
        )

        with pytest.raises(ValueError, match="requires username and password"):
            create_auth(config)

    def test_digest_auth_missing_password(self) -> None:
        """Test digest auth raises error without password."""
        config = AuthConfig(
            auth_type=AuthType.DIGEST,
            username="user",
        )

        with pytest.raises(ValueError, match="requires username and password"):
            create_auth(config)

    def test_bearer_returns_none(self) -> None:
        """Test that bearer auth returns None (handled via headers instead)."""
        config = AuthConfig(
            auth_type=AuthType.BEARER,
            token="my-jwt-token",
        )
        auth = create_auth(config)

        assert auth is None


class TestCreateAuthHeaders:
    """Tests for create_auth_headers function."""

    def test_no_auth_returns_empty(self) -> None:
        """Test that non-bearer auth returns empty headers."""
        config = AuthConfig(auth_type=AuthType.NONE)
        headers = create_auth_headers(config)

        assert headers == {}

    def test_basic_auth_returns_empty(self) -> None:
        """Test that basic auth returns empty headers (handled by httpx)."""
        config = AuthConfig(
            auth_type=AuthType.BASIC,
            username="user",
            password="pass",
        )
        headers = create_auth_headers(config)

        assert headers == {}

    def test_bearer_token(self) -> None:
        """Test bearer token creates Authorization header."""
        config = AuthConfig(
            auth_type=AuthType.BEARER,
            token="my-secret-token",
        )
        headers = create_auth_headers(config)

        assert headers == {"Authorization": "Bearer my-secret-token"}

    def test_bearer_jwt_token(self) -> None:
        """Test JWT token creates correct Authorization header."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc"
        config = AuthConfig(
            auth_type=AuthType.BEARER,
            token=jwt,
        )
        headers = create_auth_headers(config)

        assert headers == {"Authorization": f"Bearer {jwt}"}

    def test_bearer_missing_token(self) -> None:
        """Test bearer auth raises error without token."""
        config = AuthConfig(auth_type=AuthType.BEARER)

        with pytest.raises(ValueError, match="requires a token"):
            create_auth_headers(config)
