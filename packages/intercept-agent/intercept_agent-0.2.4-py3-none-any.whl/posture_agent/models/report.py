"""Pydantic models for the posture report payload."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PostureReportPayload(BaseModel):
    """The full report payload sent to the API."""

    fingerprint: str
    agent_version: str
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    machine: dict[str, Any] = {}
    ides: list[Any] | dict[str, Any] = []
    extensions: dict[str, Any] = {}
    ai_tools: list[Any] | dict[str, Any] = []
    dev_tools: list[Any] | dict[str, Any] = []
    security: dict[str, Any] = {}
    package_managers: list[Any] | dict[str, Any] = []
