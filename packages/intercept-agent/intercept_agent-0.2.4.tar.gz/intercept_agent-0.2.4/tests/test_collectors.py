"""Tests for posture agent collectors."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from posture_agent.collectors.base import CollectorResult
from posture_agent.collectors.machine import MachineCollector
from posture_agent.collectors.dev_tools import DevToolsCollector
from posture_agent.collectors.security import SecurityCollector
from posture_agent.collectors.package_managers import PackageManagerCollector
from posture_agent.collectors.ides import IDECollector
from posture_agent.collectors.ai_tools import AIToolsCollector
from posture_agent.collectors.extensions import ExtensionCollector


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestMachineCollector:
    def test_collect_returns_result(self):
        collector = MachineCollector()
        result = asyncio.run(collector.collect())
        assert isinstance(result, CollectorResult)
        assert result.collector == "machine"
        assert "hostname" in result.data
        assert "os_name" in result.data
        assert "architecture" in result.data

    def test_collect_has_username(self):
        collector = MachineCollector()
        result = asyncio.run(collector.collect())
        assert "username" in result.data


class TestDevToolsCollector:
    def test_collect_returns_result(self):
        collector = DevToolsCollector()
        result = asyncio.run(collector.collect())
        assert isinstance(result, CollectorResult)
        assert result.collector == "dev_tools"
        assert isinstance(result.data, list)

    def test_finds_git(self):
        """Git should be installed on any dev machine."""
        collector = DevToolsCollector()
        result = asyncio.run(collector.collect())
        tool_names = [t["name"] for t in result.data]
        assert "Git" in tool_names


class TestSecurityCollector:
    def test_collect_returns_result(self):
        collector = SecurityCollector()
        result = asyncio.run(collector.collect())
        assert isinstance(result, CollectorResult)
        assert result.collector == "security"
        assert "git_signing_enabled" in result.data

    def test_has_ssh_info(self):
        collector = SecurityCollector()
        result = asyncio.run(collector.collect())
        assert "ssh_key_count" in result.data


class TestPackageManagerCollector:
    def test_collect_returns_result(self):
        collector = PackageManagerCollector()
        result = asyncio.run(collector.collect())
        assert isinstance(result, CollectorResult)
        assert result.collector == "package_managers"
        assert isinstance(result.data, list)


class TestIDECollector:
    def test_collect_returns_result(self):
        collector = IDECollector()
        result = asyncio.run(collector.collect())
        assert isinstance(result, CollectorResult)
        assert result.collector == "ides"
        assert isinstance(result.data, list)


class TestAIToolsCollector:
    def test_collect_returns_result(self):
        collector = AIToolsCollector()
        result = asyncio.run(collector.collect())
        assert isinstance(result, CollectorResult)
        assert result.collector == "ai_tools"
        assert isinstance(result.data, list)


class TestExtensionCollector:
    def test_collect_returns_result(self):
        collector = ExtensionCollector()
        result = asyncio.run(collector.collect())
        assert isinstance(result, CollectorResult)
        assert result.collector == "extensions"
        assert isinstance(result.data, dict)
