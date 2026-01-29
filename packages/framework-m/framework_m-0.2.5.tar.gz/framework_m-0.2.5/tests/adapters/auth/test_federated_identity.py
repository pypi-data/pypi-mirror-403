"""Tests for FederatedIdentityAdapter.

TDD: This test file is created BEFORE the implementation.

Tests cover:
- IdentityProtocol implementation for enterprise/federated mode
- Header hydration for user context
- authenticate() raises NotImplementedError
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.identity import PasswordCredentials

# =============================================================================
# Test: FederatedIdentityAdapter Import
# =============================================================================


class TestFederatedIdentityAdapterImport:
    """Tests for FederatedIdentityAdapter import."""

    def test_import_federated_identity_adapter(self) -> None:
        """FederatedIdentityAdapter should be importable."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        assert FederatedIdentityAdapter is not None

    def test_federated_identity_adapter_in_auth_exports(self) -> None:
        """FederatedIdentityAdapter should be in auth __all__."""
        from framework_m.adapters import auth

        assert "FederatedIdentityAdapter" in auth.__all__


# =============================================================================
# Test: FederatedIdentityAdapter Protocol Compliance
# =============================================================================


class TestFederatedIdentityAdapterProtocol:
    """Tests for IdentityProtocol compliance."""

    def test_has_get_user_method(self) -> None:
        """FederatedIdentityAdapter should have get_user method."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        assert hasattr(FederatedIdentityAdapter, "get_user")

    def test_has_get_user_by_email_method(self) -> None:
        """FederatedIdentityAdapter should have get_user_by_email method."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        assert hasattr(FederatedIdentityAdapter, "get_user_by_email")

    def test_has_authenticate_method(self) -> None:
        """FederatedIdentityAdapter should have authenticate method."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        assert hasattr(FederatedIdentityAdapter, "authenticate")

    def test_has_get_attributes_method(self) -> None:
        """FederatedIdentityAdapter should have get_attributes method."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        assert hasattr(FederatedIdentityAdapter, "get_attributes")

    def test_has_validate_token_method(self) -> None:
        """FederatedIdentityAdapter should have validate_token method."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        assert hasattr(FederatedIdentityAdapter, "validate_token")


# =============================================================================
# Test: FederatedIdentityAdapter.get_user (Header Hydration)
# =============================================================================


class TestFederatedIdentityAdapterGetUser:
    """Tests for FederatedIdentityAdapter.get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_from_cache(self) -> None:
        """get_user should return user from preferences cache."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        mock_prefs_repo = AsyncMock()
        mock_prefs_repo.get_by_user_id.return_value = MagicMock(
            user_id="user-123",
            settings={"display_name": "John Doe", "email": "john@example.com"},
        )

        adapter = FederatedIdentityAdapter(preferences_repository=mock_prefs_repo)
        result = await adapter.get_user("user-123")

        assert result is not None
        assert isinstance(result, UserContext)
        assert result.id == "user-123"

    @pytest.mark.asyncio
    async def test_get_user_returns_none_for_missing(self) -> None:
        """get_user should return None if no preferences exist."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        mock_prefs_repo = AsyncMock()
        mock_prefs_repo.get_by_user_id.return_value = None

        adapter = FederatedIdentityAdapter(preferences_repository=mock_prefs_repo)
        result = await adapter.get_user("unknown-user")

        assert result is None


# =============================================================================
# Test: FederatedIdentityAdapter.authenticate (Should Raise)
# =============================================================================


class TestFederatedIdentityAdapterAuthenticate:
    """Tests for FederatedIdentityAdapter.authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_raises_not_implemented(self) -> None:
        """authenticate should raise NotImplementedError for federated mode."""
        from framework_m.adapters.auth.federated_identity import (
            FederatedIdentityAdapter,
        )

        mock_prefs_repo = AsyncMock()
        adapter = FederatedIdentityAdapter(preferences_repository=mock_prefs_repo)

        credentials = PasswordCredentials(
            username="test@example.com",
            password="secret123",
        )

        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.authenticate(credentials)

        assert "external auth gateway" in str(exc_info.value).lower()


# =============================================================================
# Test: FederatedIdentityAdapter.hydrate_from_headers
# =============================================================================


class TestFederatedIdentityAdapterHydration:
    """Tests for header hydration functionality."""

    def test_import_hydrate_from_headers(self) -> None:
        """hydrate_from_headers should be importable."""
        from framework_m.adapters.auth.federated_identity import hydrate_from_headers

        assert hydrate_from_headers is not None

    def test_hydrate_from_headers_creates_user_context(self) -> None:
        """hydrate_from_headers should create UserContext from headers."""
        from framework_m.adapters.auth.federated_identity import hydrate_from_headers

        headers = {
            "X-User-ID": "user-123",
            "X-Email": "john@example.com",
            "X-Full-Name": "John Doe",
            "X-Roles": "Employee,Manager",
            "X-Tenants": "tenant-001,tenant-002",
        }

        result = hydrate_from_headers(headers)

        assert result is not None
        assert result.id == "user-123"
        assert result.email == "john@example.com"
        assert result.name == "John Doe"
        assert result.roles == ["Employee", "Manager"]
        assert result.tenants == ["tenant-001", "tenant-002"]

    def test_hydrate_from_headers_minimal(self) -> None:
        """hydrate_from_headers should work with minimal headers."""
        from framework_m.adapters.auth.federated_identity import hydrate_from_headers

        headers = {
            "X-User-ID": "user-123",
            "X-Email": "john@example.com",
        }

        result = hydrate_from_headers(headers)

        assert result.id == "user-123"
        assert result.email == "john@example.com"
        assert result.roles == []
        assert result.tenants == []

    def test_hydrate_from_headers_returns_none_missing_user_id(self) -> None:
        """hydrate_from_headers should return None if X-User-ID missing."""
        from framework_m.adapters.auth.federated_identity import hydrate_from_headers

        headers = {
            "X-Email": "john@example.com",
        }

        result = hydrate_from_headers(headers)
        assert result is None

    def test_hydrate_from_headers_returns_none_missing_email(self) -> None:
        """hydrate_from_headers should return None if X-Email missing."""
        from framework_m.adapters.auth.federated_identity import hydrate_from_headers

        headers = {
            "X-User-ID": "user-123",
        }

        result = hydrate_from_headers(headers)
        assert result is None
