from __future__ import annotations

import sys
from pathlib import Path

import json

from services.automation.runner import CommandRunner, CommandSpec, format_summary
from services.automation.main import _load_commands_from_file


def _python_cmd(code: str) -> CommandSpec:
    return CommandSpec.from_config([sys.executable, "-c", code])


def test_command_runner_executes_in_sequence(tmp_path: Path) -> None:
    runner = CommandRunner(stop_on_failure=True, base_env={})
    commands = [
        _python_cmd("print('first')"),
        CommandSpec.from_config(
            {
                "command": [sys.executable, "-c", "import os; print(os.environ['SMOKE_TOKEN'])"],
                "env": {"SMOKE_TOKEN": "demo"},
            }
        ),
    ]

    results = runner.run_sync(commands)

    assert len(results) == 2
    assert results[0].passed is True
    assert results[0].stdout.strip() == "first"
    assert results[1].stdout.strip() == "demo"


def test_command_runner_stops_on_failure() -> None:
    runner = CommandRunner(stop_on_failure=True, base_env={})
    commands = [
        _python_cmd("import sys; sys.exit(2)"),
        _python_cmd("print('should not run')"),
    ]

    results = runner.run_sync(commands)

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].returncode == 2


def test_command_runner_honors_allow_failure() -> None:
    runner = CommandRunner(stop_on_failure=True, base_env={})
    commands = [
        CommandSpec.from_config(
            {
                "command": [sys.executable, "-c", "import sys; sys.exit(3)"],
                "allow_failure": True,
            }
        ),
        _python_cmd("print('executed')"),
    ]

    results = runner.run_sync(commands)

    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].stdout.strip() == "executed"


def test_command_spec_from_json_file(tmp_path: Path) -> None:
    payload = {
        "commands": [
            {
                "label": "say",
                "command": [sys.executable, "-c", "print('hi')"],
            }
        ]
    }
    path = tmp_path / "commands.json"
    path.write_text(json.dumps(payload))

    specs = _load_commands_from_file(path)
    runner = CommandRunner(base_env={})
    results = runner.run_sync(specs)

    assert results[0].passed is True
    assert results[0].stdout.strip() == "hi"


def test_format_summary_includes_output() -> None:
    runner = CommandRunner(base_env={})
    commands = [_python_cmd("print('summary')")]
    results = runner.run_sync(commands)

    summary = format_summary(results)

    assert "summary" in summary
