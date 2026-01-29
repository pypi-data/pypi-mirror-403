"""Tests for BaseController."""

import inspect
from typing import Any, ClassVar, get_type_hints

import pytest

from framework_m import DocType, Field
from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.core.domain.base_controller import BaseController


class Todo(DocType):
    """Test DocType for controller tests."""

    title: str = Field(description="Task title")
    is_completed: bool = False


class TodoController(BaseController[Todo]):
    """Test controller implementation."""

    def __init__(self, doc: Todo) -> None:
        super().__init__(doc)
        self.hooks_called: list[str] = []
        self.contexts_received: list[Any] = []

    async def validate(self, context: Any = None) -> None:
        """Track validate hook call."""
        self.hooks_called.append("validate")
        self.contexts_received.append(context)

    async def before_insert(self, context: Any = None) -> None:
        """Track before_insert hook call."""
        self.hooks_called.append("before_insert")
        self.contexts_received.append(context)

    async def after_insert(self, context: Any = None) -> None:
        """Track after_insert hook call."""
        self.hooks_called.append("after_insert")
        self.contexts_received.append(context)

    async def before_save(self, context: Any = None) -> None:
        """Track before_save hook call."""
        self.hooks_called.append("before_save")
        self.contexts_received.append(context)

    async def after_save(self, context: Any = None) -> None:
        """Track after_save hook call."""
        self.hooks_called.append("after_save")
        self.contexts_received.append(context)

    async def before_delete(self, context: Any = None) -> None:
        """Track before_delete hook call."""
        self.hooks_called.append("before_delete")
        self.contexts_received.append(context)

    async def after_delete(self, context: Any = None) -> None:
        """Track after_delete hook call."""
        self.hooks_called.append("after_delete")
        self.contexts_received.append(context)

    async def on_submit(self, context: Any = None) -> None:
        """Track on_submit hook call."""
        self.hooks_called.append("on_submit")
        self.contexts_received.append(context)

    async def on_cancel(self, context: Any = None) -> None:
        """Track on_cancel hook call."""
        self.hooks_called.append("on_cancel")
        self.contexts_received.append(context)


class TestBaseController:
    """Tests for BaseController functionality."""

    def test_controller_holds_document(self) -> None:
        """Controller should hold reference to document."""
        todo = Todo(title="Test")
        controller = TodoController(todo)

        assert controller.doc is todo
        assert controller.doc.title == "Test"

    def test_controller_is_generic(self) -> None:
        """Controller should be generic over DocType."""
        todo = Todo(title="Test")
        controller = TodoController(todo)

        # Type system ensures doc is Todo
        assert isinstance(controller.doc, Todo)


class TestLifecycleHooksSignature:
    """Tests to verify all lifecycle hooks have correct signature with context param."""

    LIFECYCLE_HOOKS: ClassVar[list[str]] = [
        "validate",
        "before_insert",
        "after_insert",
        "before_save",
        "after_save",
        "before_delete",
        "after_delete",
        "on_submit",
        "on_cancel",
    ]

    def test_all_hooks_have_context_parameter(self) -> None:
        """All lifecycle hooks should have context parameter."""
        for hook_name in self.LIFECYCLE_HOOKS:
            hook = getattr(BaseController, hook_name)
            sig = inspect.signature(hook)
            params = list(sig.parameters.keys())
            assert "context" in params, f"{hook_name} should have context parameter"

    def test_context_defaults_to_none(self) -> None:
        """Context parameter should default to None."""
        for hook_name in self.LIFECYCLE_HOOKS:
            hook = getattr(BaseController, hook_name)
            sig = inspect.signature(hook)
            context_param = sig.parameters.get("context")
            assert context_param is not None, f"{hook_name} missing context param"
            assert context_param.default is None, (
                f"{hook_name} context should default to None"
            )

    def test_context_type_is_any(self) -> None:
        """Context parameter should be typed as Any."""
        for hook_name in self.LIFECYCLE_HOOKS:
            hook = getattr(BaseController, hook_name)
            hints = get_type_hints(hook)
            assert "context" in hints, f"{hook_name} missing context type hint"
            assert hints["context"] is Any, f"{hook_name} context should be Any type"


