"""Tests for User Data Routes (GDPR).

Tests cover:
- GET /api/v1/auth/me/data - Export user data
- DELETE /api/v1/auth/me - Delete account
"""


# =============================================================================
# Test: User Data Routes Import
# =============================================================================


class TestUserDataRoutesImport:
    """Tests for User data routes import."""

    def test_import_user_data_routes_router(self) -> None:
        """user_data_routes_router should be importable."""
        from framework_m.adapters.web.user_data_routes import user_data_routes_router

        assert user_data_routes_router is not None

    def test_import_export_user_data(self) -> None:
        """export_user_data handler should be importable."""
        from framework_m.adapters.web.user_data_routes import export_user_data

        assert export_user_data is not None

    def test_import_delete_account(self) -> None:
        """delete_account handler should be importable."""
        from framework_m.adapters.web.user_data_routes import delete_account

        assert delete_account is not None


# =============================================================================
# Test: Router Configuration
# =============================================================================


class TestUserDataRoutesConfig:
    """Tests for User data routes configuration."""

    def test_router_has_correct_path(self) -> None:
        """User data router should be mounted at /api/v1/auth/me."""
        from framework_m.adapters.web.user_data_routes import user_data_routes_router

        assert user_data_routes_router.path == "/api/v1/auth/me"

    def test_router_has_auth_tag(self) -> None:
        """User data router should have 'auth' tag."""
        from framework_m.adapters.web.user_data_routes import user_data_routes_router

        assert "auth" in user_data_routes_router.tags

    def test_router_has_gdpr_tag(self) -> None:
        """User data router should have 'gdpr' tag."""
        from framework_m.adapters.web.user_data_routes import user_data_routes_router

        assert "gdpr" in user_data_routes_router.tags


# =============================================================================
# Test: Response Models
# =============================================================================


class TestUserDataResponseModels:
    """Tests for User data response models."""

    def test_import_data_export_response(self) -> None:
        """DataExportResponse should be importable."""
        from framework_m.adapters.web.user_data_routes import DataExportResponse

        assert DataExportResponse is not None

    def test_import_account_delete_response(self) -> None:
        """AccountDeleteResponse should be importable."""
        from framework_m.adapters.web.user_data_routes import AccountDeleteResponse

        assert AccountDeleteResponse is not None

    def test_account_delete_response_model(self) -> None:
        """AccountDeleteResponse should accept expected fields."""
        from framework_m.adapters.web.user_data_routes import AccountDeleteResponse

        response = AccountDeleteResponse(
            message="Account deleted",
            mode="hard_delete",
            deleted_items={"sessions": 5, "api_keys": 2},
        )

        assert response.message == "Account deleted"
        assert response.mode == "hard_delete"
        assert response.deleted_items["sessions"] == 5
