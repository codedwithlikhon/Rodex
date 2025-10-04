
# Rodex Autonomous Web Automation Platform

This repository contains the scaffolding and initial planning artifacts for the Rodex autonomous web automation platform. The immediate focus is resolving the Gemini streaming reliability issues while laying down infrastructure for the Playwright-based automation engine.

## Repository Layout
- `docs/` – Planning artifacts and architecture notes.
- `services/` – Python packages for planner and automation services.
- `configs/` – Environment and tooling configuration templates.
- `infra/` – Docker and Terraform infrastructure scaffolding.
- `tests/` – Placeholder for automated test suites.

## Getting Started
1. Create a virtual environment (recommended via `uv` or `poetry`).
2. Install base dependencies:
   ```bash
   pip install -e .[planner,automation]
   ```
3. Copy `configs/base.env` to `.env` and populate secrets.
4. Review `configs/project_settings.json` for deployment metadata and Gemini
   defaults. The same manifest ships inside the package so runtime environments
   always have sane defaults; override via environment variables or secret
   manager entries when deploying to non-local environments.
5. Install Playwright browsers:
   ```bash
   npx playwright install-deps
   npx playwright install chromium
   ```

## Next Steps
Refer to `docs/initial_development_plan.md` for a detailed 48-hour work breakdown and prioritized tasks.

# Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YOUR_TEMPLATE_ID)

### What gets deployed
- **Planner Service** – Gemini-powered planning API exposed via FastAPI.
- **Automation Service** – Playwright automation runtime with shared browser cache.
- **PostgreSQL** – Primary relational datastore for planner and automation jobs.
- **Redis** – Shared cache and queue backend.

### Post-deployment checklist
1. Set the `GEMINI_API_KEY` secret on the planner service (it propagates to automation).
2. Confirm that `planner` and `automation` services resolve to each other using their private domains.
3. Tail the planner logs to verify that health checks succeed before inviting consumers.

# Rodex

This repository houses evaluation artifacts for runtime environments supporting AI-generated code execution. See [`reports/runtime_evaluation.md`](reports/runtime_evaluation.md) for the full comparison of WebContainer, managed containers, and serverless functions.
