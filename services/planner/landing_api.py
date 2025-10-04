"""FastAPI application exposing the landing page data contract.

The previous iteration of this repository only contained planning documents
describing the desired API shape for the landing experience.  This module
implements those contracts so that the frontend can interact with a working
service.  The implementation keeps the data store pluggable which allows unit
tests to exercise behaviour without relying on network calls or external
databases.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, MutableMapping, Sequence

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

__all__ = [
    "Branch",
    "LandingDataStore",
    "PromptResponse",
    "PromptSubmission",
    "Task",
    "TaskCollection",
    "TaskDiff",
    "TasksResponse",
    "WorkspacesResponse",
    "Workspace",
    "create_app",
]


class Branch(BaseModel):
    """Represents a workspace branch that can be targeted by prompts."""

    id: str
    label: str
    is_default: bool = False


class Workspace(BaseModel):
    """Workspace surfaced on the landing page selector."""

    id: str
    name: str
    branches: list[Branch]


class WorkspacesResponse(BaseModel):
    """Envelope returned by the ``/api/workspaces`` endpoint."""

    workspaces: list[Workspace]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskDiff(BaseModel):
    """Diff metadata rendered on task cards."""

    added: int = Field(ge=0)
    removed: int = Field(ge=0)


class Task(BaseModel):
    """Task model displayed within the landing screen."""

    id: str
    title: str
    status: str
    repo: str
    branch: str
    created_at: datetime
    merged_at: datetime | None = None
    diff: TaskDiff


class TaskCollection(str, Enum):
    """Logical grouping of tasks for filtering."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class TasksResponse(BaseModel):
    """Response payload returned by ``/api/tasks``."""

    tasks: list[Task]
    next_cursor: str | None = None


class PromptSubmission(BaseModel):
    """Incoming payload accepted by the ``/api/prompts`` endpoint."""

    workspace_id: str
    branch_id: str
    mode: str = Field(pattern="^(ask|code)$")
    prompt: str

    def normalised_prompt(self) -> str:
        """Return the trimmed prompt text."""

        return self.prompt.strip()


class PromptResponse(BaseModel):
    """Response returned after a prompt submission is accepted."""

    job_id: str
    accepted_at: datetime


