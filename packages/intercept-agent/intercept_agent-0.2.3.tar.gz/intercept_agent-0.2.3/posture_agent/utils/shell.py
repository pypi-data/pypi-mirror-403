"""Shell utility functions for running subprocesses."""

import asyncio
import os
from pathlib import Path


def _get_expanded_path() -> str:
    """Return PATH expanded with common tool locations.

    launchd runs with a minimal PATH (/usr/bin:/bin:/usr/sbin:/sbin).
    We add common locations where dev tools are installed.
    """
    current_path = os.environ.get("PATH", "")
    home = str(Path.home())

    extra_paths = [
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
        "/usr/local/sbin",
        f"{home}/.local/bin",
        f"{home}/.cargo/bin",
        f"{home}/.go/bin",
        f"{home}/go/bin",
    ]

    # Add nvm node paths
    nvm_dir = Path(home) / ".nvm" / "versions" / "node"
    if nvm_dir.exists():
        for version_dir in sorted(nvm_dir.iterdir(), reverse=True):
            bin_dir = version_dir / "bin"
            if bin_dir.exists():
                extra_paths.append(str(bin_dir))
                break  # Only add the latest version

    # Add Python framework paths (macOS)
    python_framework = Path("/Library/Frameworks/Python.framework/Versions")
    if python_framework.exists():
        for version_dir in sorted(python_framework.iterdir(), reverse=True):
            bin_dir = version_dir / "bin"
            if bin_dir.exists() and version_dir.name != "Current":
                extra_paths.append(str(bin_dir))
                break

    # Add pip --user paths (macOS)
    lib_python = Path(home) / "Library" / "Python"
    if lib_python.exists():
        for version_dir in sorted(lib_python.iterdir(), reverse=True):
            bin_dir = version_dir / "bin"
            if bin_dir.exists():
                extra_paths.append(str(bin_dir))
                break

    # Deduplicate while preserving order
    seen: set[str] = set()
    parts = []
    for p in current_path.split(":") + extra_paths:
        if p and p not in seen:
            seen.add(p)
            parts.append(p)

    return ":".join(parts)


def _get_env() -> dict[str, str]:
    """Return environment with expanded PATH for subprocess execution."""
    env = os.environ.copy()
    env["PATH"] = _get_expanded_path()
    return env


async def run_command(*args: str, timeout: float = 10.0) -> str | None:
    """Run a command and return stdout, or None on failure."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_get_env(),
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        if proc.returncode == 0 and stdout:
            return stdout.decode("utf-8", errors="replace")
        return None
    except (asyncio.TimeoutError, FileNotFoundError, OSError):
        return None


async def check_version(binary: str, version_flag: str) -> str | None:
    """Get version string from a binary. Handles multi-word flags."""
    args = [binary] + version_flag.split()
    result = await run_command(*args)
    if not result:
        return None

    # Extract version from common formats
    line = result.strip().split("\n")[0]

    # Try to find version-like pattern
    import re
    match = re.search(r"(\d+\.\d+[\.\d]*)", line)
    if match:
        return match.group(1)

    return line[:50]  # Fallback: first 50 chars of first line
