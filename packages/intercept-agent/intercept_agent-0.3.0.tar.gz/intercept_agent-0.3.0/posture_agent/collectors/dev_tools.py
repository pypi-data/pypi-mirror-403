"""Developer tools collector."""

import os

from posture_agent.collectors.base import BaseCollector, CollectorResult
from posture_agent.utils.shell import check_version, run_command


# Tool definitions: (name, binary, version_flag)
DEV_TOOL_DEFINITIONS = [
    ("Git", "git", "--version"),
    ("Docker", "docker", "--version"),
    ("Node.js", "node", "--version"),
    ("Python", "python3", "--version"),
    ("Go", "go", "version"),
    ("Rust", "rustc", "--version"),
    ("Ruby", "ruby", "--version"),
    ("Java", "java", "--version"),
    ("Swift", "swift", "--version"),
    ("Make", "make", "--version"),
    ("CMake", "cmake", "--version"),
    ("Terraform", "terraform", "--version"),
    ("kubectl", "kubectl", "version --client"),
    ("Helm", "helm", "version --short"),
    ("AWS CLI", "aws", "--version"),
    ("gcloud", "gcloud", "--version"),
    ("Azure CLI", "az", "--version"),
]


class DevToolsCollector(BaseCollector):
    """Collects installed developer tools."""

    name = "dev_tools"

    async def collect(self) -> CollectorResult:
        errors: list[str] = []
        tools: list[dict[str, str]] = []

        for name, binary, version_flag in DEV_TOOL_DEFINITIONS:
            try:
                which_result = await run_command("which", binary)
                if which_result and which_result.strip():
                    version = await check_version(binary, version_flag) or ""
                    path = os.path.realpath(which_result.strip())
                    tools.append({
                        "name": name,
                        "binary": binary,
                        "version": version,
                        "path": path,
                    })
            except Exception as e:
                errors.append(f"{name}: {e}")

        return CollectorResult(
            collector=self.name,
            data=tools,
            errors=errors,
        )
