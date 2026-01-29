"""
Auto-detection and setup of IDA Python environment.

This module handles finding IDA Pro and configuring the Python environment
so that idapro and ida_domain can be imported correctly.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _is_valid_ida_dir(path: Path) -> bool:
    """Check if a path is a valid IDA installation with idalib support."""
    if not path.exists():
        return False
    # Must have idalib directory and idapyswitch
    return (path / "idalib").exists() and (path / "idapyswitch").exists()


def _glob_ida_installations(base_dir: Path) -> list[Path]:
    """Find IDA installations in a directory using glob patterns."""
    patterns = ["ida-pro-*", "idapro-*", "ida-*", "IDA*"]
    found = []
    if not base_dir.exists():
        return found
    for pattern in patterns:
        for path in base_dir.glob(pattern):
            if path.is_dir() and _is_valid_ida_dir(path):
                found.append(path)
    # Sort by version (highest first) - assumes version in name like ida-pro-9.3
    found.sort(key=lambda p: p.name, reverse=True)
    return found


def find_ida_installation() -> Path | None:
    """Find IDA Pro installation.

    Search order:
    1. IDADIR environment variable
    2. IDA_INSTALL_DIR environment variable
    3. Glob search in /opt for ida-pro-*, idapro-*, etc.
    4. Glob search in home directory
    5. Common macOS paths
    6. WSL Windows paths
    """
    # Check environment variables first
    for env_var in ["IDADIR", "IDA_INSTALL_DIR"]:
        env_value = os.environ.get(env_var)
        if env_value:
            path = Path(env_value)
            if _is_valid_ida_dir(path):
                return path

    # Glob search in /opt (most common Linux location)
    for path in _glob_ida_installations(Path("/opt")):
        return path  # Return first (highest version)

    # Glob search in home directory
    for path in _glob_ida_installations(Path.home()):
        return path

    # macOS application paths
    mac_paths = [
        Path("/Applications/IDA Professional 9.3.app/Contents/MacOS"),
        Path("/Applications/IDA Professional 9.2.app/Contents/MacOS"),
        Path("/Applications/IDA Professional 9.1.app/Contents/MacOS"),
    ]
    for path in mac_paths:
        if _is_valid_ida_dir(path):
            return path

    # WSL Windows paths
    wsl_paths = [
        Path("/mnt/c/Program Files/IDA Pro 9.3"),
        Path("/mnt/c/Program Files/IDA Pro 9.2"),
        Path("/mnt/c/Program Files/IDA Pro 9.1"),
    ]
    for path in wsl_paths:
        if _is_valid_ida_dir(path):
            return path

    return None


def is_idapro_configured() -> bool:
    """Check if idapro is already configured and working."""
    try:
        import idapro
        # Check if IDA install dir is set
        ida_dir = idapro.get_ida_install_dir()
        return ida_dir is not None and Path(ida_dir).exists()
    except (ImportError, Exception):
        return False


def is_ida_domain_available() -> bool:
    """Check if ida_domain is available."""
    try:
        import idapro  # noqa: F401 - must be imported first
        from ida_domain import Database  # noqa: F401
        return True
    except ImportError:
        return False


def run_activation_script(ida_path: Path) -> bool:
    """Run the IDA idalib activation script."""
    activation_script = ida_path / "idalib" / "python" / "py-activate-idalib.py"

    if not activation_script.exists():
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(activation_script), "-d", str(ida_path)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def install_ida_domain() -> bool:
    """Install ida-domain package."""
    try:
        # Try pip first
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "ida-domain", "-q"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True

        # Try uv if pip fails (externally managed environment)
        if "externally-managed-environment" in result.stderr:
            result = subprocess.run(
                ["uv", "pip", "install", "ida-domain", "-q"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0

        return False
    except Exception:
        return False


def ensure_environment() -> tuple[bool, str | None]:
    """
    Ensure the IDA Python environment is properly configured.

    Returns:
        Tuple of (success, error_message)
    """
    # Check if everything is already working
    if is_ida_domain_available():
        return True, None

    # Try to find IDA installation
    ida_path = find_ida_installation()
    if ida_path is None:
        return False, (
            "Could not find IDA Pro installation. "
            "Please set IDA_INSTALL_DIR environment variable or install IDA Pro 9.1+."
        )

    # Check if idapro needs activation
    if not is_idapro_configured():
        if not run_activation_script(ida_path):
            return False, (
                f"Failed to activate idalib. "
                f"Please run: python {ida_path}/idalib/python/py-activate-idalib.py -d {ida_path}"
            )

    # Check if ida_domain needs to be installed
    try:
        import idapro  # noqa: F401
        from ida_domain import Database  # noqa: F401
        return True, None
    except ImportError as e:
        if "ida_domain" in str(e):
            if not install_ida_domain():
                return False, (
                    "Failed to install ida-domain. "
                    "Please run: pip install ida-domain"
                )
            # Try import again after installation
            try:
                import idapro  # noqa: F401
                from ida_domain import Database  # noqa: F401
                return True, None
            except ImportError as e2:
                return False, f"Failed to import ida_domain after installation: {e2}"
        else:
            return False, f"Failed to import required modules: {e}"


def setup_or_exit() -> None:
    """
    Ensure environment is set up, or exit with error message.

    This should be called at the start of the CLI main function.
    """
    success, error = ensure_environment()
    if not success:
        import click
        click.echo(f"Error: {error}", err=True)
        click.echo("\nida-cli requires IDA Pro 9.1+ with idalib support.", err=True)
        click.echo("See: https://hex-rays.com/ida-pro/", err=True)
        sys.exit(1)
