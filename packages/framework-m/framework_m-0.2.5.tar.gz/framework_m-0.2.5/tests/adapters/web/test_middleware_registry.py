"""Tests for Middleware Discovery.

TDD tests for the middleware discovery system that allows apps to register
and inject ASGI middleware with priority ordering.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import TYPE_CHECKING

import pytest
from litestar import Litestar, get
from litestar.testing import TestClient

from framework_m.adapters.web.middleware_registry import (
    MiddlewareConfig,
    MiddlewareRegistry,
    create_middleware_stack,
)

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Receive, Scope, Send


class TestMiddlewareConfig:
    """Test MiddlewareConfig dataclass."""

    def test_middleware_config_creation(self) -> None:
        """MiddlewareConfig should hold middleware class and options."""

        class DummyMiddleware:
            pass

        config = MiddlewareConfig(
            middleware_class=DummyMiddleware,
            name="dummy",
            priority=100,
        )
        assert config.middleware_class is DummyMiddleware
        assert config.name == "dummy"
        assert config.priority == 100

    def test_middleware_config_default_priority(self) -> None:
        """MiddlewareConfig should have default priority of 100."""

        class DummyMiddleware:
            pass

        config = MiddlewareConfig(
            middleware_class=DummyMiddleware,
            name="dummy",
        )
        assert config.priority == 100

    def test_middleware_config_with_kwargs(self) -> None:
        """MiddlewareConfig should support middleware kwargs."""

        class DummyMiddleware:
            pass

        config = MiddlewareConfig(
            middleware_class=DummyMiddleware,
            name="dummy",
            kwargs={"timeout": 30, "enabled": True},
        )
        assert config.kwargs == {"timeout": 30, "enabled": True}


class TestMiddlewareRegistry:
    """Test MiddlewareRegistry singleton."""

    def test_registry_is_singleton(self) -> None:
        """MiddlewareRegistry should be a singleton."""
        registry1 = MiddlewareRegistry()
        registry2 = MiddlewareRegistry()
        assert registry1 is registry2

    def test_register_middleware(self) -> None:
        """Should be able to register middleware."""
        registry = MiddlewareRegistry()
        registry.clear()

        class TestMiddleware:
            pass

        registry.register(
            middleware_class=TestMiddleware,
            name="test",
            priority=50,
        )

        middlewares = registry.list_middlewares()
        assert len(middlewares) == 1
        assert middlewares[0].name == "test"
        assert middlewares[0].priority == 50
        registry.clear()

    def test_middlewares_ordered_by_priority(self) -> None:
        """Middlewares should be returned ordered by priority (lowest first)."""
        registry = MiddlewareRegistry()
        registry.clear()

        class MiddlewareA:
            pass

        class MiddlewareB:
            pass

        class MiddlewareC:
            pass

        # Register out of order
        registry.register(MiddlewareB, name="b", priority=200)
        registry.register(MiddlewareC, name="c", priority=300)
        registry.register(MiddlewareA, name="a", priority=100)

        middlewares = registry.list_middlewares()
        names = [m.name for m in middlewares]
        assert names == ["a", "b", "c"]
        registry.clear()

    def test_register_with_kwargs(self) -> None:
        """Should be able to register middleware with kwargs."""
        registry = MiddlewareRegistry()
        registry.clear()

        class TestMiddleware:
            pass

        registry.register(
            middleware_class=TestMiddleware,
            name="test",
            kwargs={"rate_limit": 100},
        )

        middlewares = registry.list_middlewares()
        assert middlewares[0].kwargs == {"rate_limit": 100}
        registry.clear()

    def test_duplicate_name_raises_error(self) -> None:
        """Registering middleware with duplicate name should raise error."""
        registry = MiddlewareRegistry()
        registry.clear()

        class TestMiddleware:
            pass

        registry.register(TestMiddleware, name="duplicate")

        with pytest.raises(ValueError, match="already registered"):
            registry.register(TestMiddleware, name="duplicate")
        registry.clear()

    def test_get_middleware_by_name(self) -> None:
        """Should be able to get middleware config by name."""
        registry = MiddlewareRegistry()
        registry.clear()

        class TestMiddleware:
            pass

        registry.register(TestMiddleware, name="my_middleware", priority=150)

        config = registry.get("my_middleware")
        assert config is not None
        assert config.name == "my_middleware"
        assert config.priority == 150
        registry.clear()


class TestCreateMiddlewareStack:
    """Test the create_middleware_stack helper."""

    def test_creates_empty_list_when_no_middlewares(self) -> None:
        """Should return empty list when no middlewares registered."""
        registry = MiddlewareRegistry()
        registry.clear()

        stack = create_middleware_stack()
        assert stack == []

    def test_creates_define_middleware_instances(self) -> None:
        """Should create DefineMiddleware instances."""
        from litestar.middleware.base import DefineMiddleware

        from framework_m.adapters.web.middleware import AuthMiddleware

        registry = MiddlewareRegistry()
        registry.clear()

        registry.register(
            AuthMiddleware,
            name="auth",
            kwargs={"require_auth": False},
        )

        stack = create_middleware_stack()
        assert len(stack) == 1
        assert isinstance(stack[0], DefineMiddleware)
        registry.clear()


class TestMiddlewareDiscoveryIntegration:
    """Integration tests for middleware discovery with Litestar app."""

    def test_app_applies_registered_middlewares(self) -> None:
        """App should apply all registered middlewares."""
        from framework_m.adapters.web.middleware import AuthMiddleware

        registry = MiddlewareRegistry()
        registry.clear()

        # Register auth middleware with auth disabled
        registry.register(
            AuthMiddleware,
            name="auth",
            priority=100,
            kwargs={"require_auth": False},
        )

        @get("/test")
        async def test_handler() -> dict:
            return {"result": "ok"}

        stack = create_middleware_stack()
        app = Litestar(route_handlers=[test_handler], middleware=stack)

        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200
        registry.clear()

    def test_priority_affects_middleware_order(self) -> None:
        """Lower priority middlewares should run first (outer layer)."""
        registry = MiddlewareRegistry()
        registry.clear()

        execution_order: list[str] = []

        class OuterMiddleware:
            def __init__(self, app: "ASGIApp") -> None:  # type: ignore[name-defined]
                self.app = app

            async def __call__(
                self,
                scope: "Scope",
                receive: "Receive",
                send: "Send",  # type: ignore[name-defined]
            ) -> None:
                execution_order.append("outer")
                await self.app(scope, receive, send)

        class InnerMiddleware:
            def __init__(self, app: "ASGIApp") -> None:  # type: ignore[name-defined]
                self.app = app

            async def __call__(
                self,
                scope: "Scope",
                receive: "Receive",
                send: "Send",  # type: ignore[name-defined]
            ) -> None:
                execution_order.append("inner")
                await self.app(scope, receive, send)

        # Lower priority = runs first (outer layer)
        registry.register(OuterMiddleware, name="outer", priority=100)
        registry.register(InnerMiddleware, name="inner", priority=200)

        @get("/test")
        async def test_handler() -> dict:
            return {"result": "ok"}

        stack = create_middleware_stack()
        app = Litestar(route_handlers=[test_handler], middleware=stack)

        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200
            assert execution_order == ["outer", "inner"]
        registry.clear()
