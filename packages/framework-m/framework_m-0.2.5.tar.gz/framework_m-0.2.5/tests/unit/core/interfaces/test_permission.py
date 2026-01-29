"""Tests for PermissionProtocol interface compliance."""

from framework_m.core.interfaces.permission import (
    DecisionSource,
    PermissionAction,
    PermissionProtocol,
    PolicyEvaluateRequest,
    PolicyEvaluateResult,
)


class TestPermissionAction:
    """Tests for PermissionAction enum."""

    def test_permission_action_values(self) -> None:
        """PermissionAction should have all required action types."""
        assert PermissionAction.READ.value == "read"
        assert PermissionAction.WRITE.value == "write"
        assert PermissionAction.CREATE.value == "create"
        assert PermissionAction.DELETE.value == "delete"
        assert PermissionAction.SUBMIT.value == "submit"
        assert PermissionAction.CANCEL.value == "cancel"
        assert PermissionAction.AMEND.value == "amend"


class TestDecisionSource:
    """Tests for DecisionSource enum."""

    def test_decision_source_values(self) -> None:
        """DecisionSource should have all required source types."""
        assert DecisionSource.RBAC.value == "rbac"
        assert DecisionSource.ABAC.value == "abac"
        assert DecisionSource.REBAC.value == "rebac"
        assert DecisionSource.COMBO.value == "combo"


class TestPolicyEvaluateRequest:
    """Tests for PolicyEvaluateRequest dataclass."""

    def test_request_creation(self) -> None:
        """PolicyEvaluateRequest should create with required fields."""
        request = PolicyEvaluateRequest(
            principal="user-001",
            action="read",
            resource="Invoice",
        )
        assert request.principal == "user-001"
        assert request.action == "read"
        assert request.resource == "Invoice"
        assert request.context == {}


class TestPolicyEvaluateResult:
    """Tests for PolicyEvaluateResult dataclass."""

    def test_result_creation(self) -> None:
        """PolicyEvaluateResult should create with required fields."""
        result = PolicyEvaluateResult(
            authorized=True,
            decision_source=DecisionSource.RBAC,
        )
        assert result.authorized is True
        assert result.decision_source == DecisionSource.RBAC


class TestPermissionProtocol:
    """Tests for PermissionProtocol interface."""

    def test_protocol_has_evaluate_method(self) -> None:
        """PermissionProtocol should define evaluate method."""
        assert hasattr(PermissionProtocol, "evaluate")

    def test_protocol_has_get_permitted_filters_method(self) -> None:
        """PermissionProtocol should define get_permitted_filters method."""
        assert hasattr(PermissionProtocol, "get_permitted_filters")
