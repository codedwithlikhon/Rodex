
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

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/rodex?referralCode=YOUR_CODE)

## Quick Deploy

Click the button above to deploy Rodex to Railway. This will create:

- 🧠 Planner Service (Gemini AI orchestration)
- 🤖 Automation Service (Playwright browser automation)
- 🗄️ PostgreSQL Database
- 🚀 Redis Cache

### Post-Deployment Setup

1. Add your Gemini API key in the Railway dashboard.
2. Services will automatically connect via internal networking.
3. Access your planner API at the provided Railway URL and verify `/health`.

## Project Information

- **Project ID:** `a6b69716-cda2-46bb-961a-2e87cad4d140`
- **Railway Dashboard:** [View Project](https://railway.app/project/a6b69716-cda2-46bb-961a-2e87cad4d140)

# Rodex

This repository houses evaluation artifacts for runtime environments supporting AI-generated code execution. See [`reports/runtime_evaluation.md`](reports/runtime_evaluation.md) for the full comparison of WebContainer, managed containers, and serverless functions.
