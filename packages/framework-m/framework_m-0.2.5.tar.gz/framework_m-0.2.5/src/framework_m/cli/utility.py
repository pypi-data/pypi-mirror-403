"""Utility CLI Commands.

This module provides utility CLI commands for Framework M:
- m console: Interactive Python/IPython shell
- m info: Show system information
- m routes: Show registered routes

Usage:
    m console                # Start IPython shell
    m info                   # Show versions
    m routes                 # List all routes
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import cyclopts


def get_python_version() -> str:
    """Get Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_framework_version() -> str:
    """Get Framework M version."""
    from framework_m import __version__

    return __version__


def check_ipython_installed() -> bool:
    """Check if IPython is installed."""
    import shutil

    return shutil.which("ipython") is not None


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
# CLI Commands
# =============================================================================


def console_command(
    ipython: Annotated[
        bool,
        cyclopts.Parameter(name="--ipython", help="Use IPython if available"),
    ] = True,
) -> None:
    """Start an interactive Python console.

    Launches an interactive Python shell with Framework M pre-imports.
    Uses IPython if available, otherwise falls back to Python asyncio REPL.

    Pre-imported:
    - app: The Litestar application
    - DocType registry
    - Database session helpers

    Examples:
        m console              # Start shell
        m console --no-ipython # Force plain Python
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = get_pythonpath()

    # Startup code to pre-import useful items
    startup_code = """
import asyncio
try:
    from framework_m import __version__
    print(f"Framework M v{__version__}")
except:
    pass
print("Use 'await' for async operations")
print()
"""

    if ipython and check_ipython_installed():
        # Use IPython
        cmd = [
            "ipython",
            "--no-banner",
            "-i",
            "-c",
            startup_code,
        ]
    else:
        # Use Python asyncio REPL
        cmd = [
            sys.executable,
            "-m",
            "asyncio",
        ]
        print("Starting Python asyncio REPL...")
        print(startup_code)

    import contextlib

    with contextlib.suppress(KeyboardInterrupt):
        subprocess.run(cmd, env=env)


def info_command(
    verbose: Annotated[
        bool,
        cyclopts.Parameter(name="--verbose", help="Show detailed information"),
    ] = False,
) -> None:
    """Show system information.

    Displays versions of Framework M, Python, and related services.

    Examples:
        m info           # Basic info
        m info --verbose # Detailed info
    """
    print("Framework M System Information")
    print("=" * 40)
    print()

    # Framework version
    print(f"  Framework M: v{get_framework_version()}")
    print(f"  Python:      v{get_python_version()}")
    print()

    if verbose:
        # Platform info
        import platform

        print("Platform:")
        print(f"  OS:          {platform.system()} {platform.release()}")
        print(f"  Machine:     {platform.machine()}")
        print()

        # Check for optional services
        print("Services:")

        # Check PostgreSQL
        try:
            result = subprocess.run(
                ["psql", "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                pg_version = result.stdout.strip().split()[-1]
                print(f"  PostgreSQL:  v{pg_version}")
        except FileNotFoundError:
            print("  PostgreSQL:  (not found)")

        # Check Redis
        try:
            result = subprocess.run(
                ["redis-server", "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                redis_info = result.stdout.strip()
                if "v=" in redis_info:
                    redis_version = redis_info.split("v=")[1].split()[0]
                    print(f"  Redis:       v{redis_version}")
        except FileNotFoundError:
            print("  Redis:       (not found)")

        # Check NATS
        try:
            result = subprocess.run(
                ["nats-server", "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"  NATS:        {result.stdout.strip()}")
        except FileNotFoundError:
            print("  NATS:        (not found)")

        print()


def routes_command(
    app_path: Annotated[
        str | None,
        cyclopts.Parameter(name="--app", help="App path (module:attribute)"),
    ] = None,
) -> None:
    """Show registered routes.

    Lists all HTTP routes registered with the Litestar application.

    Examples:
        m routes                      # Auto-detect app
        m routes --app myapp.main:app # Explicit app
    """
    print("Route listing requires a running application.")
    print()
    print("To see routes, start the server and visit:")
    print("  http://localhost:8000/schema/openapi.json")
    print()
    print("Or use the built-in docs:")
    print("  http://localhost:8000/schema/swagger")
    print("  http://localhost:8000/schema/redoc")


__all__ = [
    "check_ipython_installed",
    "console_command",
    "get_framework_version",
    "get_python_version",
    "get_pythonpath",
    "info_command",
    "routes_command",
]
