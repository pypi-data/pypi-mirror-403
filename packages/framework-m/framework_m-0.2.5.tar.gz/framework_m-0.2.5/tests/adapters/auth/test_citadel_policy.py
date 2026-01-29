"""Tests for CitadelPolicyAdapter.

Tests cover:
- AuthorizationRequest construction
- Policy evaluation via mock service
- Error handling and fallback behavior
"""

import pytest

from framework_m.adapters.auth.citadel_policy import (
    AuthorizationRequest,
    AuthorizationResponse,
    CitadelPolicyAdapter,
)
from framework_m.core.interfaces.permission import (
    DecisionSource,
    PermissionAction,
    PolicyEvaluateRequest,
)

# =============================================================================
# Test: Imports
# =============================================================================


class TestCitadelPolicyImports:
    """Tests for CitadelPolicyAdapter imports."""

    def test_import_citadel_policy_adapter(self) -> None:
        """CitadelPolicyAdapter should be importable."""
        from framework_m.adapters.auth.citadel_policy import CitadelPolicyAdapter

        assert CitadelPolicyAdapter is not None

    def test_import_authorization_request(self) -> None:
        """AuthorizationRequest should be importable."""
        from framework_m.adapters.auth.citadel_policy import AuthorizationRequest

        assert AuthorizationRequest is not None

    def test_import_authorization_response(self) -> None:
        """AuthorizationResponse should be importable."""
        from framework_m.adapters.auth.citadel_policy import AuthorizationResponse

        assert AuthorizationResponse is not None


# =============================================================================
# Test: AuthorizationRequest
# =============================================================================


class TestAuthorizationRequest:
    """Tests for AuthorizationRequest model."""

    def test_create_authorization_request(self) -> None:
        """AuthorizationRequest should create with required fields."""
        request = AuthorizationRequest(
            principal="user-123",
            action="Invoice:create",
            resource="Invoice:INV-001",
        )
        assert request.principal == "user-123"
        assert request.action == "Invoice:create"
        assert request.resource == "Invoice:INV-001"

    def test_authorization_request_with_tenant(self) -> None:
        """AuthorizationRequest should accept tenant_id."""
        request = AuthorizationRequest(
            principal="user-123",
            action="Invoice:read",
            resource="Invoice",
            tenant_id="acme-corp",
        )
        assert request.tenant_id == "acme-corp"

    def test_authorization_request_with_attributes(self) -> None:
        """AuthorizationRequest should accept attributes."""
        request = AuthorizationRequest(
            principal="user-123",
            action="Invoice:create",
            resource="Invoice",
            principal_attributes={"roles": ["Manager"], "department": "Sales"},
            resource_attributes={"status": "draft"},
        )
        assert request.principal_attributes["roles"] == ["Manager"]
        assert request.resource_attributes["status"] == "draft"

    def test_to_dict(self) -> None:
        """to_dict should serialize to dictionary."""
        request = AuthorizationRequest(
            principal="user-123",
            action="Invoice:read",
            resource="Invoice",
            tenant_id="acme",
        )
        data = request.to_dict()
        assert data["principal"] == "user-123"
        assert data["action"] == "Invoice:read"
        assert data["tenant_id"] == "acme"


# =============================================================================
# Test: CitadelPolicyAdapter Construction
# =============================================================================


class TestCitadelPolicyAdapterInit:
    """Tests for CitadelPolicyAdapter initialization."""

    def test_init_with_endpoint(self) -> None:
        """CitadelPolicyAdapter should accept endpoint."""
        adapter = CitadelPolicyAdapter(endpoint="http://policy:8080/authorize")
        assert adapter._endpoint == "http://policy:8080/authorize"

    def test_init_with_timeout(self) -> None:
        """CitadelPolicyAdapter should accept timeout_ms."""
        adapter = CitadelPolicyAdapter(endpoint="http://policy:8080", timeout_ms=1000)
        assert adapter._timeout_ms == 1000

    def test_init_with_fallback(self) -> None:
        """CitadelPolicyAdapter should accept fallback_on_error."""
        adapter = CitadelPolicyAdapter(
            endpoint="http://policy:8080", fallback_on_error=True
        )
        assert adapter._fallback_on_error is True


# =============================================================================
# Test: AuthorizationRequest Building
# =============================================================================


