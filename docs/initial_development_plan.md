# Autonomous Web Automation Platform: Initial Development Plan

## 1. Plan Analysis
- **Foundational infrastructure**: Requires containerized runtime, IaC for environments, and shared configuration for secrets. Early setup of mono-repo structure, Python package management (Poetry/uv), and CI workflows is critical to support downstream teams.
- **AI Planning & Decision System**: Gemini streaming integration is the critical path; requires reliable bidirectional streaming client, token budgeting, and stateful planning loop. Needs telemetry and retry logic.
- **Automation Engine (Playwright)**: Depends on planner outputs. Requires isolated browser workers, task queue, and secure credential management.
- **Security & Compliance**: Must enforce secrets hygiene, audit logging, and RBAC; can run in parallel with automation engine work once infra scaffolding exists.
- **Delivery Milestones**: 12-week plan with early emphasis on core planner/automation loop and Gemini streaming fix.
- **Risks**: Streaming instability, environment drift, and multi-tenant security.

## 2. Highest-Impact Starting Point
1. **Stabilize Gemini streaming client** to unblock AI planner roadmap.
2. **Bootstrap shared platform repository** with Python package structure, config templates, and CI guardrails.
3. **Lay groundwork for Playwright automation service** (env config + test harness).

## 3. Immediate Actionable Steps

### Repository Structure to Create
```
.
├── docs/
│   └── architecture/
├── infra/
│   ├── docker/
│   └── terraform/
├── services/
│   ├── planner/
│   │   ├── __init__.py
│   │   └── gemini_stream.py
│   └── automation/
│       └── __init__.py
├── configs/
│   ├── base.env
│   └── playwright.config.ts
└── pyproject.toml
```

### Files to Create/Populate Today
- `pyproject.toml`: Declare workspace packages, dependencies (`google-generativeai`, `websockets`, `fastapi`, `playwright`, `pydantic`, `structlog`).
- `services/planner/gemini_stream.py`: Implement streaming client wrapper with reconnection, heartbeats, and incremental token assembly.
- `configs/base.env`: Template environment variables (`GEMINI_API_KEY`, streaming endpoints, telemetry toggles).
- `configs/playwright.config.ts`: Baseline config enabling headed/headless modes, tracing, and secure storage path.
- `infra/docker/Dockerfile.base`: Base image with Python 3.11, Playwright deps, `uv` installer, non-root user.
- `infra/terraform/main.tf`: Placeholder for environment modules referencing secrets manager + logging.
- `docs/architecture/gemini-streaming.md`: Document protocol expectations, retries, budgeting.

### Commands to Run
```bash
uv init --package rodex-platform
uv add fastapi google-generativeai websockets structlog httpx pydantic-settings playwright
npx playwright install-deps
npx playwright install chromium
```

### Gemini Streaming Fix (Priority)
- Implement async streaming client that:
  - Uses Gemini streaming endpoint via WebSocket (or HTTP chunked response if required).
  - Supports **adaptive chunk aggregation** with token limit awareness.
  - Emits planning events over `asyncio.Queue` for downstream planner.
  - Implements exponential backoff on disconnect with jitter, max retries configurable.
  - Persists conversation context to Redis (via planned `rodex.core.state` module).
- Add integration test scaffold invoking mock Gemini server to validate reconnect & message ordering.

### Parallelizable Tasks
- **Container 1**: Build Python package + Gemini client implementation.
- **Container 2**: Set up Docker base image and Playwright dependencies.
- **Container 3**: Draft Terraform scaffolding and CI workflow (GitHub Actions) concurrently.

### Immediate Blockers/Dependencies
- Access to Gemini streaming API specs + authentication flow.
- Decide on package manager (`uv` vs. Poetry) and align team tooling.
- Secure secrets storage (Vault/GCP Secret Manager) before connecting to live Gemini endpoints.

## 4. 24-48 Hour Work Breakdown

### Day 1 (Hours 0-24)
1. **Repo Bootstrap (4h)**
   - Initialize `pyproject.toml` with core dependencies and local dev scripts.
   - Add pre-commit config (formatting, linting) and CI pipeline skeleton.
2. **Gemini Streaming Client Skeleton (6h)**
   - Implement `GeminiStreamClient` with connection lifecycle management.
   - Write unit tests covering handshake, heartbeat, reconnection.
3. **Config & Secrets Templates (2h)**
   - Populate `.env` templates, document required environment variables.
4. **Automation Engine Setup (3h)**
   - Create Playwright config, sample task runner stub.

### Day 2 (Hours 24-48)
1. **Streaming Integration Testing (6h)**
   - Build mock Gemini server, run end-to-end streaming tests.
2. **Planner-Orchestrator Interface (4h)**
   - Define `PlanningEvent` dataclasses and event bus contract.
3. **Docker & Infra Scaffolding (4h)**
   - Author base Dockerfile, GitHub Actions workflow for image build.
4. **Security Foundations (2h)**
   - Draft RBAC matrix & audit logging requirements in docs.
5. **Backlog Grooming (2h)**
   - Capture follow-up tickets for telemetry, rate limiting, compliance tasks.

## 5. Next Deliverables
- Merge initial repo scaffolding with streaming client skeleton & docs.
- Establish CI checks (lint, tests) to guard future PRs.
- Prepare design review doc for Gemini integration before implementing advanced planning features.

