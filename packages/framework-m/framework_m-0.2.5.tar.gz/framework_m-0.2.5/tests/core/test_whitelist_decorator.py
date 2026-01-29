"""Tests for @whitelist Decorator.

TDD tests for the whitelist decorator that marks controller methods
as publicly callable via RPC endpoints.
"""

from framework_m.core.domain.base_controller import BaseController
from framework_m.core.domain.base_doctype import BaseDocType

# =============================================================================
# Test DocType and Controller
# =============================================================================


class Task(BaseDocType):
    """Test DocType."""

    title: str = ""
    completed: bool = False


class TaskController(BaseController[Task]):
    """Test controller with whitelisted methods."""

    pass  # Methods will be added after decorator is implemented


# =============================================================================
# Tests for @whitelist Decorator
# =============================================================================


class TestWhitelistDecorator:
    """Tests for the @whitelist decorator."""

    def test_whitelist_is_importable(self) -> None:
        """@whitelist should be importable from core.decorators."""
        from framework_m.core.decorators import whitelist

        assert whitelist is not None

    def test_whitelist_marks_method(self) -> None:
        """@whitelist should add metadata to method."""
        from framework_m.core.decorators import WHITELIST_ATTR, whitelist

        @whitelist()
        async def my_method() -> str:
            return "hello"

        assert hasattr(my_method, WHITELIST_ATTR)

    def test_whitelist_default_options(self) -> None:
        """@whitelist should have sensible defaults."""
        from framework_m.core.decorators import WHITELIST_ATTR, whitelist

        @whitelist()
        async def my_method() -> str:
            return "hello"

        options = getattr(my_method, WHITELIST_ATTR)
        assert options["allow_guest"] is False
        assert options["methods"] == ["POST"]

    def test_whitelist_custom_options(self) -> None:
        """@whitelist should accept custom options."""
        from framework_m.core.decorators import WHITELIST_ATTR, whitelist

        @whitelist(allow_guest=True, methods=["GET", "POST"])
        async def public_method() -> str:
            return "public"

        options = getattr(public_method, WHITELIST_ATTR)
        assert options["allow_guest"] is True
        assert options["methods"] == ["GET", "POST"]


class TestIsWhitelisted:
    """Tests for is_whitelisted helper."""

    def test_is_whitelisted_is_importable(self) -> None:
        """is_whitelisted should be importable."""
        from framework_m.core.decorators import is_whitelisted

        assert is_whitelisted is not None

    def test_returns_true_for_decorated(self) -> None:
        """is_whitelisted should return True for decorated methods."""
        from framework_m.core.decorators import is_whitelisted, whitelist

        @whitelist()
        async def decorated() -> None:
            pass

        assert is_whitelisted(decorated) is True

    def test_returns_false_for_undecorated(self) -> None:
        """is_whitelisted should return False for undecorated methods."""
        from framework_m.core.decorators import is_whitelisted

        async def undecorated() -> None:
            pass

        assert is_whitelisted(undecorated) is False


class TestGetWhitelistOptions:
    """Tests for get_whitelist_options helper."""

    def test_get_whitelist_options_is_importable(self) -> None:
        """get_whitelist_options should be importable."""
        from framework_m.core.decorators import get_whitelist_options

        assert get_whitelist_options is not None

    def test_returns_options_for_decorated(self) -> None:
        """get_whitelist_options should return options dict."""
        from framework_m.core.decorators import get_whitelist_options, whitelist

        @whitelist(allow_guest=True)
        async def my_method() -> None:
            pass

        options = get_whitelist_options(my_method)
        assert options["allow_guest"] is True

    def test_returns_empty_for_undecorated(self) -> None:
        """get_whitelist_options should return empty dict for undecorated."""
        from framework_m.core.decorators import get_whitelist_options

        async def undecorated() -> None:
            pass

        options = get_whitelist_options(undecorated)
        assert options == {}


class TestWhitelistOnController:
    """Tests for @whitelist on controller methods."""

    def test_whitelist_on_controller_method(self) -> None:
        """@whitelist should work on controller methods."""
        from framework_m.core.decorators import is_whitelisted, whitelist

        class TestController(BaseController[Task]):
            @whitelist()
            async def mark_complete(self) -> bool:
                self.doc.completed = True
                return True

        controller = TestController(Task(title="Test"))
        assert is_whitelisted(controller.mark_complete)

    def test_non_whitelist_method_not_exposed(self) -> None:
        """Non-decorated methods should not be whitelisted."""
        from framework_m.core.decorators import is_whitelisted

        class TestController(BaseController[Task]):
            async def internal_method(self) -> None:
                pass

        controller = TestController(Task(title="Test"))
        assert is_whitelisted(controller.internal_method) is False
