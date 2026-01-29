"""Dependency Injection Container.

This module provides the central DI container for Framework M.
It uses dependency-injector for managing dependencies and supports
configuration, singletons, factories, and automatic wiring.

Example:
    from framework_m.core.container import Container

    container = Container()
    container.config.from_dict({"database_url": "sqlite:///:memory:"})

    # Access services
    db_url = container.config.database_url()

Configuration:
    # From Pydantic settings
    container.config.from_pydantic(Settings())

    # From environment variables with prefix
    container.config.from_env("APP", as_=str)

    # From dictionary
    container.config.from_dict({"key": "value"})

Wiring:
    from dependency_injector.wiring import inject, Provide

    @inject
    async def my_function(
        repo: RepositoryProtocol = Provide[Container.repository]
    ):
        # repo is automatically injected
        pass

Entrypoint Overrides:
    # In app's pyproject.toml:
    [project.entry-points."framework_m.overrides"]
    repository = "my_app.custom:CustomRepository"
"""

from importlib.metadata import entry_points
from typing import Any

from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
    """
    Central dependency injection container for Framework M.

    This container manages all application dependencies and supports:
    - Configuration from Pydantic settings, dicts, or env vars
    - Singleton services (single instance)
    - Factory services (new instance each call)
    - Resource services (with lifecycle management)
    - Automatic wiring with @inject decorator

    Provider Types:
        - Singleton: One instance shared across the app
        - Factory: New instance each time
        - Resource: For connections with open/close lifecycle
        - Callable: For functions
        - Dependency: For protocol injection

    Example:
        container = Container()
        container.config.from_pydantic(settings)

        # Override for testing
        container.repository.override(MockRepository())
    """

    # Wiring configuration - modules to wire automatically
    wiring_config = containers.WiringConfiguration(
        modules=[
            # Will be populated as adapters are created
            # "framework_m.adapters.api",
            # "framework_m.adapters.db",
        ]
    )

    # Configuration provider
    # Can be loaded from dict, pydantic settings, or env vars
    config = providers.Configuration()

    # ==========================================================================
    # Core Services
    # ==========================================================================

    # Connection Factory - manages database engines
    # Usage: container.connection_factory()
    connection_factory: providers.Provider[Any] = providers.Singleton(
        "framework_m.adapters.db.connection.ConnectionFactory"
    )

    # Session Factory - creates async database sessions
    # Usage: container.session_factory()
    session_factory: providers.Provider[Any] = providers.Singleton(
        "framework_m.adapters.db.session.SessionFactory"
    )

    # Unit of Work Factory - creates transaction context managers
    # Usage: async with container.unit_of_work()() as uow: ...
    unit_of_work: providers.Provider[Any] = providers.Factory(
        "framework_m.core.unit_of_work.UnitOfWork",
    )

    # Event Bus - pub/sub for domain events (defaults to in-memory)
    # Usage: container.event_bus()
    event_bus: providers.Provider[Any] = providers.Singleton(
        "framework_m.adapters.events.inmemory_event_bus.InMemoryEventBus"
    )


def load_overrides(container: Container, group: str = "framework_m.overrides") -> int:
    """
    Load provider overrides from package entrypoints.

    Scans the specified entrypoint group for override definitions
    and applies them to the container. This allows applications
    to customize framework behavior without modifying core code.

    Args:
        container: The DI container to apply overrides to
        group: The entrypoint group name to scan

    Returns:
        Number of overrides applied

    Example:
        In app's pyproject.toml:
        ```toml
        [project.entry-points."framework_m.overrides"]
        repository = "my_app.adapters:CustomRepository"
        event_bus = "my_app.events:CustomEventBus"
        ```

        Then in app initialization:
        ```python
        container = Container()
        load_overrides(container)
        ```
    """
    count = 0

    # Python 3.12+ entry_points API - use group parameter directly
    override_eps = entry_points(group=group)

    for ep in override_eps:
        provider_name = ep.name
        if hasattr(container, provider_name):
            try:
                override_class = ep.load()
                provider = getattr(container, provider_name)
                provider.override(override_class)
                count += 1
            except Exception:
                # Log warning in production, skip for now
                pass

    return count


def load_app_containers(group: str = "framework_m.containers") -> dict[str, type]:
    """
    Discover app-defined containers from entrypoints.

    Scans the specified entrypoint group for app container classes.
    This allows applications to register their own DI containers
    with custom protocols/ports.

    Args:
        group: The entrypoint group name to scan

    Returns:
        Dictionary mapping container name to container class

    Example:
        In app's pyproject.toml:
        ```toml
        [project.entry-points."framework_m.containers"]
        ecommerce = "ecommerce_app.container:EcommerceContainer"
        ```

        Then in framework initialization:
        ```python
        app_containers = load_app_containers()
        # {'ecommerce': EcommerceContainer}
        ```
    """
    containers_dict: dict[str, type] = {}

    # Python 3.12+ entry_points API
    container_eps = entry_points(group=group)

    for ep in container_eps:
        try:
            container_class = ep.load()
            containers_dict[ep.name] = container_class
        except Exception:
            # Skip invalid entrypoints (log warning in production)
            pass

    return containers_dict


def register_app_container(
    main_container: Container, name: str, app_container: Any
) -> None:
    """
    Register an app-defined container with the main framework container.

    Dynamically adds the app container as an attribute of the main container,
    making it accessible throughout the application.

    Args:
        main_container: The main framework Container instance
        name: The name to register the app container under
        app_container: The app container instance to register

    Example:
        ```python
        main_container = Container()
        ecommerce = EcommerceContainer()

        register_app_container(main_container, "ecommerce", ecommerce)

        # Now accessible as:
        payment_gateway = main_container.ecommerce.payment_gateway()
        ```
    """
    setattr(main_container, name, app_container)


def auto_load_app_containers(
    main_container: Container, group: str = "framework_m.containers"
) -> int:
    """
    Automatically discover and register all app-defined containers.

    Combines load_app_containers and register_app_container to provide
    a one-step solution for loading all app containers from entrypoints.

    Args:
        main_container: The main framework Container instance
        group: The entrypoint group name to scan

    Returns:
        Number of app containers registered

    Example:
        ```python
        container = Container()
        count = auto_load_app_containers(container)
        print(f"Loaded {count} app containers")

        # All app containers are now registered
        payment = container.ecommerce.payment_gateway()
        ```
    """
    containers_dict = load_app_containers(group)

    for name, container_class in containers_dict.items():
        # Instantiate the container
        app_container = container_class()
        register_app_container(main_container, name, app_container)

    return len(containers_dict)


def get_app_container_names(main_container: Container) -> list[str]:
    """
    Get list of registered app container names.

    Returns the names of all app containers that have been registered
    with the main container, excluding framework providers.

    Args:
        main_container: The main framework Container instance

    Returns:
        List of app container names

    Example:
        ```python
        container = Container()
        auto_load_app_containers(container)

        names = get_app_container_names(container)
        # ['ecommerce', 'marketing', ...]
        ```
    """
    # Framework providers are defined on the Container class
    framework_attrs = {
        "config",
        "connection_factory",
        "session_factory",
        "unit_of_work",
        "event_bus",
        "wiring_config",
    }

    # Get all attributes that are not framework providers
    app_containers = [
        name
        for name in dir(main_container)
        if not name.startswith("_")
        and name not in framework_attrs
        and not callable(getattr(type(main_container), name, None))
    ]

    return app_containers


__all__ = [
    "Container",
    "auto_load_app_containers",
    "get_app_container_names",
    "load_app_containers",
    "load_overrides",
    "register_app_container",
]
