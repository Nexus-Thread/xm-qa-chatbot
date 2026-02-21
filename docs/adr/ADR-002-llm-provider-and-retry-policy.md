# ADR-002: LLM Provider and Retry Policy

## Context
The chatbot depends on an LLM for structured extraction of project identifiers, reporting windows, and coverage metrics from free-form conversation text. This integration has two architectural risks:
- provider lock-in if use cases depend directly on a single SDK,
- unstable runtime behavior if transient transport failures are not handled consistently.

The solution must keep infrastructure concerns out of the application layer and allow different OpenAI-compatible endpoints (local or hosted) through configuration.

## Decision
Use an OpenAI-compatible adapter stack with explicit boundary separation:
- `OpenAIStructuredExtractionAdapter` implements `StructuredExtractionPort` for application use cases,
- OpenAI transport concerns (request execution and retry behavior) remain in `adapters/output/llm/openai/transport.py`,
- retry policy uses capped retries with exponential backoff,
- settings (`base_url`, `api_key`, `model`, retry/timeouts) are externalized and injected.

Adapter-layer exceptions are translated into extraction-layer errors before crossing back into application flows.

## Consequences
- Positive:
  - Use cases remain provider-agnostic via `StructuredExtractionPort`.
  - Retry and backoff behavior is centralized close to external I/O.
  - Local development can use OpenAI-compatible local endpoints without changing core logic.
- Trade-offs:
  - The adapter still assumes OpenAI-compatible payload shape and semantics.
  - Additional mapping/validation logic is required to transform model output into domain values.
  - Misconfigured retry values can increase latency under partial outages.
- Follow-up implications:
  - New providers should be integrated as additional adapters behind the same port contract.
  - Operational tuning (timeouts/retry counts) should be revisited with production telemetry.

## Alternatives
- Direct OpenAI SDK calls from use cases.
- Provider-specific integrations with no shared output port contract.
- No retry strategy (fail-fast on first transport error).
