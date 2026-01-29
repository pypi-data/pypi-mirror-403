"""IDE extension collector."""

import json
import re
import zipfile
from pathlib import Path

from posture_agent.collectors.base import BaseCollector, CollectorResult
from posture_agent.utils.shell import run_command

# Map binary name to extensions directory
_EXT_DIRS = {
    "code": Path.home() / ".vscode" / "extensions",
    "cursor": Path.home() / ".cursor" / "extensions",
}


class ExtensionCollector(BaseCollector):
    """Collects IDE extension information."""

    name = "extensions"

    async def collect(self) -> CollectorResult:
        errors: list[str] = []
        extensions: dict[str, list[dict[str, str]]] = {}

        # VS Code extensions
        try:
            vscode_exts = await self._collect_vscode_extensions("code")
            if vscode_exts:
                extensions["vscode"] = vscode_exts
        except Exception as e:
            errors.append(f"VS Code extensions: {e}")

        # Cursor extensions
        try:
            cursor_exts = await self._collect_vscode_extensions("cursor")
            if cursor_exts:
                extensions["cursor"] = cursor_exts
        except Exception as e:
            errors.append(f"Cursor extensions: {e}")

        # JetBrains plugins
        try:
            jetbrains_plugins = await self._collect_jetbrains_plugins()
            if jetbrains_plugins:
                extensions["jetbrains"] = jetbrains_plugins
        except Exception as e:
            errors.append(f"JetBrains plugins: {e}")

        return CollectorResult(
            collector=self.name,
            data=extensions,
            errors=errors,
        )

    async def _collect_vscode_extensions(self, binary: str) -> list[dict[str, str]]:
        """Collect extensions for VS Code or Cursor via CLI or filesystem."""
        # Try CLI first
        which_result = await run_command("which", binary)
        if which_result and which_result.strip():
            result = await run_command(binary, "--list-extensions", "--show-versions")
            if result:
                exts = []
                for line in result.strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    if "@" in line:
                        ext_id, version = line.rsplit("@", 1)
                        exts.append({"id": ext_id, "version": version})
                    else:
                        exts.append({"id": line, "version": ""})
                return exts

        # Fall back to reading extensions directory
        ext_dir = _EXT_DIRS.get(binary)
        if not ext_dir or not ext_dir.exists():
            return []

        exts = []
        for entry in ext_dir.iterdir():
            if not entry.is_dir():
                continue
            pkg_json = entry / "package.json"
            if not pkg_json.exists():
                continue
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
                publisher = data.get("publisher", "")
                name = data.get("name", "")
                version = data.get("version", "")
                if publisher and name:
                    exts.append({"id": f"{publisher}.{name}", "version": version})
            except (json.JSONDecodeError, OSError):
                continue
        # Deduplicate (multiple versions may be installed)
        seen: dict[str, str] = {}
        for ext in exts:
            ext_id = ext["id"].lower()
            if ext_id not in seen or ext["version"] > seen[ext_id]:
                seen[ext_id] = ext["version"]
        return [{"id": ext_id, "version": ver} for ext_id, ver in sorted(seen.items())]

    async def _collect_jetbrains_plugins(self) -> list[dict[str, str]]:
        """Collect JetBrains IDE plugins from filesystem."""
        plugins: list[dict[str, str]] = []
        jetbrains_dir = Path.home() / "Library" / "Application Support" / "JetBrains"
        if not jetbrains_dir.exists():
            return plugins

        for ide_dir in jetbrains_dir.iterdir():
            if not ide_dir.is_dir():
                continue
            plugins_dir = ide_dir / "plugins"
            if plugins_dir.exists():
                for plugin_dir in plugins_dir.iterdir():
                    if plugin_dir.is_dir():
                        version = self._get_jetbrains_plugin_version(plugin_dir)
                        plugins.append({
                            "id": plugin_dir.name,
                            "ide": ide_dir.name,
                            "version": version,
                        })
        return plugins

    def _get_jetbrains_plugin_version(self, plugin_dir: Path) -> str:
        """Extract version from a JetBrains plugin's JAR META-INF/plugin.xml."""
        lib_dir = plugin_dir / "lib"
        if not lib_dir.exists():
            return ""

        for jar_path in lib_dir.glob("*.jar"):
            try:
                with zipfile.ZipFile(jar_path) as zf:
                    if "META-INF/plugin.xml" not in zf.namelist():
                        continue
                    plugin_xml = zf.read("META-INF/plugin.xml").decode("utf-8", errors="replace")
                    match = re.search(r"<version>([^<]+)</version>", plugin_xml)
                    if match:
                        return match.group(1)
            except (zipfile.BadZipFile, OSError, KeyError):
                continue
        return ""
