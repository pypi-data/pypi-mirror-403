"""Start CLI Command - Development Server (Uvicorn Relay).

This module provides the `m start` CLI command for starting
the development server using uvicorn as the underlying server.

Usage:
    m start                         # Start with defaults
    m start --port 8080             # Custom port
    m start --reload --workers 4    # With reload and workers
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import cyclopts

# Default app path pattern
DEFAULT_APP_PATH = "app:app"

# Common app patterns to search for
APP_PATTERNS = [
    "app:app",
    "app.main:app",
    "main:app",
    "src.app:app",
    "src.app.main:app",
]


def find_app(explicit_app: str | None = None) -> str:
    """Find the Litestar app to run.

    Args:
        explicit_app: Explicit app path if provided

    Returns:
        App path in module:attribute format

    Example:
        >>> find_app("myapp.main:app")
        'myapp.main:app'
        >>> find_app(None)  # Auto-detect
        'app:app'
    """
    if explicit_app:
        return explicit_app

    # Try to find app in common locations
    cwd = Path.cwd()

    # Check for app.py in current directory
    if (cwd / "app.py").exists():
        return "app:app"

    # Check for app/__init__.py
    if (cwd / "app" / "__init__.py").exists():
        return "app:app"

    # Check for src/app structure
    if (cwd / "src" / "app" / "__init__.py").exists():
        return "src.app:app"

    # Check for main.py
    if (cwd / "main.py").exists():
        return "main:app"

    # Default fallback
    return DEFAULT_APP_PATH


def get_pythonpath() -> str:
    """Get PYTHONPATH with src/ directory included.

    Returns:
        PYTHONPATH string with src/ prepended

    Example:
        >>> os.environ["PYTHONPATH"] = "/existing"
        >>> get_pythonpath()
        'src:/existing'
    """
    cwd = Path.cwd()
    src_path = cwd / "src"

    paths = []

    # Add src/ if it exists
    if src_path.exists():
        paths.append(str(src_path))

    # Add current directory
    paths.append(str(cwd))

    # Preserve existing PYTHONPATH
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        paths.append(existing)

    return os.pathsep.join(paths)


def build_uvicorn_command(
    app: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
    workers: int | None = None,
    log_level: str | None = None,
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build the uvicorn command line.

    Args:
        app: App path in module:attribute format
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
        workers: Number of workers
        log_level: Log level (debug, info, warning, error)
        extra_args: Additional arguments to pass to uvicorn

    Returns:
        Complete command as list of strings
    """
    cmd = [sys.executable, "-m", "uvicorn", app]

    cmd.extend(["--host", host])
    cmd.extend(["--port", str(port)])

    if reload:
        cmd.append("--reload")

    if workers is not None and workers > 1:
        cmd.extend(["--workers", str(workers)])

    if log_level:
        cmd.extend(["--log-level", log_level])

    # Add any extra arguments
    cmd.extend(extra_args)

    return cmd


def start_command(
    app: Annotated[
        str | None,
        cyclopts.Parameter(name="--app", help="App path (module:attribute format)"),
    ] = None,
    host: Annotated[
        str,
        cyclopts.Parameter(name="--host", help="Host to bind to"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        cyclopts.Parameter(name="--port", help="Port to bind to"),
    ] = 8000,
    reload: Annotated[
        bool,
        cyclopts.Parameter(name="--reload", help="Enable auto-reload for development"),
    ] = False,
    workers: Annotated[
        int | None,
        cyclopts.Parameter(name="--workers", help="Number of worker processes"),
    ] = None,
    log_level: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--log-level", help="Log level (debug, info, warning, error)"
        ),
    ] = None,
) -> None:
    """Start the development server (uvicorn relay).

    Starts a uvicorn server with the specified configuration.
    Auto-detects the Litestar app if not explicitly provided.

    Examples:
        m start                           # Use defaults
        m start --port 8080               # Custom port
        m start --reload --log-level debug
        m start --app myapp.main:app      # Explicit app
    """
    # Find or use explicit app
    app_path = find_app(app)

    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = get_pythonpath()

    # Build command
    cmd = build_uvicorn_command(
        app=app_path,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )

    print(f"Starting server: {app_path}")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Reload: {reload}")
    if workers:
        print(f"  Workers: {workers}")
    print()

    # Execute uvicorn
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        raise SystemExit(e.returncode) from e
    except KeyboardInterrupt:
        print("\nServer stopped.")


__all__ = [
    "DEFAULT_APP_PATH",
    "build_uvicorn_command",
    "find_app",
    "get_pythonpath",
    "start_command",
]
