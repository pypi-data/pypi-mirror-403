"""Framework M CLI - Main entry point.

This module provides the main CLI application for Framework M.
It includes core commands and supports plugin extensibility via entry points.

Entry Point Extension:
    Apps can register commands in pyproject.toml:
    [project.entry-points."framework_m.cli_commands"]
    studio = "my_app.cli:studio_app"
"""

from __future__ import annotations

from typing import Annotated

import cyclopts

from framework_m import __version__
from framework_m.cli.build import build_command, build_docker_command
from framework_m.cli.config import config_set_command, config_show_command
from framework_m.cli.jobs import job_app
from framework_m.cli.migrate import migrate_app
from framework_m.cli.new import new_app_command, new_doctype_command
from framework_m.cli.plugin_loader import load_plugins
from framework_m.cli.quality import (
    format_command,
    lint_command,
    test_command,
    typecheck_command,
)
from framework_m.cli.start import start_command
from framework_m.cli.utility import console_command, info_command, routes_command
from framework_m.cli.worker import worker_command

app = cyclopts.App(
    name="m",
    help="Framework M CLI - A modern, metadata-driven business application framework",
    version=__version__,
)

# Register sub-apps
app.command(migrate_app, name="migrate")
app.command(job_app, name="job")

# Register start command
app.command(start_command, name="start")

# Note: studio command is registered by framework-m-studio plugin if installed
# This allows the full Studio (with DocType APIs) to take precedence

# Register new:doctype command
app.command(new_doctype_command, name="new:doctype")

# Register new:app command
app.command(new_app_command, name="new:app")

# Register quality commands
app.command(test_command, name="test")
app.command(lint_command, name="lint")
app.command(format_command, name="format")
app.command(typecheck_command, name="typecheck")

# Register config commands
app.command(config_show_command, name="config:show")
app.command(config_set_command, name="config:set")

# Register utility commands
app.command(console_command, name="console")
app.command(info_command, name="info")
app.command(routes_command, name="routes")

# Register build commands
app.command(build_command, name="build")
app.command(build_docker_command, name="build:docker")

# Load plugins from entry points (3rd-party extensibility)
load_plugins(app)


@app.command
def worker(
    concurrency: Annotated[
        int,
        cyclopts.Parameter(name="--concurrency", help="Number of concurrent workers"),
    ] = 4,
    verbose: Annotated[
        bool, cyclopts.Parameter(name="--verbose", help="Verbose output")
    ] = False,
) -> None:
    """Start the Taskiq worker for processing background jobs."""
    worker_command(concurrency=concurrency, verbose=verbose)


@app.default
def default() -> None:
    """Show help when no command is provided."""
    app.help_print()


if __name__ == "__main__":
    app()
