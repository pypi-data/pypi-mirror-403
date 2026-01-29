"""Package manager collector."""

from posture_agent.collectors.base import BaseCollector, CollectorResult
from posture_agent.utils.shell import check_version, run_command


# Package manager definitions: (name, binary, version_flag)
PACKAGE_MANAGERS = [
    ("Homebrew", "brew", "--version"),
    ("npm", "npm", "--version"),
    ("pnpm", "pnpm", "--version"),
    ("yarn", "yarn", "--version"),
    ("pip", "pip3", "--version"),
    ("uv", "uv", "--version"),
    ("pipx", "pipx", "--version"),
    ("Cargo", "cargo", "--version"),
    ("Go Modules", "go", "version"),
    ("Composer", "composer", "--version"),
    ("Gem", "gem", "--version"),
    ("CocoaPods", "pod", "--version"),
    ("Swift PM", "swift", "package --version"),
]


class PackageManagerCollector(BaseCollector):
    """Collects installed package managers."""

    name = "package_managers"

    async def collect(self) -> CollectorResult:
        errors: list[str] = []
        managers: list[dict[str, str]] = []

        for name, binary, version_flag in PACKAGE_MANAGERS:
            try:
                which_result = await run_command("which", binary)
                if which_result and which_result.strip():
                    version = await check_version(binary, version_flag) or ""
                    managers.append({
                        "name": name,
                        "binary": binary,
                        "version": version,
                    })
            except Exception as e:
                errors.append(f"{name}: {e}")

        return CollectorResult(
            collector=self.name,
            data=managers,
            errors=errors,
        )
