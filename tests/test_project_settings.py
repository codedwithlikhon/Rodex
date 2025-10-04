"""Tests for the Gemini project settings integration."""

from __future__ import annotations

import json
import os
from importlib import resources
from pathlib import Path
import unittest
from unittest import mock

import services.planner.project_settings as project_settings_module
from services.planner.project_settings import GeminiEnvironment, ProjectSettings


class GeminiEnvironmentTests(unittest.TestCase):
    """Validate merging of project defaults with runtime overrides."""

    def setUp(self) -> None:
        self._original_env: dict[str, str | None] = {}
        self._set_env("GEMINI_API_KEY", "test-key")

    def tearDown(self) -> None:
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _set_env(self, key: str, value: str | None) -> None:
        if key not in self._original_env:
            self._original_env[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    def test_project_settings_manifest_loads(self) -> None:
        settings = ProjectSettings.load()
        self.assertEqual(settings.deployment.name, "Resilient Gemini Environment")
        self.assertEqual(settings.deployment.environment, "production")
        self.assertIn("gemini-stream-failover", settings.deployment.features)
        self.assertEqual(settings.gemini.model, "models/gemini-1.5-pro")

    def test_environment_builds_stream_config_from_defaults(self) -> None:
        env = GeminiEnvironment()
        settings = ProjectSettings.load()
        config = env.build_stream_config(settings)

        self.assertEqual(config.model, settings.gemini.model)
        self.assertEqual(config.endpoint, settings.gemini.primary_endpoint)
        self.assertEqual(config.fallback_endpoints, tuple(settings.gemini.fallback_endpoints))
        self.assertEqual(config.max_retries, settings.gemini.max_retries)
        self.assertEqual(config.backoff_base, settings.gemini.backoff.factor)
        self.assertEqual(config.backoff_max, settings.gemini.backoff.max_delay_seconds)

    def test_environment_honours_runtime_overrides(self) -> None:
        self._set_env("GEMINI_MODEL", "models/test-overrides")
        self._set_env("GEMINI_STREAM_ENDPOINT", "wss://override-endpoint")
        self._set_env("GEMINI_FALLBACK_ENDPOINTS", "wss://fallback-1, wss://fallback-2")
        self._set_env("GEMINI_REQUEST_TIMEOUT", "99")
        self._set_env("GEMINI_HEARTBEAT_INTERVAL", "7")
        self._set_env("GEMINI_MAX_RETRIES", "6")
        self._set_env("GEMINI_BACKOFF_BASE", "2.5")
        self._set_env("GEMINI_BACKOFF_MAX", "120")

        env = GeminiEnvironment()
        config = env.build_stream_config(ProjectSettings.load())

        self.assertEqual(config.model, "models/test-overrides")
        self.assertEqual(config.endpoint, "wss://override-endpoint")
        self.assertEqual(config.fallback_endpoints, ("wss://fallback-1", "wss://fallback-2"))
        self.assertEqual(config.request_timeout, 99.0)
        self.assertEqual(config.heartbeat_interval, 7.0)
        self.assertEqual(config.max_retries, 6)
        self.assertEqual(config.backoff_base, 2.5)
        self.assertEqual(config.backoff_max, 120.0)


class ProjectSettingsLoadTests(unittest.TestCase):
    """Validate loading behaviour for packaged defaults."""

    def test_project_settings_manifest_available_as_packaged_resource(self) -> None:
        packaged = resources.files("services.planner._data").joinpath("project_settings.json")
        self.assertTrue(packaged.is_file())

        with packaged.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        with Path("configs/project_settings.json").open("r", encoding="utf-8") as handle:
            repo_payload = json.load(handle)

        self.assertEqual(payload, repo_payload)

    def test_load_falls_back_to_packaged_defaults(self) -> None:
        missing_path = Path("/nonexistent/configs/project_settings.json")
        with mock.patch.object(project_settings_module, "_CONFIG_PATH", missing_path):
            settings = ProjectSettings.load()

        self.assertEqual(settings.deployment.name, "Resilient Gemini Environment")
        self.assertEqual(settings.deployment.environment, "production")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