class LandingDataStore:
    """In-memory backing store that fulfils landing API queries."""

    def __init__(
        self,
        *,
        workspaces: Sequence[Workspace] | None = None,
        tasks: Mapping[tuple[str, str, TaskCollection], Sequence[Task]] | None = None,
    ) -> None:
        self._workspaces: list[Workspace] = [
            workspace.model_copy(deep=True)
            for workspace in (workspaces if workspaces is not None else self._default_workspaces())
        ]
        self._workspace_index: dict[str, Workspace] = {ws.id: ws for ws in self._workspaces}
        default_tasks = tasks if tasks is not None else self._default_tasks()
        self._tasks: dict[tuple[str, str, TaskCollection], list[Task]] = {}
        for key, collection in default_tasks.items():
            self._tasks[key] = [task.model_copy(deep=True) for task in collection]

    # ------------------------------------------------------------------
    # Default dataset used when no external source is provided

    def _default_workspaces(self) -> list[Workspace]:
        return [
            Workspace(
                id="monorepo",
                name="Monorepo",
                branches=[
                    Branch(id="main", label="main", is_default=True),
                    Branch(id="experimental", label="experimental"),
                ],
            )
        ]

    def _default_tasks(self) -> MutableMapping[tuple[str, str, TaskCollection], list[Task]]:
        created = datetime(2025, 1, 26, 22, 10, tzinfo=timezone.utc)
        merged = datetime(2025, 1, 26, 23, 45, tzinfo=timezone.utc)
        return {
            ("monorepo", "main", TaskCollection.ACTIVE): [
                Task(
                    id="task_123",
                    title="Diagnose issues with status updates",
                    status="in_review",
                    repo="monorepo",
                    branch="main",
                    created_at=created,
                    diff=TaskDiff(added=76, removed=47),
                ),
                Task(
                    id="task_124",
                    title="Document Gemini streaming mitigation plan",
                    status="draft",
                    repo="monorepo",
                    branch="main",
                    created_at=created,
                    diff=TaskDiff(added=12, removed=3),
                ),
            ],
            ("monorepo", "main", TaskCollection.ARCHIVED): [
                Task(
                    id="task_120",
                    title="Stabilise WebSocket reconnect flow",
                    status="merged",
                    repo="monorepo",
                    branch="main",
                    created_at=created,
                    merged_at=merged,
                    diff=TaskDiff(added=33, removed=5),
                )
            ],
        }

    # ------------------------------------------------------------------
    # Public API used by the FastAPI routes

    def workspaces(self) -> list[Workspace]:
        """Return a deep copy of the known workspaces."""

        return [workspace.model_copy(deep=True) for workspace in self._workspaces]

    def workspaces_etag(self) -> str:
        """Stable ETag derived from the workspace payload."""

        payload = [ws.model_dump(mode="json", round_trip=True) for ws in self._workspaces]
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8"))
        return digest.hexdigest()

    def list_tasks(
        self,
        workspace_id: str,
        branch_id: str,
        collection: TaskCollection,
        *,
        cursor: str | None = None,
        page_size: int = 25,
    ) -> tuple[list[Task], str | None]:
        """Return tasks for the given selection along with an optional cursor."""

        workspace = self._workspace_index.get(workspace_id)
        if workspace is None:
            raise KeyError("workspace_not_found")

        branch_ids = {branch.id for branch in workspace.branches}
        if branch_id not in branch_ids:
            raise KeyError("branch_not_found")

        key = (workspace_id, branch_id, collection)
        collection_tasks = self._tasks.get(key, [])

        start_index = 0
        if cursor:
            try:
                start_index = int(cursor)
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError("invalid_cursor") from exc
            if start_index < 0:
                raise ValueError("invalid_cursor")

        end_index = start_index + page_size
        page = [task.model_copy(deep=True) for task in collection_tasks[start_index:end_index]]
        next_cursor = str(end_index) if end_index < len(collection_tasks) else None
        return page, next_cursor

    def create_prompt(self, submission: PromptSubmission) -> PromptResponse:
        """Validate and record a prompt submission."""

        workspace = self._workspace_index.get(submission.workspace_id)
        if workspace is None:
            raise KeyError("workspace_not_found")

        if submission.branch_id not in {branch.id for branch in workspace.branches}:
            raise KeyError("branch_not_found")

        prompt_text = submission.normalised_prompt()
        if not prompt_text:
            raise ValueError("prompt_required")

        job_id = f"job_{uuid.uuid4().hex}"
        return PromptResponse(job_id=job_id, accepted_at=datetime.now(timezone.utc))


def create_app(data_store: LandingDataStore | None = None) -> FastAPI:
    """Instantiate the FastAPI application exposing the landing endpoints."""

    store = data_store or LandingDataStore()
    app = FastAPI(title="Rodex Landing API", version="1.0.0")

    @app.get("/api/workspaces", response_model=WorkspacesResponse)
    def get_workspaces() -> JSONResponse:
        response_model = WorkspacesResponse(workspaces=store.workspaces())
        payload = response_model.model_dump(mode="json")
        headers = {
            "Cache-Control": "public, max-age=300, must-revalidate",
            "ETag": store.workspaces_etag(),
        }
        return JSONResponse(content=payload, headers=headers)

    @app.get("/api/tasks", response_model=TasksResponse)
    def get_tasks(
        workspace: str = Query(..., description="Workspace identifier"),
        branch: str = Query(..., description="Branch identifier"),
        collection: TaskCollection = Query(
            ..., alias="status", description="Collection filter"
        ),
        cursor: str | None = Query(None, description="Pagination cursor"),
    ) -> JSONResponse:
        try:
            tasks, next_cursor = store.list_tasks(
                workspace, branch, collection, cursor=cursor
            )
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        payload = TasksResponse(tasks=tasks, next_cursor=next_cursor).model_dump(mode="json")
        return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})

    @app.post(
        "/api/prompts",
        response_model=PromptResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def submit_prompt(submission: PromptSubmission) -> JSONResponse:
        try:
            result = store.create_prompt(submission)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        return JSONResponse(
            content=result.model_dump(mode="json"),
            status_code=status.HTTP_202_ACCEPTED,
            headers={"Cache-Control": "no-store"},
        )

    return app

