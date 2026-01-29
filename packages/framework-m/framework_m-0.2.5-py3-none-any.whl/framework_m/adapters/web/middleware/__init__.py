"""Web middleware components for Framework M.

This module provides middleware for:
- Authentication
- Locale resolution (i18n)
- Request logging
- Performance monitoring
"""

# Import from auth_middleware.py
from framework_m.adapters.web.auth_middleware import (
    AuthMiddleware,
    create_auth_middleware,
)

# Import from this package
from framework_m.adapters.web.middleware.locale import (
    LocaleResolutionMiddleware,
    create_locale_middleware,
    provide_locale,
)

__all__ = [
    # Auth middleware
    "AuthMiddleware",
    # Locale middleware
    "LocaleResolutionMiddleware",
    "create_auth_middleware",
    "create_locale_middleware",
    "provide_locale",
]
