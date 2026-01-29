"""Architecture tests to ensure clean package separation.

These tests enforce that the `core` package does not import from `adapters`,
which is required for the future package split (Phase 11: MX Pattern).
"""

import ast
import importlib.util
from pathlib import Path

import pytest


def get_package_path(package_name: str) -> Path:
    """Get the filesystem path for a package."""
    spec = importlib.util.find_spec(package_name)
    if spec is None or spec.origin is None:
        pytest.skip(f"Package {package_name} not found")
    return Path(spec.origin).parent


def get_all_python_files(directory: Path) -> list[Path]:
    """Get all Python files in a directory recursively."""
    return list(directory.rglob("*.py"))


def get_imports_from_file(filepath: Path) -> list[str]:
    """Extract all import statements from a Python file."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


class TestCoreDoesNotImportAdapters:
    """Ensure core package has no dependency on adapters.

    This is critical for the future package split where:
    - framework-m-core: Pure protocols, no concrete implementations
    - framework-m-standard: SQLAlchemy and other adapters

    If core imports adapters, the split becomes impossible without refactoring.
    """

    def test_core_interfaces_do_not_import_adapters(self):
        """Core interfaces should be pure protocols with no adapter deps."""
        core_path = get_package_path("framework_m.core")
        interfaces_path = core_path / "interfaces"

        if not interfaces_path.exists():
            pytest.skip("interfaces directory not found")

        violations = []
        for py_file in get_all_python_files(interfaces_path):
            imports = get_imports_from_file(py_file)
            for imp in imports:
                if "framework_m.adapters" in imp:
                    violations.append(f"{py_file.name}: imports {imp}")

        assert not violations, (
            "Core interfaces must not import from adapters!\n"
            "Violations:\n" + "\n".join(violations)
        )

    def test_core_domain_does_not_import_adapters(self):
        """Core domain models should be pure with no adapter deps."""
        core_path = get_package_path("framework_m.core")
        domain_path = core_path / "domain"

        if not domain_path.exists():
            pytest.skip("domain directory not found")

        violations = []
        for py_file in get_all_python_files(domain_path):
            imports = get_imports_from_file(py_file)
            for imp in imports:
                if "framework_m.adapters" in imp:
                    violations.append(f"{py_file.name}: imports {imp}")

        assert not violations, (
            "Core domain must not import from adapters!\n"
            "Violations:\n" + "\n".join(violations)
        )

    def test_core_does_not_import_sqlalchemy(self):
        """Core should not have direct SQLAlchemy dependency.

        SQLAlchemy types should only appear in adapters.
        Core uses abstract types (e.g., `Any` for session).
        """
        core_path = get_package_path("framework_m.core")

        violations = []
        for py_file in get_all_python_files(core_path):
            imports = get_imports_from_file(py_file)
            for imp in imports:
                if imp.startswith("sqlalchemy"):
                    violations.append(f"{py_file.name}: imports {imp}")

        assert not violations, (
            "Core should not import SQLAlchemy directly!\n"
            "Use abstract types in protocols.\n"
            "Violations:\n" + "\n".join(violations)
        )


class TestAdaptersImplementProtocols:
    """Ensure adapters properly implement core protocols.

    This validates the Ports & Adapters architecture.
    """

    def test_adapters_import_from_core(self):
        """Adapters should import protocols from core."""
        adapters_path = get_package_path("framework_m.adapters")

        # At least some adapter files should import from core
        imports_core = False
        for py_file in get_all_python_files(adapters_path):
            imports = get_imports_from_file(py_file)
            for imp in imports:
                if "framework_m.core" in imp:
                    imports_core = True
                    break
            if imports_core:
                break

        assert imports_core, (
            "Adapters should import protocols from core.interfaces. "
            "This validates the Ports & Adapters pattern."
        )
