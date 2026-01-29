"""AI tools collector."""

from posture_agent.collectors.base import BaseCollector, CollectorResult
from posture_agent.utils.shell import check_version, run_command


# Known AI extension IDs across editors
AI_EXTENSIONS = {
    "github.copilot",
    "github.copilot-chat",
    "sourcegraph.cody-ai",
    "continue.continue",
    "amazonwebservices.amazon-q-vscode",
    "saoudrizwan.claude-dev",
    "cursor.cursor-ai",
}

# CLI-based AI tools: (name, binary, version_flag)
AI_CLI_TOOLS = [
    ("Claude Code", "claude", "--version"),
    ("GitHub Copilot CLI", "github-copilot-cli", "--version"),
    ("Aider", "aider", "--version"),
    ("Open Interpreter", "interpreter", "--version"),
]


class AIToolsCollector(BaseCollector):
    """Collects AI coding tool information."""

    name = "ai_tools"

    async def collect(self) -> CollectorResult:
        errors: list[str] = []
        ai_tools: list[dict[str, str]] = []

        # Check CLI tools
        for name, binary, version_flag in AI_CLI_TOOLS:
            try:
                which_result = await run_command("which", binary)
                if which_result and which_result.strip():
                    version = await check_version(binary, version_flag) or ""
                    ai_tools.append({
                        "name": name,
                        "type": "cli",
                        "binary": binary,
                        "version": version,
                    })
            except Exception as e:
                errors.append(f"{name}: {e}")

        # Check VS Code/Cursor extensions for AI tools
        for binary in ("code", "cursor"):
            try:
                which_result = await run_command("which", binary)
                if not which_result or not which_result.strip():
                    continue

                result = await run_command(binary, "--list-extensions")
                if not result:
                    continue

                installed_exts = {ext.strip().lower() for ext in result.strip().split("\n") if ext.strip()}
                for ai_ext_id in AI_EXTENSIONS:
                    if ai_ext_id.lower() in installed_exts:
                        editor = "VS Code" if binary == "code" else "Cursor"
                        ai_tools.append({
                            "name": ai_ext_id,
                            "type": "extension",
                            "editor": editor,
                            "version": "",
                        })
            except Exception as e:
                errors.append(f"AI extensions ({binary}): {e}")

        return CollectorResult(
            collector=self.name,
            data=ai_tools,
            errors=errors,
        )
