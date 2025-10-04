# Feature Opportunities for the Rodex Platform

This document expands on three strategic investments that can elevate the resiliency and usability of the Rodex platform. Each section recaps the motivating problem, points to the existing building blocks within the repository, and outlines measurable success criteria.

## 1. Automated Template Update Validation Pipeline

### Why it Matters
- Railway template updates currently land without automated regression protection, increasing the risk of shipping broken planner or landing flows.

### Existing Building Blocks
- Automation service scaffold: `services/automation/main.py`
- Deployment walkthrough detailing planner and landing endpoints: `README.md`

### Implementation Steps
1. Extend the automation service entry point so it can execute scripted smoke tests against the preview deployment created for template update PRs.
2. Wire Railway PR deploys to call the automation runner, capturing pass/fail results and storing logs plus artifacts (screenshots, HAR files).
3. Emit GitHub Check annotations summarizing the validation matrix to surface actionable feedback for reviewers.

### Dependencies & Risks
- Requires credentials for preview environments and secure object storage.
- Playwright suites can extend CI runtime; prioritize a deterministic, minimal coverage set.

### Success Indicators
- Every template update PR shows validation status before review.
- Mean review time drops because reviewers trust the automated signal.

## 2. Gemini Streaming Observability Dashboard

### Why it Matters
- Gemini streaming reliability issues are difficult to diagnose without aggregated telemetry, prolonging incidents and masking regressions.

### Existing Building Blocks
- Streaming client implementation: `services/planner/gemini_stream.py`
- Planner configuration surface for observability sinks: `services/planner/project_settings.py`

### Implementation Steps
1. Instrument the Gemini streaming client with counters and histograms capturing retry attempts, fallback usage, and latency distributions.
2. Add tracing hooks around prompt planning flows so degraded streaming performance can be correlated with downstream automation impact.
3. Publish the telemetry to the chosen metrics backend (e.g., OpenTelemetry exporter) and build Grafana/DataDog dashboards plus alerting rules.

### Dependencies & Risks
- Instrumentation must avoid blocking the streaming loop; prefer async-safe emission.
- Metric naming should follow existing observability conventions to simplify adoption.

### Success Indicators
- Incident detection time decreases thanks to actionable dashboards.
- Post-incident reviews cite dashboard insights when diagnosing root causes.

## 3. Landing Prompt-to-Execution Feedback Loop

### Why it Matters
- The landing API stores prompt context in memory only, leaving users without visibility into automation progress after receiving a `job_id`.

### Existing Building Blocks
- Landing API implementation: `services/planner/landing_api.py`

### Implementation Steps
1. Persist prompt submissions and job metadata to a durable store (Redis or Postgres) via a planner-owned storage adapter.
2. Emit lifecycle events (queued, running, succeeded, failed) from automation jobs that the landing API can relay via SSE or WebSockets.
3. Update the frontend to display real-time progress, including links to generated artifacts or diffs.

### Dependencies & Risks
- Real-time endpoints require authentication, rate limiting, and data retention policies aligned with privacy expectations.
- Streaming updates must degrade gracefully if clients disconnect or transports are unavailable.

### Success Indicators
- Users see immediate automation status without manual refreshes.
- Support volume decreases as customers self-serve via transparent execution tracking.