class TestAuthorizationRequestBuilding:
    """Tests for building AuthorizationRequest from PolicyEvaluateRequest."""

    def test_build_request_basic(self) -> None:
        """_build_authorization_request should format action and resource."""
        adapter = CitadelPolicyAdapter(endpoint="http://policy:8080")

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.CREATE,
            resource="Invoice",
        )

        auth_request = adapter._build_authorization_request(request)

        assert auth_request.principal == "user-123"
        assert auth_request.action == "Invoice:create"
        assert auth_request.resource == "Invoice"

    def test_build_request_with_resource_id(self) -> None:
        """_build_authorization_request should include resource_id."""
        adapter = CitadelPolicyAdapter(endpoint="http://policy:8080")

        request = PolicyEvaluateRequest(
            principal="user-123",
            action="read",
            resource="Invoice",
            resource_id="INV-001",
        )

        auth_request = adapter._build_authorization_request(request)

        assert auth_request.resource == "Invoice:INV-001"

    def test_build_request_with_tenant(self) -> None:
        """_build_authorization_request should include tenant_id."""
        adapter = CitadelPolicyAdapter(endpoint="http://policy:8080")

        request = PolicyEvaluateRequest(
            principal="user-123",
            action="read",
            resource="Invoice",
            tenant_id="acme-corp",
        )

        auth_request = adapter._build_authorization_request(request)

        assert auth_request.tenant_id == "acme-corp"

    def test_build_request_with_attributes(self) -> None:
        """_build_authorization_request should include attributes."""
        adapter = CitadelPolicyAdapter(endpoint="http://policy:8080")

        request = PolicyEvaluateRequest(
            principal="user-123",
            action="write",
            resource="Invoice",
            principal_attributes={"roles": ["Manager"]},
            resource_attributes={"owner": "user-456"},
        )

        auth_request = adapter._build_authorization_request(request)

        assert auth_request.principal_attributes["roles"] == ["Manager"]
        assert auth_request.resource_attributes["owner"] == "user-456"


# =============================================================================
# Mock HTTP Client for Testing
# =============================================================================


class MockPolicyClient:
    """Mock HTTP client for testing CitadelPolicyAdapter."""

    def __init__(self, response: AuthorizationResponse) -> None:
        self.response = response
        self.last_request: AuthorizationRequest | None = None

    async def authorize(self, request: AuthorizationRequest) -> AuthorizationResponse:
        self.last_request = request
        return self.response


class MockErrorClient:
    """Mock client that raises errors."""

    async def authorize(self, request: AuthorizationRequest) -> AuthorizationResponse:
        raise ConnectionError("Policy service unavailable")


# =============================================================================
# Test: Policy Evaluation
# =============================================================================


class TestCitadelPolicyEvaluation:
    """Tests for policy evaluation via mock service."""

    @pytest.mark.asyncio
    async def test_evaluate_allowed(self) -> None:
        """evaluate should return authorized=True when policy allows."""
        mock_client = MockPolicyClient(
            AuthorizationResponse(allowed=True, reason="Policy allowed")
        )
        adapter = CitadelPolicyAdapter(
            endpoint="http://policy:8080", http_client=mock_client
        )

        request = PolicyEvaluateRequest(
            principal="user-123",
            action="read",
            resource="Invoice",
        )

        result = await adapter.evaluate(request)

        assert result.authorized is True
        assert result.decision_source == DecisionSource.ABAC

    @pytest.mark.asyncio
    async def test_evaluate_denied(self) -> None:
        """evaluate should return authorized=False when policy denies."""
        mock_client = MockPolicyClient(
            AuthorizationResponse(allowed=False, reason="Insufficient permissions")
        )
        adapter = CitadelPolicyAdapter(
            endpoint="http://policy:8080", http_client=mock_client
        )

        request = PolicyEvaluateRequest(
            principal="user-123",
            action="delete",
            resource="Invoice",
        )

        result = await adapter.evaluate(request)

        assert result.authorized is False
        assert "Insufficient permissions" in (result.reason or "")

    @pytest.mark.asyncio
    async def test_evaluate_error_deny_by_default(self) -> None:
        """evaluate should deny on error when fallback_on_error=False."""
        adapter = CitadelPolicyAdapter(
            endpoint="http://policy:8080",
            http_client=MockErrorClient(),
            fallback_on_error=False,
        )

        request = PolicyEvaluateRequest(
            principal="user-123",
            action="read",
            resource="Invoice",
        )

        result = await adapter.evaluate(request)

        assert result.authorized is False
        assert "error" in (result.reason or "").lower()

    @pytest.mark.asyncio
    async def test_evaluate_error_allow_on_fallback(self) -> None:
        """evaluate should allow on error when fallback_on_error=True."""
        adapter = CitadelPolicyAdapter(
            endpoint="http://policy:8080",
            http_client=MockErrorClient(),
            fallback_on_error=True,
        )

        request = PolicyEvaluateRequest(
            principal="user-123",
            action="read",
            resource="Invoice",
        )

        result = await adapter.evaluate(request)

        assert result.authorized is True
        assert "fallback" in (result.reason or "").lower()


# =============================================================================
# Test: RLS Filters
# =============================================================================


class TestCitadelRLSFilters:
    """Tests for get_permitted_filters."""

    @pytest.mark.asyncio
    async def test_get_permitted_filters_empty(self) -> None:
        """get_permitted_filters should return empty dict for now."""
        adapter = CitadelPolicyAdapter(endpoint="http://policy:8080")

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={"roles": ["Manager"]},
            resource="Invoice",
        )

        assert filters == {}
