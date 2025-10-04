"""Placeholder entrypoint for the automation service.

This keeps the Railway deployment template functional until the
Playwright automation runtime is implemented.
"""

from __future__ import annotations

import asyncio
import logging
import os

from fastapi import FastAPI

try:
    import uvicorn
except ModuleNotFoundError:  # pragma: no cover - fallback path
    uvicorn = None  # type: ignore[assignment]

__all__ = ["app", "main"]


logger = logging.getLogger("automation")


app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a minimal health payload for deployment checks."""

    return {"status": "ok"}


async def _serve() -> None:
    """Run the FastAPI application using Uvicorn."""

    assert uvicorn is not None  # guard for type checkers
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", "8081")))
    server = uvicorn.Server(config)
    await server.serve()


async def _idle() -> None:
    """Fallback loop used when Uvicorn is unavailable."""

    logger.warning("Uvicorn is unavailable; automation service is idling.")
    while True:
        await asyncio.sleep(3600)


def main() -> None:
    """Entrypoint executed by ``python -m automation.main``."""

    if uvicorn is None:
        asyncio.run(_idle())
    else:
        asyncio.run(_serve())


if __name__ == "__main__":
    main()