class TestLifecycleHooksCallable:
    """Tests to verify all lifecycle hooks are callable."""

    @pytest.mark.asyncio
    async def test_validate_hook(self) -> None:
        """validate hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.validate(context=context)

        assert "validate" in controller.hooks_called
        assert context in controller.contexts_received

    @pytest.mark.asyncio
    async def test_validate_hook_without_context(self) -> None:
        """validate hook should work without context (default None)."""
        todo = Todo(title="Test")
        controller = TodoController(todo)

        await controller.validate()

        assert "validate" in controller.hooks_called
        assert None in controller.contexts_received

    @pytest.mark.asyncio
    async def test_before_insert_hook(self) -> None:
        """before_insert hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.before_insert(context=context)

        assert "before_insert" in controller.hooks_called
        assert context in controller.contexts_received

    @pytest.mark.asyncio
    async def test_after_insert_hook(self) -> None:
        """after_insert hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.after_insert(context=context)

        assert "after_insert" in controller.hooks_called
        assert context in controller.contexts_received

    @pytest.mark.asyncio
    async def test_before_save_hook(self) -> None:
        """before_save hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.before_save(context=context)

        assert "before_save" in controller.hooks_called
        assert context in controller.contexts_received

    @pytest.mark.asyncio
    async def test_after_save_hook(self) -> None:
        """after_save hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.after_save(context=context)

        assert "after_save" in controller.hooks_called
        assert context in controller.contexts_received

    @pytest.mark.asyncio
    async def test_before_delete_hook(self) -> None:
        """before_delete hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.before_delete(context=context)

        assert "before_delete" in controller.hooks_called
        assert context in controller.contexts_received

    @pytest.mark.asyncio
    async def test_after_delete_hook(self) -> None:
        """after_delete hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.after_delete(context=context)

        assert "after_delete" in controller.hooks_called
        assert context in controller.contexts_received

    @pytest.mark.asyncio
    async def test_on_submit_hook(self) -> None:
        """on_submit hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.on_submit(context=context)

        assert "on_submit" in controller.hooks_called
        assert context in controller.contexts_received

    @pytest.mark.asyncio
    async def test_on_cancel_hook(self) -> None:
        """on_cancel hook should be callable with context."""
        todo = Todo(title="Test")
        controller = TodoController(todo)
        context = {"user_id": "user-123"}

        await controller.on_cancel(context=context)

        assert "on_cancel" in controller.hooks_called
        assert context in controller.contexts_received


class TestBaseControllerDefaults:
    """Tests for BaseController default (no-op) implementations."""

    @pytest.mark.asyncio
    async def test_base_validate_does_nothing(self) -> None:
        """Base validate should be no-op."""
        todo = Todo(title="Test")
        controller = BaseController(todo)
        await controller.validate()  # Should not raise

    @pytest.mark.asyncio
    async def test_base_before_delete_does_nothing(self) -> None:
        """Base before_delete should be no-op."""
        todo = Todo(title="Test")
        controller = BaseController(todo)
        await controller.before_delete()  # Should not raise

    @pytest.mark.asyncio
    async def test_base_after_delete_does_nothing(self) -> None:
        """Base after_delete should be no-op."""
        todo = Todo(title="Test")
        controller = BaseController(todo)
        await controller.after_delete()  # Should not raise

    @pytest.mark.asyncio
    async def test_base_on_submit_does_nothing(self) -> None:
        """Base on_submit should be no-op."""
        todo = Todo(title="Test")
        controller = BaseController(todo)
        await controller.on_submit()  # Should not raise

    @pytest.mark.asyncio
    async def test_base_on_cancel_does_nothing(self) -> None:
        """Base on_cancel should be no-op."""
        todo = Todo(title="Test")
        controller = BaseController(todo)
        await controller.on_cancel()  # Should not raise


class TestControllerImport:
    """Tests for controller imports."""

    def test_import_base_controller(self) -> None:
        """BaseController should be importable."""
        from framework_m.core.domain.base_controller import BaseController

        assert BaseController is not None


# =============================================================================
# Tests for Permission Convenience Methods
# =============================================================================


class PermissionTestDocType(DocType):
    """DocType for permission tests with defined permissions."""

    title: str = Field(description="Title")

    class Meta:
        requires_auth: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
            "create": ["Manager"],
            "delete": ["Admin"],
        }


