"""IDE collector."""

from pathlib import Path

from posture_agent.collectors.base import BaseCollector, CollectorResult
from posture_agent.utils.shell import check_version, run_command


# IDE definitions: (name, binary, app_path, version_flag)
IDE_DEFINITIONS = [
    ("VS Code", "code", "/Applications/Visual Studio Code.app", "--version"),
    ("Cursor", "cursor", "/Applications/Cursor.app", "--version"),
    ("IntelliJ IDEA", "idea", "/Applications/IntelliJ IDEA.app", None),
    ("PyCharm", "pycharm", "/Applications/PyCharm.app", None),
    ("WebStorm", "webstorm", "/Applications/WebStorm.app", None),
    ("GoLand", "goland", "/Applications/GoLand.app", None),
    ("Xcode", None, "/Applications/Xcode.app", None),
    ("Vim", "vim", None, "--version"),
    ("Neovim", "nvim", None, "--version"),
    ("Emacs", "emacs", None, "--version"),
    ("Sublime Text", "subl", "/Applications/Sublime Text.app", "--version"),
    ("Zed", "zed", "/Applications/Zed.app", "--version"),
]


class IDECollector(BaseCollector):
    """Collects installed IDE information."""

    name = "ides"

    async def collect(self) -> CollectorResult:
        errors: list[str] = []
        ides: list[dict[str, str]] = []

        for name, binary, app_path, version_flag in IDE_DEFINITIONS:
            try:
                installed = False
                version = ""

                # Check app bundle
                if app_path and Path(app_path).exists():
                    installed = True
                    # Try to get version from Info.plist
                    plist_path = Path(app_path) / "Contents" / "Info.plist"
                    if plist_path.exists():
                        result = await run_command(
                            "defaults", "read", str(plist_path), "CFBundleShortVersionString"
                        )
                        if result:
                            version = result.strip()

                # Check binary
                if binary:
                    which_result = await run_command("which", binary)
                    if which_result and which_result.strip():
                        installed = True
                        if version_flag and not version:
                            ver = await check_version(binary, version_flag)
                            if ver:
                                version = ver

                if installed:
                    ides.append({
                        "name": name,
                        "version": version,
                        "binary": binary or "",
                    })
            except Exception as e:
                errors.append(f"{name}: {e}")

        return CollectorResult(
            collector=self.name,
            data=ides,
            errors=errors,
        )
