"""Tests for Dependency Injection Container - Comprehensive coverage tests."""

from unittest.mock import MagicMock, patch

# =============================================================================
# Test: Container Import
# =============================================================================


class TestContainerImport:
    """Tests for Container import."""

    def test_import_container(self) -> None:
        """Container should be importable."""
        from framework_m.core.container import Container

        assert Container is not None

    def test_import_load_overrides(self) -> None:
        """load_overrides should be importable."""
        from framework_m.core.container import load_overrides

        assert load_overrides is not None

    def test_exports(self) -> None:
        """container module should export expected items."""
        from framework_m.core import container

        assert "Container" in container.__all__
        assert "load_overrides" in container.__all__


# =============================================================================
# Test: Container Instantiation
# =============================================================================


class TestContainerInstantiation:
    """Tests for Container instantiation."""

    def test_create_container(self) -> None:
        """Container should be instantiable."""
        from framework_m.core.container import Container

        container = Container()

        assert container is not None

    def test_container_has_config(self) -> None:
        """Container should have config provider."""
        from framework_m.core.container import Container

        container = Container()

        assert hasattr(container, "config")

    def test_container_has_connection_factory(self) -> None:
        """Container should have connection_factory provider."""
        from framework_m.core.container import Container

        container = Container()

        assert hasattr(container, "connection_factory")

    def test_container_has_session_factory(self) -> None:
        """Container should have session_factory provider."""
        from framework_m.core.container import Container

        container = Container()

        assert hasattr(container, "session_factory")

    def test_container_has_unit_of_work(self) -> None:
        """Container should have unit_of_work provider."""
        from framework_m.core.container import Container

        container = Container()

        assert hasattr(container, "unit_of_work")

    def test_container_has_event_bus(self) -> None:
        """Container should have event_bus provider."""
        from framework_m.core.container import Container

        container = Container()

        assert hasattr(container, "event_bus")


# =============================================================================
# Test: Container Config
# =============================================================================


class TestContainerConfig:
    """Tests for Container config provider."""

    def test_config_from_dict(self) -> None:
        """Container config should load from dict."""
        from framework_m.core.container import Container

        container = Container()
        container.config.from_dict({"database_url": "sqlite:///:memory:"})

        assert container.config.database_url() == "sqlite:///:memory:"

    def test_config_nested_values(self) -> None:
        """Container config should support nested values."""
        from framework_m.core.container import Container

        container = Container()
        container.config.from_dict({"app": {"debug": True, "name": "test"}})

        assert container.config.app.debug() is True
        assert container.config.app.name() == "test"


# =============================================================================
# Test: Container Wiring
# =============================================================================


class TestContainerWiring:
    """Tests for Container wiring configuration."""

    def test_has_wiring_config(self) -> None:
        """Container should have wiring_config."""
        from framework_m.core.container import Container

        assert hasattr(Container, "wiring_config")


# =============================================================================
# Test: load_overrides
# =============================================================================


class TestLoadOverrides:
    """Tests for load_overrides function."""

    def test_load_overrides_with_no_entrypoints(self) -> None:
        """load_overrides should return 0 when no entrypoints."""
        from framework_m.core.container import Container, load_overrides

        container = Container()

        with patch("framework_m.core.container.entry_points") as mock_eps:
            mock_eps.return_value = []

            count = load_overrides(container)

            assert count == 0

    def test_load_overrides_applies_override(self) -> None:
        """load_overrides should apply matching overrides."""
        from framework_m.core.container import Container, load_overrides

        container = Container()

        mock_ep = MagicMock()
        mock_ep.name = "event_bus"
        mock_ep.load.return_value = MagicMock()

        with patch("framework_m.core.container.entry_points") as mock_eps:
            mock_eps.return_value = [mock_ep]

            count = load_overrides(container)

            assert count == 1

    def test_load_overrides_ignores_unknown_provider(self) -> None:
        """load_overrides should skip unknown provider names."""
        from framework_m.core.container import Container, load_overrides

        container = Container()

        mock_ep = MagicMock()
        mock_ep.name = "nonexistent_provider"

        with patch("framework_m.core.container.entry_points") as mock_eps:
            mock_eps.return_value = [mock_ep]

            count = load_overrides(container)

            assert count == 0

    def test_load_overrides_handles_load_error(self) -> None:
        """load_overrides should handle entrypoint load errors."""
        from framework_m.core.container import Container, load_overrides

        container = Container()

        mock_ep = MagicMock()
        mock_ep.name = "event_bus"
        mock_ep.load.side_effect = Exception("Load error")

        with patch("framework_m.core.container.entry_points") as mock_eps:
            mock_eps.return_value = [mock_ep]

            count = load_overrides(container)

            assert count == 0

    def test_load_overrides_custom_group(self) -> None:
        """load_overrides should use custom group."""
        from framework_m.core.container import Container, load_overrides

        container = Container()

        with patch("framework_m.core.container.entry_points") as mock_eps:
            mock_eps.return_value = []

            load_overrides(container, group="custom.group")

            mock_eps.assert_called_once_with(group="custom.group")
