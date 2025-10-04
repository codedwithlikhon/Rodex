"""Tests for the Gemini project settings integration."""

from __future__ import annotations

import os
import unittest

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
