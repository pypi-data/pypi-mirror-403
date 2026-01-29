"""Intercept Posture Agent CLI."""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from posture_agent.collectors.ai_tools import AIToolsCollector
from posture_agent.collectors.dev_tools import DevToolsCollector
from posture_agent.collectors.extensions import ExtensionCollector
from posture_agent.collectors.ides import IDECollector
from posture_agent.collectors.machine import MachineCollector
from posture_agent.collectors.package_managers import PackageManagerCollector
from posture_agent.collectors.security import SecurityCollector
from posture_agent.core.config import get_settings
from posture_agent.models.report import PostureReportPayload
from posture_agent.services.fingerprint import get_machine_fingerprint
from posture_agent.services.reporter import send_report


PLIST_NAME = "com.hijacksecurity.intercept-agent"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_NAME}.plist"


async def run_collection(report: bool = False) -> None:
    """Run all collectors and optionally report to API."""
    settings = get_settings()

    # Get machine fingerprint
    fingerprint = await get_machine_fingerprint()

    # Run enabled collectors
    collectors = []
    if settings.collectors.machine:
        collectors.append(MachineCollector())
    if settings.collectors.ides:
        collectors.append(IDECollector())
    if settings.collectors.extensions:
        collectors.append(ExtensionCollector())
    if settings.collectors.ai_tools:
        collectors.append(AIToolsCollector())
    if settings.collectors.dev_tools:
        collectors.append(DevToolsCollector())
    if settings.collectors.security:
        collectors.append(SecurityCollector())
    if settings.collectors.package_managers:
        collectors.append(PackageManagerCollector())

    results = await asyncio.gather(
        *(c.collect() for c in collectors),
        return_exceptions=True,
    )

    # Build payload
    payload_data: dict = {
        "fingerprint": fingerprint,
        "agent_version": settings.agent_version,
        "collected_at": datetime.now(timezone.utc),
    }

    for result in results:
        if isinstance(result, Exception):
            click.echo(f"  Error: {result}", err=True)
            continue
        payload_data[result.collector] = result.data

    payload = PostureReportPayload(**payload_data)

    if report:
        click.echo(f"Sending report to {settings.api.url}...")
        try:
            response = await send_report(payload, settings)
            click.echo(f"Report submitted: {response.get('id', 'ok')}")
        except Exception as e:
            click.echo(f"Failed to send report: {e}", err=True)
            sys.exit(1)
    else:
        click.echo(json.dumps(payload.model_dump(mode="json"), indent=2))


@click.group()
def cli() -> None:
    """Intercept Developer Posture Agent."""
    pass


@cli.command()
@click.option("--report", is_flag=True, help="Send report to API (default: dry-run to stdout)")
def collect(report: bool) -> None:
    """Collect developer environment data."""
    asyncio.run(run_collection(report=report))


@cli.command()
def install() -> None:
    """Install launchd plist for hourly collection."""
    settings = get_settings()
    interval = settings.schedule.interval_seconds

    # Ensure config directory and logs exist
    config_dir = Path.home() / ".config" / "intercept"
    logs_dir = config_dir / "logs"
    config_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Write default config if not present
    config_file = config_dir / "agent.yaml"
    if not config_file.exists():
        config_file.write_text(
            "api:\n"
            f"  url: \"{settings.api.url}\"\n"
            "  timeout: 30\n"
            "  retries: 3\n"
            "collectors:\n"
            "  machine: true\n"
            "  ides: true\n"
            "  extensions: true\n"
            "  ai_tools: true\n"
            "  dev_tools: true\n"
            "  security: true\n"
            "  package_managers: true\n"
            "schedule:\n"
            f"  interval_seconds: {interval}\n"
        )
        click.echo(f"Config written to {config_file}")

    # Find the intercept-agent binary
    import shutil
    agent_bin = shutil.which("intercept-agent")
    if not agent_bin:
        click.echo("Error: intercept-agent not found in PATH. Install with: pip install -e .", err=True)
        sys.exit(1)

    stdout_log = str(logs_dir / "agent.stdout.log")
    stderr_log = str(logs_dir / "agent.stderr.log")

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{agent_bin}</string>
        <string>collect</string>
        <string>--report</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{stdout_log}</string>
    <key>StandardErrorPath</key>
    <string>{stderr_log}</string>
</dict>
</plist>
"""

    # Write plist
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(plist_content)
    click.echo(f"Plist written to {PLIST_PATH}")

    # Load with launchctl
    import subprocess
    subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)
    click.echo("Agent installed and started.")


@cli.command()
def uninstall() -> None:
    """Uninstall launchd plist."""
    import subprocess

    if PLIST_PATH.exists():
        subprocess.run(["launchctl", "unload", str(PLIST_PATH)], check=False)
        PLIST_PATH.unlink()
        click.echo("Agent uninstalled.")
    else:
        click.echo("Agent not installed.")


@cli.command()
def status() -> None:
    """Show agent status."""
    settings = get_settings()

    click.echo(f"Agent version: {settings.agent_version}")
    click.echo(f"API URL: {settings.api.url}")
    click.echo(f"Schedule: every {settings.schedule.interval_seconds}s")
    click.echo(f"Plist: {PLIST_PATH}")
    click.echo(f"Installed: {PLIST_PATH.exists()}")

    if PLIST_PATH.exists():
        import subprocess
        result = subprocess.run(
            ["launchctl", "list", PLIST_NAME],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            click.echo(f"Status: loaded")
            for line in result.stdout.strip().split("\n"):
                if "PID" in line or "LastExitStatus" in line:
                    click.echo(f"  {line.strip()}")
        else:
            click.echo("Status: not loaded")

    # Check logs
    stdout_log = Path.home() / ".config" / "intercept" / "logs" / "agent.stdout.log"
    if stdout_log.exists():
        lines = stdout_log.read_text().strip().split("\n")
        if lines:
            click.echo(f"Last output: {lines[-1]}")


if __name__ == "__main__":
    cli()
