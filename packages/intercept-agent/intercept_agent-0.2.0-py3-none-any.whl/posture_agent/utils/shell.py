"""Shell utility functions for running subprocesses."""

import asyncio


async def run_command(*args: str, timeout: float = 10.0) -> str | None:
    """Run a command and return stdout, or None on failure."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
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
