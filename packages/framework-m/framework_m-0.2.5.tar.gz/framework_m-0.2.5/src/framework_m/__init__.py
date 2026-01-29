"""Framework M - A modern, metadata-driven business application framework."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("framework-m")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

from framework_m.core.domain.base_doctype import BaseDocType as DocType
from framework_m.core.domain.base_doctype import Field

__all__ = ["DocType", "Field", "__version__"]
