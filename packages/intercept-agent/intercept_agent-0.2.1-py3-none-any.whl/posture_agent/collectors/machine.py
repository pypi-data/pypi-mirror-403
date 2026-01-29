"""Machine info collector."""

import platform

from posture_agent.collectors.base import BaseCollector, CollectorResult
from posture_agent.utils.shell import run_command


class MachineCollector(BaseCollector):
    """Collects machine hardware and OS information."""

    name = "machine"

    async def collect(self) -> CollectorResult:
        errors: list[str] = []

        hostname = platform.node()
        os_name = "macOS"
        os_version = platform.mac_ver()[0] or platform.release()
        architecture = platform.machine()

        # CPU info
        cpu_brand = ""
        cpu_cores = 0
        try:
            result = await run_command("sysctl", "-n", "machdep.cpu.brand_string")
            cpu_brand = result.strip() if result else ""
        except Exception as e:
            errors.append(f"CPU brand: {e}")

        try:
            result = await run_command("sysctl", "-n", "hw.ncpu")
            cpu_cores = int(result.strip()) if result else 0
        except Exception as e:
            errors.append(f"CPU cores: {e}")

        # Memory
        memory_gb = 0
        try:
            result = await run_command("sysctl", "-n", "hw.memsize")
            if result:
                memory_gb = round(int(result.strip()) / (1024**3), 1)
        except Exception as e:
            errors.append(f"Memory: {e}")

        # Username
        import os
        username = os.environ.get("USER", "")

        return CollectorResult(
            collector=self.name,
            data={
                "hostname": hostname,
                "username": username,
                "os_name": os_name,
                "os_version": os_version,
                "architecture": architecture,
                "cpu_brand": cpu_brand,
                "cpu_cores": cpu_cores,
                "memory_gb": memory_gb,
            },
            errors=errors,
        )
