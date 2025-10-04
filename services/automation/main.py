"""Entrypoint and command runner for the automation service."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence

from fastapi import FastAPI

from .runner import CommandRunner, CommandSpec, format_summary

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


def _split_commands(raw: str) -> list[str]:
    """Parse command strings from the ``AUTOMATION_COMMANDS`` variable."""

    parts: list[str] = []
    for block in raw.splitlines():
        for segment in block.split(";"):
            item = segment.strip()
            if item:
                parts.append(item)
    return parts


def _load_commands_from_env() -> list[CommandSpec]:
    raw = os.getenv("AUTOMATION_COMMANDS", "").strip()
    if not raw:
        return []
    return [CommandSpec.from_config(value) for value in _split_commands(raw)]


def _load_commands_from_file(path: Path) -> list[CommandSpec]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "commands" in data:
        items = data["commands"]
    else:  # pragma: no cover - defensive branch
        raise ValueError("Unsupported automation config format")
    return [CommandSpec.from_config(item) for item in items]


def _parse_environment_overrides(items: Iterable[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items:
        key, _, value = item.partition("=")
        if not _:
            msg = f"Invalid environment override '{item}'. Expected KEY=VALUE."
            raise SystemExit(msg)
        overrides[key.strip()] = value
    return overrides


def _commands_from_args(args: argparse.Namespace) -> list[CommandSpec]:
    commands: list[CommandSpec] = []
    if args.config is not None:
        commands.extend(_load_commands_from_file(args.config))
    for command in args.command:
        commands.append(CommandSpec.from_config(command))
    if not commands:
        commands.extend(_load_commands_from_env())
    return commands


def _run_commands(args: argparse.Namespace) -> None:
    commands = _commands_from_args(args)
    if not commands:
        raise SystemExit(
            "No commands provided. Use --command, --config, or set AUTOMATION_COMMANDS."
        )

    overrides = _parse_environment_overrides(args.env)
    runner = CommandRunner(
        base_env={**os.environ, **overrides},
        stop_on_failure=not args.keep_going,
        default_timeout=args.timeout,
    )
    results = runner.run_sync(commands)
    print(format_summary(results))

    exit_code = 0 if all(result.passed for result in results) else results[-1].exit_code
    sys.exit(exit_code)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automation service utilities")
    subparsers = parser.add_subparsers(dest="mode")
    subparsers.required = False
    parser.set_defaults(mode="serve")

    subparsers.add_parser("serve", help="Run the FastAPI server")

    run_parser = subparsers.add_parser("run", help="Execute smoke test commands sequentially")
    run_parser.add_argument(
        "--command",
        "-c",
        action="append",
        default=[],
        help="Command string to execute. Accepts multiple entries.",
    )
    run_parser.add_argument(
        "--config",
        type=Path,
        help="Path to a JSON file describing commands.",
    )
    run_parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Environment overrides for the command run.",
    )
    run_parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Default timeout (in seconds) applied to each command.",
    )
    run_parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue executing commands after a failure.",
    )

    return parser


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


def main(argv: Sequence[str] | None = None) -> None:
    """Entrypoint executed by ``python -m services.automation.main``."""

    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.mode == "run":
        _run_commands(args)
    elif args.mode == "serve":
        if uvicorn is None:
            asyncio.run(_idle())
        else:
            asyncio.run(_serve())
    else:  # pragma: no cover - defensive guard
        parser.error(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
