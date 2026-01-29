"""Build CLI Commands.

This module provides CLI commands for building Framework M applications:
- m build: Build frontend assets (placeholder for Phase 09)
- m build:docker: Build Docker image

Usage:
    m build                      # Build frontend
    m build:docker               # Build Docker image
    m build:docker --tag app:v1  # Custom tag
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import cyclopts

from framework_m.cli.config import load_config


def get_default_image_name() -> str:
    """Get default Docker image name from config or project name.

    Returns:
        Default image name
    """
    config = load_config()
    framework_config = config.get("framework", {})

    name = framework_config.get("name", "framework-m-app")
    version = framework_config.get("version", "latest")

    return f"{name}:{version}"


def build_docker_cmd(
    tag: str,
    dockerfile: str = "Dockerfile",
    context: str = ".",
    no_cache: bool = False,
    build_args: list[str] | None = None,
) -> list[str]:
    """Build the docker build command.

    Args:
        tag: Image tag
        dockerfile: Path to Dockerfile
        context: Build context path
        no_cache: Disable cache
        build_args: Build arguments

    Returns:
        Command list
    """
    cmd = ["docker", "build", "-t", tag, "-f", dockerfile]

    if no_cache:
        cmd.append("--no-cache")

    if build_args:
        for arg in build_args:
            cmd.extend(["--build-arg", arg])

    cmd.append(context)
    return cmd


# =============================================================================
# CLI Commands
# =============================================================================


def build_command(
    mode: Annotated[
        str,
        cyclopts.Parameter(help="Build mode: development or production"),
    ] = "production",
    output: Annotated[
        Path,
        cyclopts.Parameter(name="--output", help="Output directory"),
    ] = Path("dist"),
    frontend_mode: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--frontend-mode", help="Override frontend mode: indie|plugin|eject"
        ),
    ] = None,
) -> None:
    """Build frontend assets.

    Built-in frontend modes (from framework_config.toml):
    - indie: Build default Desk (no custom code)
    - plugin: Shadow Build with app plugins
    - eject: Skip (user manages their own build)

    Examples:
        m build                           # Production build
        m build --mode development
        m build --frontend-mode plugin    # Override config
    """
    print("Frontend Build")
    print("=" * 40)
    print()

    # Load config to detect frontend mode
    config = load_config()
    frontend_config = config.get("frontend", {})
    detected_mode = frontend_mode or frontend_config.get("mode", "indie")

    print(f"  Build Mode:    {mode}")
    print(f"  Frontend Mode: {detected_mode}")
    print(f"  Output:        {output}")
    print()

    # Handle different frontend modes
    if detected_mode == "eject":
        _build_eject_mode()
    elif detected_mode == "plugin":
        _build_plugin_mode(mode, output)
    else:  # indie (default)
        _build_indie_mode(mode, output)


def _build_eject_mode() -> None:
    """Handle eject mode - user manages their own build."""
    print("Frontend mode: eject")
    print()
    print("Eject mode detected. Skipping frontend build.")
    print("User is responsible for their own frontend build process.")
    print()
    print("If you want Framework M to build the frontend, change mode in")
    print("framework_config.toml:")
    print()
    print("  [frontend]")
    print('  mode = "indie"    # or "plugin"')


def _build_indie_mode(mode: str, output: Path) -> None:
    """Build indie mode - default Desk only."""
    print("Frontend mode: indie (default Desk)")
    print()

    # Check for framework's frontend directory
    framework_frontend = Path(__file__).parent.parent.parent.parent / "frontend"

    # Also check relative paths
    frontend_dirs = [
        framework_frontend,
        Path.cwd() / "frontend",
        Path.cwd() / "static" / "frontend",
    ]

    frontend_dir = None
    for d in frontend_dirs:
        if (d / "package.json").exists():
            frontend_dir = d
            break

    if frontend_dir is None:
        print("Warning: No frontend directory found.")
        print()
        print("For indie mode, ensure frontend/ exists with package.json.")
        print("See Phase 09A: Frontend for setup instructions.")
        return

    print(f"Building from: {frontend_dir}")

    try:
        # Prefer pnpm, fallback to npm
        pkg_manager = "pnpm" if _has_command("pnpm") else "npm"

        # Install dependencies if needed
        if not (frontend_dir / "node_modules").exists():
            print(f"Installing dependencies with {pkg_manager}...")
            subprocess.run(
                [pkg_manager, "install"],
                cwd=frontend_dir,
                check=True,
            )

        # Build
        build_cmd = [pkg_manager, "run", "build"]
        if mode == "development":
            build_cmd = [pkg_manager, "run", "dev"]  # or build:dev if exists

        print(f"Running: {' '.join(build_cmd)}")
        subprocess.run(build_cmd, cwd=frontend_dir, check=True)

        # Copy to output
        frontend_dist = frontend_dir / "dist"
        if frontend_dist.exists() and frontend_dist != output:
            import shutil

            output.mkdir(parents=True, exist_ok=True)
            shutil.copytree(frontend_dist, output, dirs_exist_ok=True)
            print(f"Copied build to: {output}")

        print()
        print("✓ Frontend build complete (indie mode)")

    except FileNotFoundError as e:
        print(
            "Error: Package manager not found. Install Node.js/pnpm.", file=sys.stderr
        )
        raise SystemExit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"Error: Build failed with exit code {e.returncode}", file=sys.stderr)
        raise SystemExit(e.returncode) from e


def _build_plugin_mode(mode: str, output: Path) -> None:
    """Build plugin mode - Shadow Build with app plugins."""
    print("Frontend mode: plugin (Shadow Build)")
    print()

    # Scan for app frontend plugins
    apps_dir = Path.cwd() / "apps"
    plugins: list[tuple[str, Path]] = []

    if apps_dir.exists():
        for app_dir in apps_dir.iterdir():
            if app_dir.is_dir():
                plugin_entry = app_dir / "frontend" / "index.ts"
                if plugin_entry.exists():
                    plugins.append((app_dir.name, plugin_entry))

    if not plugins:
        print("No app frontend plugins found.")
        print()
        print("For plugin mode, apps should have:")
        print("  apps/{app_name}/frontend/index.ts")
        print()
        print("Falling back to indie mode...")
        _build_indie_mode(mode, output)
        return

    print(f"Found {len(plugins)} app plugins:")
    for name, path in plugins:
        print(f"  - {name}: {path}")
    print()

    # Generate temporary entry file
    temp_dir = Path.cwd() / ".m" / "build"
    temp_dir.mkdir(parents=True, exist_ok=True)

    entry_file = temp_dir / "entry.tsx"
    _generate_plugin_entry(entry_file, plugins)

    print(f"Generated entry: {entry_file}")

    # Run vite build
    try:
        # Check for frontend base
        frontend_dir = Path.cwd() / "frontend"
        if not (frontend_dir / "package.json").exists():
            print(
                "Error: No frontend/package.json. Plugin mode requires base frontend."
            )
            raise SystemExit(1)

        pkg_manager = "pnpm" if _has_command("pnpm") else "npm"

        # Install deps
        if not (frontend_dir / "node_modules").exists():
            subprocess.run([pkg_manager, "install"], cwd=frontend_dir, check=True)

        # Build with custom entry
        env = {**os.environ, "VITE_ENTRY": str(entry_file)}
        subprocess.run(
            [pkg_manager, "run", "build"],
            cwd=frontend_dir,
            check=True,
            env=env,
        )

        print()
        print("✓ Frontend build complete (plugin mode)")

    except subprocess.CalledProcessError as e:
        print(f"Error: Plugin build failed: {e.returncode}", file=sys.stderr)
        raise SystemExit(e.returncode) from e


def _generate_plugin_entry(entry_file: Path, plugins: list[tuple[str, Path]]) -> None:
    """Generate temporary entry.tsx that imports all app plugins."""
    imports = []
    registrations = []

    for app_name, plugin_path in plugins:
        relative_path = plugin_path.relative_to(Path.cwd())
        import_name = app_name.replace("-", "_").replace(".", "_")
        imports.append(
            f'import {{ register as register_{import_name} }} from "../../{relative_path}";'
        )
        registrations.append(f"  register_{import_name}();")

    content = f"""// Auto-generated plugin entry
