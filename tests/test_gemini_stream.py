"""Unit tests for the Gemini streaming client."""

from __future__ import annotations

import asyncio
import unittest
from collections.abc import AsyncIterator
from typing import Sequence

from services.planner.gemini_stream import (
    GeminiGenerateRequest,
    GeminiStreamClient,
    GeminiStreamConfig,
    GeminiStreamError,
    GeminiStreamEvent,
    GeminiTextAccumulator,
    StreamingTransport,
)


class _ListTransport(StreamingTransport):
    """Transport that replays a predefined list of events."""

    def __init__(self, events: Sequence[GeminiStreamEvent]) -> None:
        self._events = list(events)

    async def __aenter__(self) -> "_ListTransport":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def iter_messages(self) -> AsyncIterator[GeminiStreamEvent]:
        for event in self._events:
            await asyncio.sleep(0)
            yield event


class _FailingTransport(StreamingTransport):
    """Transport that raises during entry to trigger retries."""

    async def __aenter__(self) -> "_FailingTransport":  # type: ignore[override]
        raise RuntimeError("boom")

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def iter_messages(self) -> AsyncIterator[GeminiStreamEvent]:  # pragma: no cover - unreachable
        yield GeminiStreamEvent(event="complete")


class GeminiStreamClientTests(unittest.IsolatedAsyncioTestCase):
    """High-level behavioural tests for ``GeminiStreamClient``."""

    async def test_stream_successfully_accumulates_chunks(self) -> None:
        config = GeminiStreamConfig(
            api_key="test-key",
            model="models/test",
            heartbeat_interval=0.0,
        )
        client = GeminiStreamClient(config)

        events = [
            GeminiStreamEvent(event="chunk", text="Hello"),
            GeminiStreamEvent(event="chunk", text=", world"),
            GeminiStreamEvent(event="complete"),
        ]

        accumulator = GeminiTextAccumulator()

        async def run() -> list[GeminiStreamEvent]:
            output: list[GeminiStreamEvent] = []
            async for event in client.stream(
                GeminiGenerateRequest(contents=[{"role": "user", "parts": [{"text": "Hi"}]}]),
                transport_factory=lambda _c, _r: _ListTransport(events),
            ):
                accumulator.push(event)
                output.append(event)
            return output

        emitted = await run()
        self.assertEqual(accumulator.text, "Hello, world")
        self.assertEqual([event.event for event in emitted], ["chunk", "chunk", "complete"])

    async def test_stream_raises_after_retry_budget_exhausted(self) -> None:
        config = GeminiStreamConfig(
            api_key="test-key",
            model="models/test",
            heartbeat_interval=0.0,
            max_retries=2,
        )
        client = GeminiStreamClient(config)

        async def consume() -> None:
            async for _ in client.stream(
                GeminiGenerateRequest(contents=[{"role": "user", "parts": [{"text": "Hi"}]}]),
                transport_factory=lambda _c, _r: _FailingTransport(),
            ):
                pass

        with self.assertRaises(GeminiStreamError):
            await consume()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

