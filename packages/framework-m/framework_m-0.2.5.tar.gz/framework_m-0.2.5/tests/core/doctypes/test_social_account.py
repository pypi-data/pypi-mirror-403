"""Tests for SocialAccount DocType.

TDD: This test file is created BEFORE the implementation.

SocialAccount links OAuth2/OIDC providers to local users.
"""


# =============================================================================
# Test: SocialAccount Import
# =============================================================================


class TestSocialAccountImport:
    """Tests for SocialAccount DocType import."""

    def test_import_social_account(self) -> None:
        """SocialAccount should be importable from doctypes."""
        from framework_m.core.doctypes.social_account import SocialAccount

        assert SocialAccount is not None

    def test_social_account_in_all_exports(self) -> None:
        """SocialAccount should be in __all__."""
        from framework_m.core.doctypes import social_account

        assert "SocialAccount" in social_account.__all__


# =============================================================================
# Test: SocialAccount Creation
# =============================================================================


class TestSocialAccountCreation:
    """Tests for SocialAccount DocType creation."""

    def test_create_social_account_with_required_fields(self) -> None:
        """SocialAccount should be creatable with required fields."""
        from framework_m.core.doctypes.social_account import SocialAccount

        account = SocialAccount(
            provider="google",
            provider_user_id="google-123456",
            user_id="user-001",
            display_name="John Doe",
        )

        assert account.provider == "google"
        assert account.provider_user_id == "google-123456"
        assert account.user_id == "user-001"
        assert account.display_name == "John Doe"

    def test_social_account_inherits_from_base_doctype(self) -> None:
        """SocialAccount should inherit from BaseDocType."""
        from framework_m.core.doctypes.social_account import SocialAccount
        from framework_m.core.domain.base_doctype import BaseDocType

        assert issubclass(SocialAccount, BaseDocType)


# =============================================================================
# Test: SocialAccount Fields
# =============================================================================


class TestSocialAccountFields:
    """Tests for SocialAccount field configuration."""

    def test_email_optional(self) -> None:
        """email should be optional."""
        from framework_m.core.doctypes.social_account import SocialAccount

        account = SocialAccount(
            provider="github",
            provider_user_id="gh-789",
            user_id="user-002",
            display_name="Jane Dev",
        )

        assert account.email is None

    def test_email_can_be_set(self) -> None:
        """email should be settable for lookup purposes."""
        from framework_m.core.doctypes.social_account import SocialAccount

        account = SocialAccount(
            provider="github",
            provider_user_id="gh-789",
            user_id="user-002",
            display_name="Jane Dev",
            email="jane@example.com",
        )

        assert account.email == "jane@example.com"

    def test_provider_validators(self) -> None:
        """provider should be one of the supported providers."""
        from framework_m.core.doctypes.social_account import (
            SUPPORTED_PROVIDERS,
            SocialAccount,
        )

        # Should accept supported providers
        for provider in SUPPORTED_PROVIDERS:
            account = SocialAccount(
                provider=provider,
                provider_user_id=f"{provider}-123",
                user_id="user-001",
                display_name="Test User",
            )
            assert account.provider == provider


# =============================================================================
# Test: SocialAccount Meta
# =============================================================================


class TestSocialAccountMeta:
    """Tests for SocialAccount Meta configuration."""

    def test_api_resource_false(self) -> None:
        """SocialAccount should not be a direct API resource."""
        from framework_m.core.doctypes.social_account import SocialAccount

        assert SocialAccount.get_api_resource() is False

    def test_apply_rls(self) -> None:
        """SocialAccount should apply RLS based on user_id."""
        from framework_m.core.doctypes.social_account import SocialAccount

        assert SocialAccount.get_apply_rls() is True
        assert SocialAccount.get_rls_field() == "user_id"