class TestCheckPermission:
    """Tests for check_permission() helper method."""

    @pytest.fixture(autouse=True)
    def register_doctype(self) -> None:
        """Register test DocType in MetaRegistry."""
        from framework_m.core.registry import MetaRegistry

        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("PermissionTestDocType")
        except KeyError:
            registry.register_doctype(PermissionTestDocType)

    @pytest.mark.asyncio
    async def test_check_permission_returns_true_for_authorized(self) -> None:
        """check_permission should return True when user has permission."""
        from framework_m.core.interfaces.auth_context import UserContext

        class TestController(BaseController[PermissionTestDocType]):
            user = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Manager"],
            )
            doctype_name = "PermissionTestDocType"
            permission = RbacPermissionAdapter()

        doc = PermissionTestDocType(title="Test")
        controller = TestController(doc)
        result = await controller.check_permission("write")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_permission_returns_false_for_unauthorized(self) -> None:
        """check_permission should return False when user lacks permission."""
        from framework_m.core.interfaces.auth_context import UserContext

        class TestController(BaseController[PermissionTestDocType]):
            user = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Employee"],  # Employee cannot write
            )
            doctype_name = "PermissionTestDocType"
            permission = RbacPermissionAdapter()

        doc = PermissionTestDocType(title="Test")
        controller = TestController(doc)
        result = await controller.check_permission("write")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_permission_with_doc_id(self) -> None:
        """check_permission should accept doc_id parameter."""
        from framework_m.core.interfaces.auth_context import UserContext

        class TestController(BaseController[PermissionTestDocType]):
            user = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Employee"],
            )
            doctype_name = "PermissionTestDocType"
            permission = RbacPermissionAdapter()

        doc = PermissionTestDocType(title="Test")
        controller = TestController(doc)
        # Employee can read
        result = await controller.check_permission("read", doc_id="DOC-001")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_permission_returns_false_without_user(self) -> None:
        """check_permission should return False when user is not set."""
        doc = PermissionTestDocType(title="Test")
        controller = BaseController(doc)
        # No user attribute set
        result = await controller.check_permission("read")
        assert result is False


class TestRequirePermission:
    """Tests for require_permission() helper method."""

    @pytest.fixture(autouse=True)
    def register_doctype(self) -> None:
        """Register test DocType in MetaRegistry."""
        from framework_m.core.registry import MetaRegistry

        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("PermissionTestDocType")
        except KeyError:
            registry.register_doctype(PermissionTestDocType)

    @pytest.mark.asyncio
    async def test_require_permission_does_not_raise_for_authorized(self) -> None:
        """require_permission should not raise when user is authorized."""
        from framework_m.core.interfaces.auth_context import UserContext

        class TestController(BaseController[PermissionTestDocType]):
            user = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Manager"],
            )
            doctype_name = "PermissionTestDocType"
            permission = RbacPermissionAdapter()

        doc = PermissionTestDocType(title="Test")
        controller = TestController(doc)
        # Should not raise
        await controller.require_permission("write")

    @pytest.mark.asyncio
    async def test_require_permission_raises_for_unauthorized(self) -> None:
        """require_permission should raise PermissionDeniedError when unauthorized."""
        from framework_m.core.exceptions import PermissionDeniedError
        from framework_m.core.interfaces.auth_context import UserContext

        class TestController(BaseController[PermissionTestDocType]):
            user = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Employee"],
            )
            doctype_name = "PermissionTestDocType"
            permission = RbacPermissionAdapter()

        doc = PermissionTestDocType(title="Test")
        controller = TestController(doc)
        with pytest.raises(PermissionDeniedError):
            await controller.require_permission("write")

    @pytest.mark.asyncio
    async def test_require_permission_with_doc_id(self) -> None:
        """require_permission should work with doc_id parameter."""
        from framework_m.core.interfaces.auth_context import UserContext

        class TestController(BaseController[PermissionTestDocType]):
            user = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Manager"],
            )
            doctype_name = "PermissionTestDocType"
            permission = RbacPermissionAdapter()

        doc = PermissionTestDocType(title="Test")
        controller = TestController(doc)
        # Should not raise
        await controller.require_permission("read", doc_id="DOC-001")
