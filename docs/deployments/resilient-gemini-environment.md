# Resilient Gemini Environment Deployment

This document captures the production deployment profile for the **Rodex Multi-agent AI Coding Platform** when targeting the
Vercel Sandbox runtime. The goal is to keep the source code identical to the current repository snapshot while refreshing the
project settings to align with the latest Gemini resilience requirements.

## Deployment Overview

- **Name:** Resilient Gemini Environment
- **Slug:** `resilient-gemini-environment`
- **Environment:** Production
- **Runtime:** Vercel Sandbox (`provider: vercel`, `product: sandbox`, `region: iad1`)
- **Primary Focus:** High-availability Gemini streaming for planner agents with automated failover across Google regions.

## Key Capabilities

1. **Multi-agent Orchestration** – Planner and automation services share the existing codebase but bootstrap configuration from
   the new `configs/project_settings.json` manifest.
2. **Gemini Stream Failover** – The planner leverages multiple Gemini streaming endpoints. When the primary endpoint fails, the
   client automatically retries against secondary regions before exhausting the retry budget.
3. **Telemetry First** – OTLP exporters are enabled via project settings so request, trace, and heartbeat data are ingested into
   the existing observability pipeline.
4. **Redis-backed Coordination** – Default environment variables point to the production Redis instance for caching plan state and
   heartbeats.

## Configuration Artifacts

| File | Purpose |
| --- | --- |
| `configs/project_settings.json` | Canonical manifest describing the deployment metadata, runtime, observability, and Gemini defaults. |
| `services/planner/project_settings.py` | Loads the manifest, applies environment overrides, and emits `GeminiStreamConfig` instances. |
| `tests/test_project_settings.py` | Regression coverage ensuring the manifest and override logic remain stable. |

## Gemini Environment Behaviour

The new `GeminiEnvironment` helper merges runtime overrides (environment variables) with the defaults provided in the project
settings manifest. Resulting configuration is fed into `GeminiStreamClient`, which now:

- Rotates through `fallback_endpoints` when connection attempts fail.
- Emits structured retry logs that include the endpoint attempted and delay chosen.
- Preserves existing retry, heartbeat, and accumulation semantics from the prior implementation.

## Operational Checklist

1. Sync secrets (`GEMINI_API_KEY`, Redis credentials) into the Vercel Sandbox project.
2. Deploy the application using the existing CI workflow; no source changes beyond configuration are required.
3. Validate streaming resilience by simulating regional outages and confirming failover to the alternate Gemini endpoints.
4. Monitor OTLP metrics to ensure heartbeat cadence and retry counts stay within expected thresholds.

With these updates, the Rodex platform can be redeployed using the same code but with hardened Gemini connectivity tailored for
production workloads on the Vercel Sandbox.
