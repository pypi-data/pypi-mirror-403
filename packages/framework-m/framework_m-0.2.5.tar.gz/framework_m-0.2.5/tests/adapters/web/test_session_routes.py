"""Tests for Session API Routes.

Tests cover:
- GET /api/v1/auth/sessions - List active sessions
- DELETE /api/v1/auth/sessions/{id} - Revoke session
- DELETE /api/v1/auth/sessions - Logout all
"""

# =============================================================================
# Test: Session Routes Import
# =============================================================================


class TestSessionRoutesImport:
    """Tests for Session routes import."""

    def test_import_session_routes_router(self) -> None:
        """session_routes_router should be importable."""
        from framework_m.adapters.web.session_routes import session_routes_router

        assert session_routes_router is not None

    def test_import_list_sessions(self) -> None:
        """list_sessions handler should be importable."""
        from framework_m.adapters.web.session_routes import list_sessions

        assert list_sessions is not None

    def test_import_revoke_session(self) -> None:
        """revoke_session handler should be importable."""
        from framework_m.adapters.web.session_routes import revoke_session

        assert revoke_session is not None

    def test_import_logout_all(self) -> None:
        """logout_all handler should be importable."""
        from framework_m.adapters.web.session_routes import logout_all

        assert logout_all is not None


# =============================================================================
# Test: Session Routes Configuration
# =============================================================================


class TestSessionRoutesConfig:
    """Tests for Session routes configuration."""

    def test_router_has_correct_path(self) -> None:
        """Session router should be mounted at /api/v1/auth/sessions."""
        from framework_m.adapters.web.session_routes import session_routes_router

        assert session_routes_router.path == "/api/v1/auth/sessions"

    def test_router_has_auth_tag(self) -> None:
        """Session router should have 'auth' tag."""
        from framework_m.adapters.web.session_routes import session_routes_router

        assert "auth" in session_routes_router.tags


# =============================================================================
# Test: Response Models
# =============================================================================


class TestSessionResponseModels:
    """Tests for Session API response models."""

    def test_import_session_info(self) -> None:
        """SessionInfo should be importable."""
        from framework_m.adapters.web.session_routes import SessionInfo

        assert SessionInfo is not None

    def test_import_session_list_response(self) -> None:
        """SessionListResponse should be importable."""
        from framework_m.adapters.web.session_routes import SessionListResponse

        assert SessionListResponse is not None

    def test_import_session_revoke_response(self) -> None:
        """SessionRevokeResponse should be importable."""
        from framework_m.adapters.web.session_routes import SessionRevokeResponse

        assert SessionRevokeResponse is not None

    def test_import_logout_all_response(self) -> None:
        """LogoutAllResponse should be importable."""
        from framework_m.adapters.web.session_routes import LogoutAllResponse

        assert LogoutAllResponse is not None

    def test_session_info_model(self) -> None:
        """SessionInfo should accept expected fields."""
        from datetime import UTC, datetime

        from framework_m.adapters.web.session_routes import SessionInfo

        session = SessionInfo(
            id="sess_abc123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0...",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC),
            is_current=True,
        )

        assert session.id == "sess_abc123"
        assert session.is_current is True

    def test_session_list_response_model(self) -> None:
        """SessionListResponse should accept sessions and count."""
        from framework_m.adapters.web.session_routes import SessionListResponse

        response = SessionListResponse(sessions=[], count=0)

        assert response.sessions == []
        assert response.count == 0
