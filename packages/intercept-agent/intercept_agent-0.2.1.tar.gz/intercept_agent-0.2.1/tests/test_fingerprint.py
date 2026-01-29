"""Tests for machine fingerprint."""

import asyncio

from posture_agent.services.fingerprint import get_machine_fingerprint


class TestFingerprint:
    def test_returns_string(self):
        fp = asyncio.run(get_machine_fingerprint())
        assert isinstance(fp, str)
        assert len(fp) == 32

    def test_stable(self):
        """Fingerprint should be stable across calls."""
        fp1 = asyncio.run(get_machine_fingerprint())
        fp2 = asyncio.run(get_machine_fingerprint())
        assert fp1 == fp2