// DO NOT EDIT - regenerated on each build

{chr(10).join(imports)}

// Register all app plugins
export function registerAllPlugins() {{
{chr(10).join(registrations)}
}}

// Auto-register on import
registerAllPlugins();
"""

    entry_file.write_text(content)


def _has_command(cmd: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def build_docker_command(
    tag: Annotated[
        str | None,
        cyclopts.Parameter(name="--tag", help="Image tag (default: from config)"),
    ] = None,
    dockerfile: Annotated[
        str,
        cyclopts.Parameter(name="--file", help="Path to Dockerfile"),
    ] = "Dockerfile",
    context: Annotated[
        str,
        cyclopts.Parameter(name="--context", help="Build context path"),
    ] = ".",
    no_cache: Annotated[
        bool,
        cyclopts.Parameter(name="--no-cache", help="Build without cache"),
    ] = False,
    push: Annotated[
        bool,
        cyclopts.Parameter(name="--push", help="Push image after build"),
    ] = False,
) -> None:
    """Build Docker image for the application.

    Wraps `docker build` with Framework M defaults.
    Reads image name and version from framework_config.toml if not specified.

    Examples:
        m build:docker                   # Use config defaults
        m build:docker --tag myapp:v1    # Custom tag
        m build:docker --push            # Build and push
    """
    # Determine tag
    image_tag = tag or get_default_image_name()

    # Check Dockerfile exists
    dockerfile_path = Path(dockerfile)
    if not dockerfile_path.exists():
        print(f"Error: Dockerfile not found: {dockerfile}", file=sys.stderr)
        print()
        print("Create a Dockerfile or specify path with --file")
        raise SystemExit(1)

    # Build command
    cmd = build_docker_cmd(
        tag=image_tag,
        dockerfile=dockerfile,
        context=context,
        no_cache=no_cache,
    )

    print("Docker Build")
    print("=" * 40)
    print()
    print(f"  Image:      {image_tag}")
    print(f"  Dockerfile: {dockerfile}")
    print(f"  Context:    {context}")
    if no_cache:
        print("  Cache:      disabled")
    print()
    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise SystemExit(result.returncode)

        print()
        print(f"✓ Built image: {image_tag}")

        # Push if requested
        if push:
            print()
            print(f"Pushing: {image_tag}")
            push_result = subprocess.run(["docker", "push", image_tag])
            if push_result.returncode != 0:
                raise SystemExit(push_result.returncode)
            print(f"✓ Pushed: {image_tag}")

    except FileNotFoundError:
        print("Error: docker not found. Install Docker.", file=sys.stderr)
        raise SystemExit(1) from None


__all__ = [
    "build_command",
    "build_docker_cmd",
    "build_docker_command",
    "get_default_image_name",
]
