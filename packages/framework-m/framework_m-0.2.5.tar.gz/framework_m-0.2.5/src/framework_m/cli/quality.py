"""Testing & Quality CLI Commands.

This module provides CLI commands for testing and code quality:
- m test: Run pytest
- m lint: Run ruff check --fix
- m format: Run ruff format
- m typecheck: Run mypy

Usage:
    m test -k "user" -vv      # Run tests with filter
    m lint                    # Check and fix lint issues
    m format                  # Format code
    m typecheck               # Type check code
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import cyclopts


def get_pythonpath() -> str:
    """Get PYTHONPATH with src/ directory included."""
    cwd = Path.cwd()
    src_path = cwd / "src"

    paths = []
    if src_path.exists():
        paths.append(str(src_path))
    paths.append(str(cwd))

    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        paths.append(existing)

    return os.pathsep.join(paths)


# =============================================================================
# Build Commands
# =============================================================================


def build_pytest_command(
    verbose: bool = False,
    coverage: bool = False,
    filter_expr: str | None = None,
    path: str = ".",
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build the pytest command line."""
    cmd = [sys.executable, "-m", "pytest", path]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.append("--cov")

    if filter_expr:
        cmd.extend(["-k", filter_expr])

    cmd.extend(extra_args)
    return cmd


def build_ruff_check_command(
    fix: bool = True,
    path: str = ".",
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build the ruff check command line."""
    cmd = [sys.executable, "-m", "ruff", "check", path]

    if fix:
        cmd.append("--fix")

    cmd.extend(extra_args)
    return cmd


def build_ruff_format_command(
    check: bool = False,
    path: str = ".",
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build the ruff format command line."""
    cmd = [sys.executable, "-m", "ruff", "format", path]

    if check:
        cmd.append("--check")

    cmd.extend(extra_args)
    return cmd


def build_mypy_command(
    path: str = ".",
    strict: bool = False,
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build the mypy command line."""
    cmd = [sys.executable, "-m", "mypy", path]

    if strict:
        cmd.append("--strict")

    cmd.extend(extra_args)
    return cmd


# =============================================================================
# CLI Commands
# =============================================================================


def test_command(
    path: Annotated[
        str,
        cyclopts.Parameter(help="Path to test (default: current directory)"),
    ] = ".",
    verbose: Annotated[
        bool,
        cyclopts.Parameter(name="--verbose", help="Verbose output"),
    ] = False,
    coverage: Annotated[
        bool,
        cyclopts.Parameter(name="--coverage", help="Run with coverage"),
    ] = False,
    filter_expr: Annotated[
        str | None,
        cyclopts.Parameter(name="-k", help="Filter expression"),
    ] = None,
) -> None:
    """Run tests using pytest.

    A convenient wrapper around pytest that sets up PYTHONPATH
    and provides common options.

    Examples:
        m test                      # Run all tests
        m test -k "user"            # Filter tests
        m test --verbose --coverage # Verbose with coverage
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = get_pythonpath()

    cmd = build_pytest_command(
        verbose=verbose,
        coverage=coverage,
        filter_expr=filter_expr,
        path=path,
    )

    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, env=env)
        raise SystemExit(result.returncode)
    except KeyboardInterrupt:
        print("\nTests interrupted.")
        raise SystemExit(130) from None


def lint_command(
    path: Annotated[
        str,
        cyclopts.Parameter(help="Path to lint (default: current directory)"),
    ] = ".",
    fix: Annotated[
        bool,
        cyclopts.Parameter(name="--fix", help="Auto-fix issues"),
    ] = True,
) -> None:
    """Run linting using ruff check.

    Checks code for linting issues and auto-fixes them by default.

    Examples:
        m lint              # Check and fix
        m lint --no-fix     # Check only
    """
    cmd = build_ruff_check_command(fix=fix, path=path)

    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd)
        raise SystemExit(result.returncode)
    except KeyboardInterrupt:
        print("\nLinting interrupted.")
        raise SystemExit(130) from None


def format_command(
    path: Annotated[
        str,
        cyclopts.Parameter(help="Path to format (default: current directory)"),
    ] = ".",
    check: Annotated[
        bool,
        cyclopts.Parameter(name="--check", help="Check only, don't format"),
    ] = False,
) -> None:
    """Format code using ruff format.

    Formats code to consistent style.

    Examples:
        m format            # Format code
        m format --check    # Check without formatting
    """
    cmd = build_ruff_format_command(check=check, path=path)

    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd)
        raise SystemExit(result.returncode)
    except KeyboardInterrupt:
        print("\nFormatting interrupted.")
        raise SystemExit(130) from None


def typecheck_command(
    path: Annotated[
        str,
        cyclopts.Parameter(help="Path to check (default: current directory)"),
    ] = ".",
    strict: Annotated[
        bool,
        cyclopts.Parameter(name="--strict", help="Enable strict mode"),
    ] = False,
) -> None:
    """Run type checking using mypy.

    Type checks Python code for type errors.

    Examples:
        m typecheck             # Check types
        m typecheck --strict    # Strict mode
    """
    cmd = build_mypy_command(path=path, strict=strict)

    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd)
        raise SystemExit(result.returncode)
    except KeyboardInterrupt:
        print("\nType checking interrupted.")
        raise SystemExit(130) from None


__all__ = [
    "build_mypy_command",
    "build_pytest_command",
    "build_ruff_check_command",
    "build_ruff_format_command",
    "format_command",
    "lint_command",
    "test_command",
    "typecheck_command",
]
