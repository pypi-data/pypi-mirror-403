"""Citadel Policy Adapter - Enterprise Policy-as-Code integration.

This module provides the CitadelPolicyAdapter, which delegates authorization
decisions to an external policy service (Cedar, OPA, or similar).

The adapter constructs a standardized AuthorizationRequest and sends it to
a configurable policy endpoint, enabling "Policy as Code" for authorization.

Configuration in framework_config.toml:
    [permissions.citadel]
    enabled = true
    endpoint = "http://citadel-policy:8080/v1/authorize"
    timeout_ms = 500
    fallback_on_error = false  # Deny on error by default

Example:
    adapter = CitadelPolicyAdapter(endpoint="http://policy-service:8080/authorize")
    result = await adapter.evaluate(PolicyEvaluateRequest(
        principal="user-123",
        action="invoice:create",
        resource="Invoice",
        resource_id="INV-001",
        tenant_id="acme-corp",
        principal_attributes={"roles": ["Manager"], "department": "Sales"},
    ))
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from framework_m.cli.config import load_config
from framework_m.core.interfaces.permission import (
    DecisionSource,
    PermissionAction,
    PermissionProtocol,
    PolicyEvaluateRequest,
    PolicyEvaluateResult,
)

# =============================================================================
# Authorization Request Model (Cedar/Citadel Format)
# =============================================================================


@dataclass
class AuthorizationRequest:
    """Standardized authorization request for policy engines.

    This format is compatible with Cedar, OPA, and similar policy engines.

    Attributes:
        principal: User/subject identifier (user.id)
        action: Action being performed (doctype:action format)
        resource: Resource being accessed (doctype:name format)
        tenant_id: Multi-tenant context
        context: Additional context (IP, time, device, etc.)
        principal_attributes: User attributes (roles, department, level)
        resource_attributes: Resource attributes (owner, status, etc.)

    Example:
        request = AuthorizationRequest(
            principal="user-123",
            action="invoice:create",
            resource="Invoice:INV-001",
            tenant_id="acme-corp",
            principal_attributes={"roles": ["Manager"]},
        )
    """

    principal: str
    action: str
    resource: str
    tenant_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    principal_attributes: dict[str, Any] = field(default_factory=dict)
    resource_attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AuthorizationResponse:
    """Response from policy service.

    Attributes:
        allowed: Whether the action is authorized
        reason: Explanation for the decision
        policy_id: ID of the policy that made the decision
    """

    allowed: bool
    reason: str | None = None
    policy_id: str | None = None


# =============================================================================
# Citadel Policy Adapter
# =============================================================================


class CitadelPolicyAdapter(PermissionProtocol):
    """Enterprise policy adapter using external policy service.

    Delegates authorization decisions to a Cedar/OPA policy engine,
    enabling "Policy as Code" with version-controlled policy definitions.

    The adapter:
    1. Constructs AuthorizationRequest from PolicyEvaluateRequest
    2. Calls the configured policy endpoint
    3. Returns PolicyEvaluateResult based on response

    Args:
        endpoint: Policy service URL (e.g., "http://citadel:8080/authorize")
        timeout_ms: Request timeout in milliseconds (default: 500)
        fallback_on_error: If True, allow on error; if False, deny on error

    Example:
        adapter = CitadelPolicyAdapter(
            endpoint="http://policy-service:8080/v1/authorize"
        )
        result = await adapter.evaluate(request)
    """

    def __init__(
        self,
        endpoint: str | None = None,
        timeout_ms: int = 500,
        fallback_on_error: bool = False,
        http_client: Any = None,  # For testing injection
    ) -> None:
        """Initialize the Citadel policy adapter.

        Args:
            endpoint: Policy service URL (required in production)
            timeout_ms: Request timeout in milliseconds
            fallback_on_error: Allow on error if True, deny if False
            http_client: Optional HTTP client for testing
        """
        config = self._load_config()
        self._endpoint = endpoint or config.get("endpoint", "")
        self._timeout_ms = timeout_ms or config.get("timeout_ms", 500)
        self._fallback_on_error = fallback_on_error or config.get(
            "fallback_on_error", False
        )
        self._http_client = http_client

    def _load_config(self) -> dict[str, Any]:
        """Load citadel configuration from config file."""
        config = load_config()
        permissions_config: dict[str, Any] = config.get("permissions", {})
        citadel_config: dict[str, Any] = permissions_config.get("citadel", {})
        return citadel_config

    def _build_authorization_request(
        self, request: PolicyEvaluateRequest
    ) -> AuthorizationRequest:
        """Build AuthorizationRequest from PolicyEvaluateRequest.

        Constructs the standardized request format for policy engines.

        Args:
            request: Framework's policy evaluate request

        Returns:
            AuthorizationRequest for the policy service
        """
        # Format action as doctype:action (e.g., "Invoice:create")
        action_str = (
            request.action.value
            if isinstance(request.action, PermissionAction)
            else str(request.action)
        )
        formatted_action = f"{request.resource}:{action_str}"

        # Format resource as doctype:id or just doctype
        formatted_resource = (
            f"{request.resource}:{request.resource_id}"
            if request.resource_id
            else request.resource
        )

        return AuthorizationRequest(
            principal=request.principal,
            action=formatted_action,
            resource=formatted_resource,
            tenant_id=request.tenant_id,
            context=request.context,
            principal_attributes=request.principal_attributes,
            resource_attributes=request.resource_attributes,
        )

    async def _call_policy_service(
        self, auth_request: AuthorizationRequest
    ) -> AuthorizationResponse:
        """Call the external policy service.

        Args:
            auth_request: Authorization request to send

        Returns:
            AuthorizationResponse from the policy service

        Raises:
            Exception: If the policy service is unreachable
        """
        if self._http_client is not None:
            # Use injected client (for testing)
            result: AuthorizationResponse = await self._http_client.authorize(
                auth_request
            )
            return result

        if not self._endpoint:
            raise ValueError(
                "Citadel endpoint not configured. "
                "Set [permissions.citadel].endpoint in framework_config.toml"
            )

        # Use httpx for async HTTP calls
        try:
            import httpx

            timeout = self._timeout_ms / 1000.0  # Convert to seconds

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self._endpoint,
                    json=auth_request.to_dict(),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                data = response.json()
                return AuthorizationResponse(
                    allowed=data.get("allowed", False),
                    reason=data.get("reason"),
                    policy_id=data.get("policy_id"),
                )
        except ImportError:
            raise ImportError(
                "httpx package not installed. Run: pip install httpx"
            ) from None

    async def evaluate(
        self,
        request: PolicyEvaluateRequest,
    ) -> PolicyEvaluateResult:
        """Evaluate authorization via external policy service.

        Constructs an AuthorizationRequest and calls the Citadel/Cedar
        policy service for a decision.

        Args:
            request: Stateless request containing all context

        Returns:
            PolicyEvaluateResult with decision from policy service
        """
        # Build the authorization request
        auth_request = self._build_authorization_request(request)

        try:
            # Call policy service
            response = await self._call_policy_service(auth_request)

            return PolicyEvaluateResult(
                authorized=response.allowed,
                decision_source=DecisionSource.ABAC,
                reason=response.reason or "Policy decision from Citadel",
            )

        except Exception as e:
            # Handle errors based on fallback configuration
            if self._fallback_on_error:
                return PolicyEvaluateResult(
                    authorized=True,
                    decision_source=DecisionSource.ABAC,
                    reason=f"Policy service error, fallback allowed: {e}",
                )
            else:
                return PolicyEvaluateResult(
                    authorized=False,
                    decision_source=DecisionSource.ABAC,
                    reason=f"Policy service error, denied: {e}",
                )

    async def get_permitted_filters(
        self,
        principal: str,
        principal_attributes: dict[str, Any],
        resource: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Get RLS filters from policy service.

        For enterprise deployments, the policy service may return
        specific document IDs or filter conditions.

        Args:
            principal: User ID
            principal_attributes: User attributes
            resource: DocType name
            tenant_id: Optional tenant context

        Returns:
            Filter dict to apply (may include specific IDs or conditions)
        """
        # For now, return empty filters (no RLS from external service)
        # In a full implementation, this would call a separate endpoint
        # to get permitted document IDs or filter conditions
        return {}


__all__ = [
    "AuthorizationRequest",
    "AuthorizationResponse",
    "CitadelPolicyAdapter",
]
