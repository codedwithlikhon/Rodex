# Railway Deployment Template

This guide explains how to deploy Rodex on [Railway](https://railway.app) using the project template files added in this repository. For a higher-level primer on Railway templates—including marketplace benefits and the updatable templates flow—refer to [`railway-templates-overview.md`](./railway-templates-overview.md).

## Overview

The provided template definition and Nixpacks configuration are intended to run alongside the following Railway resources:

- **rodex-app** – FastAPI-based planner service exposed via Uvicorn.
- **PostgreSQL** – Optional relational store for persisting automation data.
- **Redis** – Optional cache layer for coordinating automation jobs.
- **Persistent volume** – Stores Playwright browser artifacts to avoid repeated downloads.

The generated deployment uses [Nixpacks](https://nixpacks.com) to install Python 3.11, Playwright dependencies, and Chromium before runtime.

## Files

| File | Purpose |
| --- | --- |
| [`railway.json`](../../railway.json) | Primary template definition used by Railway (build + deploy settings). |
| [`nixpacks.toml`](../../nixpacks.toml) | Customises the build image with required system packages. |
| [`Procfile`](../../Procfile) | Declares the `web` process that serves the FastAPI application. |
| [`.railwayignore`](../../.railwayignore) | Reduces build context by ignoring local-only artefacts. |

## Required Environment Variables

| Variable | Description |
| --- | --- |
| `GEMINI_API_KEY` | Google Gemini API key used by the planner. |
| `ENVIRONMENT` | Deployment environment indicator (defaults to `production`). |
| `PORT` | HTTP port (defaults to `8080`). |
| `PLAYWRIGHT_BROWSERS_PATH` | Location for cached Playwright browsers (`/data/playwright/browsers`). |
| `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` | Leave `0` so Chromium is installed during build. |
| `LOG_LEVEL` | Application log verbosity (defaults to `INFO`). |

When the PostgreSQL and Redis template services are included, Railway automatically injects `DATABASE_URL` and `REDIS_URL` environment variables into the application service.

## Deployment Steps

1. **Create a new Railway project** and import the Rodex repository.
2. **Set environment variables** using the Railway dashboard or CLI:
   ```bash
   railway variables set GEMINI_API_KEY=your-key-here
   railway variables set ENVIRONMENT=production LOG_LEVEL=INFO
   ```
3. **Create and attach a persistent volume** (e.g. `playwright-cache`) to `/data/playwright` so browser downloads are cached between deploys.
4. **Deploy the template**. Railway will build the image with Playwright dependencies and start the Uvicorn server.
5. **Validate the deployment**:
   ```bash
   railway run python -m playwright --version
   railway run curl "$RAILWAY_PUBLIC_DOMAIN/api/workspaces"
   ```

## Health Checks and Monitoring

- The template configures a `/health` endpoint within `services/planner/landing_api.py` for Railway’s HTTP health checks.
- Restart policy is set to retry up to 10 times on failure.
- Consider enabling Railway metrics dashboards to monitor memory usage during heavy Playwright sessions.

## Customisation Tips

- Update `Procfile` if you split the automation engine into a separate worker process.
- Modify `nixpacks.toml` to install additional system packages required by Playwright extensions.
- Use additional Railway environment groups to share secrets across environments.
- If you need more than 1 GB RAM, adjust the service plan or scale vertically.

With these files in place, new deployments can be bootstrapped quickly from the Railway template gallery or via the CLI.
