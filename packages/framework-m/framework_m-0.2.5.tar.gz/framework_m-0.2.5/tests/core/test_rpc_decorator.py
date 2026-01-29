"""Tests for @rpc Decorator and RpcRegistry.

TDD tests for the @rpc decorator that marks standalone functions
as callable via dotted path RPC endpoints.
"""


# =============================================================================
# Tests for RpcRegistry
# =============================================================================


class TestRpcRegistry:
    """Tests for RpcRegistry singleton."""

    def test_rpc_registry_is_importable(self) -> None:
        """RpcRegistry should be importable."""
        from framework_m.core.rpc_registry import RpcRegistry

        assert RpcRegistry is not None

    def test_rpc_registry_is_singleton(self) -> None:
        """RpcRegistry should be a singleton."""
        from framework_m.core.rpc_registry import RpcRegistry

        registry1 = RpcRegistry.get_instance()
        registry2 = RpcRegistry.get_instance()
        assert registry1 is registry2

    def test_register_function(self) -> None:
        """register() should store function by path."""
        from framework_m.core.rpc_registry import RpcRegistry

        registry = RpcRegistry.get_instance()
        registry.reset()  # Clear for test

        async def my_func() -> str:
            return "hello"

        registry.register("my_app.api.my_func", my_func)
        assert registry.get("my_app.api.my_func") is my_func

    def test_get_returns_none_for_unregistered(self) -> None:
        """get() should return None for unregistered paths."""
        from framework_m.core.rpc_registry import RpcRegistry

        registry = RpcRegistry.get_instance()
        registry.reset()

        assert registry.get("unknown.path") is None

    def test_list_functions(self) -> None:
        """list_functions() should return all registered paths."""
        from framework_m.core.rpc_registry import RpcRegistry

        registry = RpcRegistry.get_instance()
        registry.reset()

        async def func1() -> None:
            pass

        async def func2() -> None:
            pass

        registry.register("app.func1", func1)
        registry.register("app.func2", func2)

        paths = registry.list_functions()
        assert "app.func1" in paths
        assert "app.func2" in paths


# =============================================================================
# Tests for @rpc Decorator
# =============================================================================


class TestRpcDecorator:
    """Tests for the @rpc decorator."""

    def test_rpc_is_importable(self) -> None:
        """@rpc should be importable from core.decorators."""
        from framework_m.core.decorators import rpc

        assert rpc is not None

    def test_rpc_marks_function(self) -> None:
        """@rpc should add metadata to function."""
        from framework_m.core.decorators import RPC_ATTR, rpc

        @rpc()
        async def my_rpc_func() -> str:
            return "hello"

        assert hasattr(my_rpc_func, RPC_ATTR)

    def test_rpc_default_options(self) -> None:
        """@rpc should have sensible defaults."""
        from framework_m.core.decorators import RPC_ATTR, rpc

        @rpc()
        async def my_rpc_func() -> str:
            return "hello"

        options = getattr(my_rpc_func, RPC_ATTR)
        assert options["permission"] is None
        assert options["allow_guest"] is False

    def test_rpc_custom_permission(self) -> None:
        """@rpc should accept custom permission."""
        from framework_m.core.decorators import RPC_ATTR, rpc

        @rpc(permission="send_email")
        async def send_email() -> bool:
            return True

        options = getattr(send_email, RPC_ATTR)
        assert options["permission"] == "send_email"

    def test_rpc_allow_guest(self) -> None:
        """@rpc should accept allow_guest option."""
        from framework_m.core.decorators import RPC_ATTR, rpc

        @rpc(allow_guest=True)
        async def public_func() -> str:
            return "public"

        options = getattr(public_func, RPC_ATTR)
        assert options["allow_guest"] is True

    def test_rpc_registers_in_registry(self) -> None:
        """@rpc should auto-register function in RpcRegistry."""
        from framework_m.core.decorators import rpc
        from framework_m.core.rpc_registry import RpcRegistry

        registry = RpcRegistry.get_instance()
        registry.reset()

        @rpc()
        async def auto_registered_func() -> str:
            return "registered"

        # Should be registered with full path
        paths = registry.list_functions()
        assert any("auto_registered_func" in p for p in paths)


class TestIsRpcFunction:
    """Tests for is_rpc_function helper."""

    def test_is_rpc_function_is_importable(self) -> None:
        """is_rpc_function should be importable."""
        from framework_m.core.decorators import is_rpc_function

        assert is_rpc_function is not None

    def test_returns_true_for_decorated(self) -> None:
        """is_rpc_function should return True for decorated functions."""
        from framework_m.core.decorators import is_rpc_function, rpc

        @rpc()
        async def decorated() -> None:
            pass

        assert is_rpc_function(decorated) is True

    def test_returns_false_for_undecorated(self) -> None:
        """is_rpc_function should return False for undecorated functions."""
        from framework_m.core.decorators import is_rpc_function

        async def undecorated() -> None:
            pass

        assert is_rpc_function(undecorated) is False


class TestGetRpcOptions:
    """Tests for get_rpc_options helper."""

    def test_get_rpc_options_is_importable(self) -> None:
        """get_rpc_options should be importable."""
        from framework_m.core.decorators import get_rpc_options

        assert get_rpc_options is not None

    def test_returns_options_for_decorated(self) -> None:
        """get_rpc_options should return options dict."""
        from framework_m.core.decorators import get_rpc_options, rpc

        @rpc(permission="test_perm")
        async def my_func() -> None:
            pass

        options = get_rpc_options(my_func)
        assert options["permission"] == "test_perm"

    def test_returns_empty_for_undecorated(self) -> None:
        """get_rpc_options should return empty dict for undecorated."""
        from framework_m.core.decorators import get_rpc_options

        async def undecorated() -> None:
            pass

        options = get_rpc_options(undecorated)
        assert options == {}
