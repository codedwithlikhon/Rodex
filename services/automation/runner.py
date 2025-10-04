"""Utility helpers for executing automation commands sequentially."""

from __future__ import annotations

import asyncio
import logging
import shlex
import time
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Sequence

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CommandSpec:
    """Serializable definition of a command to execute."""

    label: str
    argv: Sequence[str]
    allow_failure: bool = False
    env: Mapping[str, str] | None = None
    timeout: float | None = None

    @classmethod
    def from_config(cls, value: object) -> "CommandSpec":
        """Create a command specification from configuration input."""

        if isinstance(value, CommandSpec):
            return value
        if isinstance(value, str):
            argv = shlex.split(value)
            return cls(label=value, argv=argv)
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
            argv = [str(item) for item in value]
            label = " ".join(argv)
            return cls(label=label, argv=argv)
        if isinstance(value, Mapping):
            if "command" not in value:
                raise ValueError("Command configuration requires a 'command' field")
            raw_command = value["command"]
            if isinstance(raw_command, str):
                argv = shlex.split(raw_command)
            elif isinstance(raw_command, Sequence):
                argv = [str(item) for item in raw_command]
            else:  # pragma: no cover - defensive branch
                raise TypeError("Unsupported command specification type")
            label = str(value.get("label") or value.get("name") or " ".join(argv))
            allow_failure = bool(value.get("allow_failure", False))
            env_value = value.get("env")
            env: Mapping[str, str] | None
            if env_value is None:
                env = None
            elif isinstance(env_value, Mapping):
                env = {str(key): str(val) for key, val in env_value.items()}
            else:  # pragma: no cover - defensive branch
                raise TypeError("Environment overrides must be provided as a mapping")
            timeout = value.get("timeout")
            timeout_value = float(timeout) if timeout is not None else None
            return cls(
                label=label,
                argv=argv,
                allow_failure=allow_failure,
                env=env,
                timeout=timeout_value,
            )
        raise TypeError(f"Unsupported command specification: {value!r}")


@dataclass(slots=True)
class CommandResult:
    """Outcome of a command execution."""

    label: str
    argv: Sequence[str]
    returncode: int
    stdout: str
    stderr: str
    duration: float
    allow_failure: bool
    timed_out: bool

    @property
    def passed(self) -> bool:
        """Return ``True`` when the command completed successfully."""

        if self.timed_out:
            return self.allow_failure
        if self.returncode == 0:
            return True
        return self.allow_failure

    @property
    def exit_code(self) -> int:
        """Return the exit code representing this result."""

        if self.returncode != 0:
            return self.returncode
        return 0


class CommandRunner:
    """Execute shell commands sequentially with optional failure handling."""

    def __init__(
        self,
        *,
        base_env: Mapping[str, str] | None = None,
        stop_on_failure: bool = True,
        default_timeout: float | None = None,
    ) -> None:
        self._base_env = dict(base_env or {})
        self._stop_on_failure = stop_on_failure
        self._default_timeout = default_timeout

    async def run(self, commands: Sequence[CommandSpec]) -> list[CommandResult]:
        results: list[CommandResult] = []
        for spec in commands:
            result = await self._execute(spec)
            results.append(result)
            if not result.passed and self._stop_on_failure and not spec.allow_failure:
                break
        return results

    def run_sync(self, commands: Sequence[CommandSpec]) -> list[CommandResult]:
        """Synchronously execute commands for imperative callers."""

        return asyncio.run(self.run(commands))

    async def _execute(self, spec: CommandSpec) -> CommandResult:
        env: MutableMapping[str, str] = dict(self._base_env)
        if spec.env:
            env.update(spec.env)

        timeout = spec.timeout if spec.timeout is not None else self._default_timeout
        start = time.perf_counter()
        try:
            process = await asyncio.create_subprocess_exec(
                *spec.argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except FileNotFoundError as exc:  # pragma: no cover - exercised via tests indirectly
            duration = time.perf_counter() - start
            logger.error("Command failed to spawn", exc_info=exc)
            return CommandResult(
                label=spec.label,
                argv=spec.argv,
                returncode=127,
                stdout="",
                stderr=str(exc),
                duration=duration,
                allow_failure=spec.allow_failure,
                timed_out=False,
            )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            timed_out = False
        except asyncio.TimeoutError:
            process.kill()
            stdout_bytes, stderr_bytes = await process.communicate()
            timed_out = True

        duration = time.perf_counter() - start
        stdout = stdout_bytes.decode()
        stderr = stderr_bytes.decode()
        returncode = process.returncode if process.returncode is not None else 1

        if timed_out:
            logger.error("Command timed out", extra={"label": spec.label, "timeout": timeout})
        elif returncode != 0:
            logger.error("Command failed", extra={"label": spec.label, "returncode": returncode})
        else:
            logger.info("Command succeeded", extra={"label": spec.label, "duration": duration})

        return CommandResult(
            label=spec.label,
            argv=spec.argv,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            allow_failure=spec.allow_failure,
            timed_out=timed_out,
        )


def format_summary(results: Sequence[CommandResult]) -> str:
    """Return a human-readable summary of command execution results."""

    lines = []
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"[{status}] {result.label} ({result.duration:.2f}s)")
        if result.stdout.strip():
            lines.append("  stdout:")
            for line in result.stdout.strip().splitlines():
                lines.append(f"    {line}")
        if result.stderr.strip():
            lines.append("  stderr:")
            for line in result.stderr.strip().splitlines():
                lines.append(f"    {line}")
    return "\n".join(lines)
