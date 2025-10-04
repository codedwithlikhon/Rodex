"""Integration tests for the landing FastAPI application."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from services.planner.landing_api import (
    Branch,
    LandingDataStore,
    Task,
    TaskCollection,
    TaskDiff,
    Workspace,
    create_app,
)


def _build_store(task_count: int = 3) -> LandingDataStore:
    """Return a data store with deterministic workspaces and tasks."""

    workspace = Workspace(
        id="monorepo",
        name="Monorepo",
        branches=[Branch(id="main", label="main", is_default=True)],
    )
    created_at = datetime(2025, 1, 26, 22, 10, tzinfo=timezone.utc)
    tasks = [
        Task(
            id=f"task_{index:03d}",
            title=f"Task {index}",
            status="merged" if index % 2 == 0 else "in_review",
            repo="monorepo",
            branch="main",
            created_at=created_at,
            diff=TaskDiff(added=index, removed=index // 2),
        )
        for index in range(task_count)
    ]
    task_map = {("monorepo", "main", TaskCollection.ACTIVE): tasks}
    return LandingDataStore(workspaces=[workspace], tasks=task_map)


def test_get_workspaces_returns_cache_headers() -> None:
    client = TestClient(create_app(_build_store()))

    response = client.get("/api/workspaces")

    assert response.status_code == 200
    assert response.json()["workspaces"][0]["id"] == "monorepo"
    assert "ETag" in response.headers
    assert response.headers["Cache-Control"].startswith("public")


def test_get_tasks_supports_cursor_pagination() -> None:
    # request more tasks than the default page size (25) to surface pagination
    client = TestClient(create_app(_build_store(task_count=30)))

    first_page = client.get(
        "/api/tasks",
        params={"workspace": "monorepo", "branch": "main", "status": "active"},
    )

    assert first_page.status_code == 200
    body = first_page.json()
    assert len(body["tasks"]) == 25
    assert body["next_cursor"] == "25"

    second_page = client.get(
        "/api/tasks",
        params={
            "workspace": "monorepo",
            "branch": "main",
            "status": "active",
            "cursor": body["next_cursor"],
        },
    )

    assert second_page.status_code == 200
    assert len(second_page.json()["tasks"]) == 5
    assert second_page.json()["next_cursor"] is None


def test_get_tasks_unknown_workspace_returns_404() -> None:
    client = TestClient(create_app(_build_store()))

    response = client.get(
        "/api/tasks",
        params={"workspace": "missing", "branch": "main", "status": "active"},
    )

    assert response.status_code == 404


def test_submit_prompt_returns_job_id() -> None:
    client = TestClient(create_app(_build_store()))

    submission = {
        "workspace_id": "monorepo",
        "branch_id": "main",
        "mode": "code",
        "prompt": "Summarise the latest automation fixes.",
    }
    response = client.post("/api/prompts", json=submission)

    assert response.status_code == 202
    payload = response.json()
    assert payload["job_id"].startswith("job_")
    assert "T" in payload["accepted_at"]
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"workspace_id": "monorepo", "branch_id": "missing", "mode": "code", "prompt": "text"},
        {"workspace_id": "monorepo", "branch_id": "main", "mode": "code", "prompt": "   "},
    ],
)
def test_submit_prompt_validation_errors(invalid_payload: dict[str, str]) -> None:
    client = TestClient(create_app(_build_store()))

    response = client.post("/api/prompts", json=invalid_payload)

    # 404 for unknown branches, 400 for empty prompt
    assert response.status_code in {400, 404}
