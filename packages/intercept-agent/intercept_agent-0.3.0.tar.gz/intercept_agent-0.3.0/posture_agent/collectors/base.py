"""Base collector interface."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class CollectorResult(BaseModel):
    """Result from a collector."""
    collector: str
    data: Any
    errors: list[str] = []


class BaseCollector(ABC):
    """Base class for all collectors."""

    name: str = "base"

    @abstractmethod
    async def collect(self) -> CollectorResult:
        """Collect data and return a result."""
        ...
