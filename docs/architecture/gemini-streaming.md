# Gemini Streaming Integration Notes

## Objectives
- Provide low-latency, bidirectional communication between the planner and Gemini model.
- Ensure resilience through automatic reconnects, heartbeats, and backpressure-aware buffering.
- Surface telemetry for latency, token usage, and error rates.

## Connection Flow
1. Acquire API key from secrets manager and instantiate
   `GeminiStreamConfig` with model + endpoint metadata.
2. Construct a `GeminiGenerateRequest` and call
   `GeminiStreamClient.stream(...)`.
3. The client spins up `GoogleGenerativeAITransport`, which configures the
   official `google-generativeai` SDK and consumes the streaming generator in a
   background thread.
4. Streamed deltas are converted into `GeminiStreamEvent` objects (either
   `chunk`, `heartbeat`, `error`, or `complete`) that downstream planner code
   can iterate over asynchronously.
5. `GeminiTextAccumulator` can stitch together `chunk` events for quick access
   to the assembled text response.

## Error Handling & Resilience
- Exponential backoff (base 1s, doubling per attempt up to configurable max)
  is built into `GeminiStreamClient.stream`. Callers can override retry counts
  via `GeminiStreamConfig`.
- Heartbeat events are emitted on a dedicated task to detect idle streams.
- Transport-level exceptions are surfaced as `GeminiStreamError` instances
  once retry budgets are exhausted.
- TODO: Persist unsent payloads in Redis prior to reconnect to guarantee
  planner state recovery.
- TODO: Enrich events with correlation IDs and telemetry metadata for tracing.

## Testing Strategy
- Mock server that simulates message chunking, dropped frames, and rate limiting.
- Contract tests validating schema of streamed messages.
- Load test using Locust to measure throughput under concurrent planner sessions.

## Open Questions
- Should we support alternative transports (pure WebSocket vs. SSE fallback)
  in addition to the Google SDK wrapper?
- What authentication scopes + rotation cadence are mandated by the hosting
  environment?
- How should token budgeting be enforced for multi-step plans?

