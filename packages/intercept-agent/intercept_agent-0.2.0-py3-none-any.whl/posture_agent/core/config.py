"""Application configuration loaded from YAML files with env overrides."""

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    """Application configuration."""

    name: str = "Intercept Posture Agent"
    debug: bool = False
    log_level: str = "INFO"


class APIConfig(BaseModel):
    """API connection configuration."""

    url: str = "http://localhost:8000"
    timeout: int = 30
    retries: int = 3


class CollectorsConfig(BaseModel):
    """Collector enable/disable flags."""

    machine: bool = True
    ides: bool = True
    extensions: bool = True
    ai_tools: bool = True
    dev_tools: bool = True
    security: bool = True
    package_managers: bool = True


class ScheduleConfig(BaseModel):
    """Schedule configuration."""

    interval_seconds: int = 3600


class Settings:
    """Combined settings from YAML config and environment."""

    def __init__(self) -> None:
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file based on ENVIRONMENT variable."""
        env = os.getenv("ENVIRONMENT", "dev-local")
        user_config = Path.home() / ".config" / "intercept" / "agent.yaml"
        config_paths = [
            user_config,
            Path(f"config/{env}.yaml"),
            Path(f"../config/{env}.yaml"),
            Path(__file__).parent.parent.parent / "config" / f"{env}.yaml",
        ]

        config_data: dict = {}
        for config_path in config_paths:
            if config_path.exists():
                with open(config_path) as f:
                    config_data = yaml.safe_load(f) or {}
                break

        self.app = AppConfig(**config_data.get("app", {}))
        self.api = APIConfig(**config_data.get("api", {}))
        self.collectors = CollectorsConfig(**config_data.get("collectors", {}))
        self.schedule = ScheduleConfig(**config_data.get("schedule", {}))

        # Environment variable overrides
        if api_url := os.environ.get("INTERCEPT_API_URL"):
            self.api = self.api.model_copy(update={"url": api_url})

    @property
    def agent_version(self) -> str:
        """Read version from VERSION file."""
        version_path = Path(__file__).parent.parent.parent / "VERSION"
        if version_path.exists():
            return version_path.read_text().strip()
        return "0.1.0"

    # Convenience properties
    @property
    def debug(self) -> bool:
        return self.app.debug

    @property
    def log_level(self) -> str:
        return self.app.log_level


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
