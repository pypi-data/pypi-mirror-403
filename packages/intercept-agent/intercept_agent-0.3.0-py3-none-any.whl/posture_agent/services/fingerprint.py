"""Machine fingerprint generation."""

import hashlib

from posture_agent.utils.shell import run_command


async def get_machine_fingerprint() -> str:
    """Generate a stable machine fingerprint from IOPlatformUUID."""
    # Try IOPlatformUUID first (most reliable on macOS)
    result = await run_command(
        "ioreg", "-rd1", "-c", "IOPlatformExpertDevice"
    )
    if result:
        for line in result.split("\n"):
            if "IOPlatformUUID" in line:
                # Extract UUID value
                parts = line.split('"')
                for i, part in enumerate(parts):
                    if part == "IOPlatformUUID" and i + 2 < len(parts):
                        uuid_val = parts[i + 2]
                        return hashlib.sha256(uuid_val.encode()).hexdigest()[:32]

    # Fallback: serial number
    serial = await run_command(
        "ioreg", "-l", "-c", "IOPlatformExpertDevice"
    )
    if serial:
        for line in serial.split("\n"):
            if "IOPlatformSerialNumber" in line:
                parts = line.split('"')
                for i, part in enumerate(parts):
                    if part == "IOPlatformSerialNumber" and i + 2 < len(parts):
                        return hashlib.sha256(parts[i + 2].encode()).hexdigest()[:32]

    # Last resort: hostname-based
    import platform
    fallback = f"{platform.node()}-{platform.machine()}"
    return hashlib.sha256(fallback.encode()).hexdigest()[:32]
