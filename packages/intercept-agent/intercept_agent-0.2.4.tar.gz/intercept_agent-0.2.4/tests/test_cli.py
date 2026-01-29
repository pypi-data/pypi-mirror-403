"""Tests for the CLI commands."""

from click.testing import CliRunner

from posture_agent.main import cli


class TestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Intercept Developer Posture Agent" in result.output

    def test_collect_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["collect", "--help"])
        assert result.exit_code == 0
        assert "--report" in result.output

    def test_status(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Agent version" in result.output

    def test_collect_dry_run(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["collect"])
        assert result.exit_code == 0
        # Should output JSON
        assert "fingerprint" in result.output
