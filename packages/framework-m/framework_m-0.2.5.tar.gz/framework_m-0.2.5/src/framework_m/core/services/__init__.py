"""Services - High-level business services for Framework M.

This package contains service classes that provide clean abstractions
over the underlying protocols and adapters.

Services:
- UserManager: User management operations (get, authenticate, create)
"""

from framework_m.core.services.user_manager import UserManager

__all__ = ["UserManager"]
