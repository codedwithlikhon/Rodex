"""High-reliability Gemini streaming client implementation.

This module provides a production-ready streaming wrapper around the Gemini
Generative AI API.  It improves upon the previous skeleton by adding:

* configurable retry and exponential backoff handling
* heartbeat emission so downstream planners can detect stalled streams
* integration with the official ``google-generativeai`` client library
* text accumulation helpers for simplified consumer usage

The implementation keeps the transport layer pluggable to support unit testing
and future protocol extensions (e.g. mock transports, SSE/WebSocket variants).
"""

from __future__ import annotations

import abc
import asyncio
import contextlib
import dataclasses
import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from typing import Any, Mapping, MutableMapping, Optional

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data models


@dataclasses.dataclass(slots=True)
class GeminiStreamConfig:
    """Configuration parameters controlling Gemini streaming behaviour."""

    api_key: str
    model: str
    endpoint: Optional[str] = None
    request_timeout: float = 30.0
    heartbeat_interval: float = 20.0
    max_retries: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 30.0
    client_options: Optional[Mapping[str, Any]] = None


@dataclasses.dataclass(slots=True)
class GeminiGenerateRequest:
    """Represents a streaming generation request to Gemini."""

    contents: Sequence[Any]
    system_instruction: Optional[str] = None
    tools: Optional[Sequence[Mapping[str, Any]]] = None
    tool_config: Optional[Mapping[str, Any]] = None
    generation_config: Optional[Mapping[str, Any]] = None
    safety_settings: Optional[Sequence[Mapping[str, Any]]] = None
    request_options: Optional[MutableMapping[str, Any]] = None


@dataclasses.dataclass(slots=True)
class GeminiStreamEvent:
    """Event emitted during streaming."""

    event: str
    text: Optional[str] = None
    raw: Optional[Mapping[str, Any]] = None
    timestamp: float = dataclasses.field(default_factory=lambda: time.time())


@dataclasses.dataclass(slots=True)
class GeminiTextAccumulator:
    """Helper that stitches ``GeminiStreamEvent`` chunks into a final string."""

    _parts: list[str] = dataclasses.field(default_factory=list)

    def push(self, event: GeminiStreamEvent) -> None:
        if event.event == "chunk" and event.text:
            self._parts.append(event.text)

    @property
    def text(self) -> str:
        return "".join(self._parts)


# ---------------------------------------------------------------------------
# Transport abstraction


class StreamingTransport(abc.ABC):
    """Protocol for a Gemini transport implementation."""

    async def __aenter__(self) -> "StreamingTransport":  # pragma: no cover - interface stub
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - interface stub
        return None

    @abc.abstractmethod
    async def iter_messages(self) -> AsyncIterator[GeminiStreamEvent]:
        """Yield streaming events from the underlying transport."""


class GoogleGenerativeAITransport(StreamingTransport):
    """Transport that streams tokens using ``google-generativeai``."""

    def __init__(self, config: GeminiStreamConfig, request: GeminiGenerateRequest) -> None:
        self._config = config
        self._request = request
        self._queue: asyncio.Queue[GeminiStreamEvent] | None = None
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def __aenter__(self) -> "GoogleGenerativeAITransport":
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()
        self._thread = threading.Thread(target=self._run_stream, name="gemini-stream", daemon=True)
        self._thread.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.1)
        self._thread = None
        self._queue = None
        self._loop = None

    async def iter_messages(self) -> AsyncIterator[GeminiStreamEvent]:
        if self._queue is None:
            raise RuntimeError("Transport not entered")

        while True:
            event = await self._queue.get()
            if event.event == "__end__":
                break
            yield event

    # ------------------------------------------------------------------
    # Private helpers

    def _run_stream(self) -> None:
        """Execute the synchronous Gemini streaming call in a background thread."""

        try:
            queue = self._queue
            loop = self._loop
            if queue is None or loop is None:
                return

            genai = self._import_genai()

            client_options = dict(self._config.client_options or {})
            if self._config.endpoint:
                client_options.setdefault("api_endpoint", self._config.endpoint)
            client_options.setdefault("timeout", self._config.request_timeout)

            genai.configure(api_key=self._config.api_key, client_options=client_options)

            model = genai.GenerativeModel(
                model_name=self._config.model,
                safety_settings=self._request.safety_settings,
                generation_config=self._request.generation_config,
                system_instruction=self._request.system_instruction,
                tools=self._request.tools,
                tool_config=self._request.tool_config,
            )

            request_kwargs: dict[str, Any] = {}
            if self._request.request_options:
                request_kwargs["request_options"] = dict(self._request.request_options)

            stream = model.generate_content(
                list(self._request.contents),
                stream=True,
                **request_kwargs,
            )

            for chunk in stream:
                payload = self._convert_chunk(chunk)
                self._run_coro_threadsafe(queue.put(payload), loop)

            self._run_coro_threadsafe(queue.put(GeminiStreamEvent(event="complete")), loop)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("gemini_stream.transport_error", error=str(exc))
            queue = self._queue
            loop = self._loop
            if queue is not None and loop is not None:
                error_event = GeminiStreamEvent(event="error", text=str(exc))
                self._run_coro_threadsafe(queue.put(error_event), loop)
        finally:
            queue = self._queue
            loop = self._loop
            if queue is not None and loop is not None:
                self._run_coro_threadsafe(queue.put(GeminiStreamEvent(event="__end__")), loop)

    def _run_coro_threadsafe(self, coro: Awaitable[Any], loop: asyncio.AbstractEventLoop) -> None:
        asyncio.run_coroutine_threadsafe(coro, loop)

    @staticmethod
    def _convert_chunk(chunk: Any) -> GeminiStreamEvent:
        chunk_dict = chunk.to_dict() if hasattr(chunk, "to_dict") else dict(chunk)
        text = chunk_dict.get("text") or _extract_text_from_chunk(chunk_dict)
        return GeminiStreamEvent(event="chunk", text=text or "", raw=chunk_dict)

    @staticmethod
    def _import_genai() -> Any:
        try:
            from google import generativeai as genai  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment guard
            raise RuntimeError(
                "google-generativeai is required for GoogleGenerativeAITransport"
            ) from exc
        return genai


