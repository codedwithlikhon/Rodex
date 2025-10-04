"""Project-level deployment and Gemini environment configuration utilities."""

from __future__ import annotations

import json
import importlib.resources as resources
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from .gemini_stream import GeminiStreamConfig


_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "project_settings.json"
_RESOURCE_PACKAGE = "services.planner._data"
_RESOURCE_NAME = "project_settings.json"


def _load_payload_from_path(config_path: Path) -> dict[str, Any]:
    """Return JSON payload loaded from ``config_path``."""

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Project settings file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in project settings: {config_path}") from exc


def _load_packaged_defaults() -> dict[str, Any]:
    """Return the packaged default project settings payload."""

    resource_path = resources.files(_RESOURCE_PACKAGE).joinpath(_RESOURCE_NAME)
    try:
        with resource_path.open("r", encoding="utf-8") as handle:  # type: ignore[attr-defined]
            return json.load(handle)
    except FileNotFoundError as exc:  # pragma: no cover - defensive guardrail
        raise FileNotFoundError(
            "Packaged project settings resource is missing; reinstall the package."
        ) from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guardrail
        raise ValueError("Packaged project settings contains invalid JSON.") from exc


class BackoffSettings(BaseModel):
    """Backoff parameters for Gemini retry handling."""

    factor: float = Field(default=1.5, gt=0)
    max_delay_seconds: float = Field(default=60.0, gt=0)


class GeminiSettings(BaseModel):
    """Gemini deployment defaults sourced from project settings."""

    model: str = Field(..., description="Model identifier for Gemini streaming requests.")
    primary_endpoint: str = Field(..., description="Primary streaming endpoint for Gemini.")
    fallback_endpoints: list[str] = Field(default_factory=list, description="Secondary endpoints used for failover.")
    request_timeout_seconds: float = Field(default=45.0, gt=0)
    heartbeat_interval_seconds: float = Field(default=10.0, ge=0)
    max_retries: int = Field(default=4, ge=0)
    backoff: BackoffSettings = Field(default_factory=BackoffSettings)


class RuntimeSettings(BaseModel):
    """Compute runtime metadata for the deployment."""

    provider: str
    product: str
    region: str


class DeploymentSettings(BaseModel):
    """Deployment metadata for the current project settings snapshot."""

    name: str
    slug: str
    environment: str
    description: str
    runtime: RuntimeSettings
    features: list[str] = Field(default_factory=list)
    environment_variables: dict[str, str] = Field(default_factory=dict)


class ProjectSettings(BaseModel):
    """Structured representation of the `project_settings.json` manifest."""

    version: str
    updated_at: str
    source: dict[str, Any] = Field(default_factory=dict)
    deployment: DeploymentSettings
    gemini: GeminiSettings
    observability: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "ProjectSettings":
        """Load project settings from disk or packaged defaults."""

        if path is not None:
            payload = _load_payload_from_path(Path(path))
        elif _CONFIG_PATH.exists():
            payload = _load_payload_from_path(_CONFIG_PATH)
        else:
            payload = _load_packaged_defaults()

        try:
            return cls.model_validate(payload)
        except ValidationError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Project settings validation failed: {exc}") from exc


class GeminiEnvironment(BaseSettings):
    """Resolve runtime Gemini configuration using environment + project defaults."""

    api_key: str = Field(..., alias="GEMINI_API_KEY", description="API key used for Gemini requests.")
    model_override: str | None = Field(None, alias="GEMINI_MODEL")
    endpoint_override: str | None = Field(None, alias="GEMINI_STREAM_ENDPOINT")
    fallback_override: str | None = Field(None, alias="GEMINI_FALLBACK_ENDPOINTS")
    request_timeout_override: float | None = Field(None, alias="GEMINI_REQUEST_TIMEOUT")
    heartbeat_override: float | None = Field(None, alias="GEMINI_HEARTBEAT_INTERVAL")
    max_retries_override: int | None = Field(None, alias="GEMINI_MAX_RETRIES")
    backoff_base_override: float | None = Field(None, alias="GEMINI_BACKOFF_BASE")
    backoff_max_override: float | None = Field(None, alias="GEMINI_BACKOFF_MAX")

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    @staticmethod
    def _split_csv(value: str | None) -> tuple[str, ...]:
        if not value:
            return tuple()
        parts: Iterable[str] = (segment.strip() for segment in value.split(","))
        return tuple(part for part in parts if part)

    def build_stream_config(self, project_settings: ProjectSettings | None = None) -> GeminiStreamConfig:
        """Combine environment overrides with project defaults to create a config."""

        settings = project_settings or ProjectSettings.load()
        gemini_defaults = settings.gemini

        endpoint = self.endpoint_override or gemini_defaults.primary_endpoint
        fallback_endpoints = (
            self._split_csv(self.fallback_override)
            if self.fallback_override is not None
            else tuple(gemini_defaults.fallback_endpoints)
        )
        model = self.model_override or gemini_defaults.model
        request_timeout = (
            float(self.request_timeout_override)
            if self.request_timeout_override is not None
            else float(gemini_defaults.request_timeout_seconds)
        )
        heartbeat_interval = (
            float(self.heartbeat_override)
            if self.heartbeat_override is not None
            else float(gemini_defaults.heartbeat_interval_seconds)
        )
        max_retries = (
            int(self.max_retries_override)
            if self.max_retries_override is not None
            else int(gemini_defaults.max_retries)
        )
        backoff_base = (
            float(self.backoff_base_override)
            if self.backoff_base_override is not None
            else float(gemini_defaults.backoff.factor)
        )
        backoff_max = (
            float(self.backoff_max_override)
            if self.backoff_max_override is not None
            else float(gemini_defaults.backoff.max_delay_seconds)
        )

        return GeminiStreamConfig(
            api_key=self.api_key,
            model=model,
            endpoint=endpoint,
            request_timeout=request_timeout,
            heartbeat_interval=heartbeat_interval,
            max_retries=max_retries,
            backoff_base=backoff_base,
            backoff_max=backoff_max,
            fallback_endpoints=fallback_endpoints,
        )


__all__ = ["ProjectSettings", "GeminiEnvironment"]
