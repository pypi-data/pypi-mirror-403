"""Studio CLI Command - Admin Interface Server.

This module provides the `m studio` CLI command for running
Framework M Studio - the admin and development interface.

Usage:
    m studio                # Start Studio on default port (9000)
    m studio --port 9001    # Custom port
    m studio --reload       # Enable auto-reload
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import cyclopts

# Default Studio configuration
DEFAULT_STUDIO_PORT = 9000
DEFAULT_STUDIO_APP = "framework_m_studio.app:app"


def get_studio_app() -> str:
    """Get the Studio app path.

    Returns:
        Studio app path in module:attribute format
    """
    return DEFAULT_STUDIO_APP


def get_pythonpath() -> str:
    """Get PYTHONPATH with src/ directory included.

    Returns:
        PYTHONPATH string with src/ prepended
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


def build_studio_command(
    host: str = "127.0.0.1",
    port: int = DEFAULT_STUDIO_PORT,
    reload: bool = False,
    log_level: str | None = None,
) -> list[str]:
    """Build the uvicorn command line for Studio.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
        log_level: Log level (debug, info, warning, error)

    Returns:
        Complete command as list of strings
    """
    app_path = get_studio_app()
    cmd = [sys.executable, "-m", "uvicorn", app_path]

    cmd.extend(["--host", host])
    cmd.extend(["--port", str(port)])

    if reload:
        cmd.append("--reload")

    if log_level:
        cmd.extend(["--log-level", log_level])

    return cmd


def studio_command(
    host: Annotated[
        str,
        cyclopts.Parameter(name="--host", help="Host to bind to"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        cyclopts.Parameter(name="--port", help="Port to bind to"),
    ] = DEFAULT_STUDIO_PORT,
    reload: Annotated[
        bool,
        cyclopts.Parameter(name="--reload", help="Enable auto-reload for development"),
    ] = False,
    log_level: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--log-level", help="Log level (debug, info, warning, error)"
        ),
    ] = None,
) -> None:
    """Start Framework M Studio - the admin interface.

    Studio provides a web-based admin UI for:
    - Browsing and editing DocTypes
    - Monitoring jobs and events
    - Running queries and reports

    Examples:
        m studio                    # Default port 9000
        m studio --port 9001        # Custom port
        m studio --reload           # Dev mode with auto-reload
    """
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = get_pythonpath()

    # Build command
    cmd = build_studio_command(
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )

    print("Starting Framework M Studio")
    print("=" * 40)
    print(f"  URL: http://{host}:{port}")
    print(f"  Reload: {reload}")
    print()

    # Execute uvicorn
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        raise SystemExit(e.returncode) from e
    except KeyboardInterrupt:
        print("\nStudio stopped.")


__all__ = [
    "DEFAULT_STUDIO_APP",
    "DEFAULT_STUDIO_PORT",
    "build_studio_command",
    "get_studio_app",
    "studio_command",
]
