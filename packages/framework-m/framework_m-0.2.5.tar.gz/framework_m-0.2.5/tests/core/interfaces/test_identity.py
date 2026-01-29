"""Tests for IdentityProtocol interface.

TDD: This test file is created BEFORE the implementation.

Tests cover:
- Token and Credentials model validation
- IdentityProtocol interface definition
- Structural typing verification (duck typing)
"""

from typing import Any

import pytest
from pydantic import ValidationError


class TestTokenModel:
    """Tests for Token model."""

    def test_import_token(self) -> None:
        """Token should be importable."""
        from framework_m.core.interfaces.identity import Token

        assert Token is not None

    def test_token_minimal(self) -> None:
        """Token with only required fields."""
        from framework_m.core.interfaces.identity import Token

        token = Token(access_token="abc123")
        assert token.access_token == "abc123"
        assert token.token_type == "Bearer"
        assert token.expires_in is None
        assert token.refresh_token is None

    def test_token_full(self) -> None:
        """Token with all fields."""
        from framework_m.core.interfaces.identity import Token

        token = Token(
            access_token="abc123",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="refresh456",
        )
        assert token.access_token == "abc123"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert token.refresh_token == "refresh456"

    def test_token_requires_access_token(self) -> None:
        """Token must have access_token."""
        from framework_m.core.interfaces.identity import Token

        with pytest.raises(ValidationError):
            Token()  # type: ignore[call-arg]


class TestCredentialsModel:
    """Tests for Credentials models."""

    def test_import_credentials(self) -> None:
        """Credentials should be importable."""
        from framework_m.core.interfaces.identity import Credentials

        assert Credentials is not None

    def test_import_password_credentials(self) -> None:
        """PasswordCredentials should be importable."""
        from framework_m.core.interfaces.identity import PasswordCredentials

        assert PasswordCredentials is not None

    def test_password_credentials_validation(self) -> None:
        """PasswordCredentials requires username and password."""
        from framework_m.core.interfaces.identity import PasswordCredentials

        creds = PasswordCredentials(username="user@example.com", password="secret123")
        assert creds.username == "user@example.com"
        assert creds.password == "secret123"

    def test_password_credentials_missing_fields(self) -> None:
        """PasswordCredentials must have both fields."""
        from framework_m.core.interfaces.identity import PasswordCredentials

        with pytest.raises(ValidationError):
            PasswordCredentials(username="user@example.com")  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            PasswordCredentials(password="secret123")  # type: ignore[call-arg]

    def test_password_credentials_is_credentials(self) -> None:
        """PasswordCredentials is subclass of Credentials."""
        from framework_m.core.interfaces.identity import (
            Credentials,
            PasswordCredentials,
        )

        assert issubclass(PasswordCredentials, Credentials)


class TestIdentityProtocol:
    """Tests for IdentityProtocol interface definition."""

    def test_import_identity_protocol(self) -> None:
        """IdentityProtocol should be importable."""
        from framework_m.core.interfaces.identity import IdentityProtocol

        assert IdentityProtocol is not None

    def test_identity_protocol_is_protocol(self) -> None:
        """IdentityProtocol should be a Protocol class."""
        from framework_m.core.interfaces.identity import IdentityProtocol

        # Protocols have _is_protocol attribute
        assert hasattr(IdentityProtocol, "_is_protocol")

    def test_identity_protocol_has_get_user(self) -> None:
        """IdentityProtocol should define get_user method."""
        from framework_m.core.interfaces.identity import IdentityProtocol

        assert hasattr(IdentityProtocol, "get_user")

    def test_identity_protocol_has_get_user_by_email(self) -> None:
        """IdentityProtocol should define get_user_by_email method."""
        from framework_m.core.interfaces.identity import IdentityProtocol

        assert hasattr(IdentityProtocol, "get_user_by_email")

    def test_identity_protocol_has_authenticate(self) -> None:
        """IdentityProtocol should define authenticate method."""
        from framework_m.core.interfaces.identity import IdentityProtocol

        assert hasattr(IdentityProtocol, "authenticate")

    def test_identity_protocol_has_get_attributes(self) -> None:
        """IdentityProtocol should define get_attributes method."""
        from framework_m.core.interfaces.identity import IdentityProtocol

        assert hasattr(IdentityProtocol, "get_attributes")

    def test_identity_protocol_has_validate_token(self) -> None:
        """IdentityProtocol should define validate_token method."""
        from framework_m.core.interfaces.identity import IdentityProtocol

        assert hasattr(IdentityProtocol, "validate_token")

    def test_identity_protocol_exports(self) -> None:
        """IdentityProtocol should be in __all__."""
        from framework_m.core.interfaces import identity

        assert "IdentityProtocol" in identity.__all__
        assert "Token" in identity.__all__
        assert "Credentials" in identity.__all__
        assert "PasswordCredentials" in identity.__all__


class TestIdentityProtocolImplementation:
    """Tests for implementing IdentityProtocol."""

    def test_can_implement_protocol(self) -> None:
        """A class implementing all methods should satisfy IdentityProtocol."""
        from framework_m.core.interfaces.auth_context import UserContext
        from framework_m.core.interfaces.identity import (
            Credentials,
            IdentityProtocol,
            Token,
        )

        class MockIdentityProvider:
            """Mock implementation for testing structural typing."""

            async def get_user(self, user_id: str) -> UserContext | None:
                return None

            async def get_user_by_email(self, email: str) -> UserContext | None:
                return None

            async def authenticate(self, credentials: Credentials) -> Token:
                return Token(access_token="mock_token")

            async def get_attributes(self, user_id: str) -> dict[str, Any]:
                return {}

            async def validate_token(self, token: str) -> UserContext | None:
                return None

        # Should be valid implementation (duck typing)
        provider: IdentityProtocol = MockIdentityProvider()
        assert provider is not None


class TestInterfacesExports:
    """Tests for exports from interfaces __init__.py."""

    def test_identity_protocol_exported_from_interfaces(self) -> None:
        """IdentityProtocol should be importable from interfaces package."""
        from framework_m.core.interfaces import IdentityProtocol

        assert IdentityProtocol is not None

    def test_token_exported_from_interfaces(self) -> None:
        """Token should be importable from interfaces package."""
        from framework_m.core.interfaces import Token

        assert Token is not None

    def test_credentials_exported_from_interfaces(self) -> None:
        """Credentials should be importable from interfaces package."""
        from framework_m.core.interfaces import Credentials

        assert Credentials is not None

    def test_password_credentials_exported_from_interfaces(self) -> None:
        """PasswordCredentials should be importable from interfaces package."""
        from framework_m.core.interfaces import PasswordCredentials

        assert PasswordCredentials is not None