# ---------------------------------------------------------------------------
# Client orchestration


class GeminiStreamError(RuntimeError):
    """Raised when the streaming client exhausts recovery attempts."""


class GeminiStreamClient:
    """Coordinate streaming sessions, retries, and heartbeats."""

    def __init__(self, config: GeminiStreamConfig) -> None:
        self._config = config

    async def stream(
        self,
        request: GeminiGenerateRequest,
        *,
        transport_factory: Callable[[GeminiStreamConfig, GeminiGenerateRequest], StreamingTransport]
        | None = None,
    ) -> AsyncIterator[GeminiStreamEvent]:
        """Stream Gemini events with retry semantics.

        Args:
            request: Generation payload to send to Gemini.
            transport_factory: Optional factory producing a ``StreamingTransport``.
        """

        factory = transport_factory or (lambda c, r: GoogleGenerativeAITransport(c, r))

        attempt = 0
        last_error: Exception | None = None

        while True:
            queue: asyncio.Queue[GeminiStreamEvent] = asyncio.Queue()
            heartbeat_task: asyncio.Task[None] | None = None
            pump_task = asyncio.create_task(
                self._pump_events(factory, request, queue),
                name="gemini-stream-pump",
            )

            if self._config.heartbeat_interval > 0:
                heartbeat_task = asyncio.create_task(
                    self._emit_heartbeats(queue, self._config.heartbeat_interval),
                    name="gemini-stream-heartbeat",
                )

            success = True

            try:
                while True:
                    event = await queue.get()
                    if event.event == "__end__":
                        break
                    if event.event == "error":
                        success = False
                        last_error = RuntimeError(event.text or "Unknown Gemini error")
                        break
                    yield event
            finally:
                pump_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await pump_task
                if heartbeat_task:
                    heartbeat_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await heartbeat_task

            if success:
                return

            if attempt >= self._config.max_retries:
                break

            attempt += 1
            delay = min(self._config.backoff_base * (2 ** (attempt - 1)), self._config.backoff_max)
            logger.warning(
                "gemini_stream.retrying",
                attempt=attempt,
                delay=delay,
                error=str(last_error) if last_error else None,
            )
            await asyncio.sleep(delay)

        raise GeminiStreamError("Exceeded maximum Gemini streaming retries") from last_error

    async def _pump_events(
        self,
        factory: Callable[[GeminiStreamConfig, GeminiGenerateRequest], StreamingTransport],
        request: GeminiGenerateRequest,
        queue: asyncio.Queue[GeminiStreamEvent],
    ) -> None:
        try:
            transport = factory(self._config, request)
            async with transport:
                async for event in transport.iter_messages():
                    await queue.put(event)
        except Exception as exc:  # pylint: disable=broad-except
            await queue.put(GeminiStreamEvent(event="error", text=str(exc)))
        finally:
            await queue.put(GeminiStreamEvent(event="__end__"))

    async def _emit_heartbeats(
        self, queue: asyncio.Queue[GeminiStreamEvent], interval: float
    ) -> None:
        while True:
            await asyncio.sleep(interval)
            await queue.put(GeminiStreamEvent(event="heartbeat"))


def _extract_text_from_chunk(chunk_dict: Mapping[str, Any]) -> str:
    candidates = chunk_dict.get("candidates") or []
    texts: list[str] = []
    for candidate in candidates:
        content = candidate.get("content") if isinstance(candidate, Mapping) else None
        if not content:
            continue
        parts = content.get("parts") if isinstance(content, Mapping) else None
        if not parts:
            continue
        for part in parts:
            text = part.get("text") if isinstance(part, Mapping) else None
            if text:
                texts.append(text)
    return "".join(texts)


__all__ = [
    "GeminiGenerateRequest",
    "GeminiStreamClient",
    "GeminiStreamConfig",
    "GeminiStreamError",
    "GeminiStreamEvent",
    "GeminiTextAccumulator",
    "GoogleGenerativeAITransport",
    "StreamingTransport",
]

