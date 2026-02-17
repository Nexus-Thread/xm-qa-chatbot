# ADR-002: LLM Provider and Retry Policy

## Context
The chatbot relies on an LLM to extract structured QA updates from conversations. We need a provider interface that can be swapped and a retry policy that handles transient errors without leaking infrastructure concerns into the application layer.

## Decision
Adopt an OpenAI-compatible API adapter (`OpenAIStructuredExtractionAdapter`) that implements `StructuredExtractionPort`, with a configurable base URL for local or hosted providers. Retries use exponential backoff with capped attempts in the OpenAI transport adapter (`adapters/output/llm/openai/transport.py`), while the structured extraction adapter translates transport failures into domain extraction errors.

## Consequences
We standardize on OpenAI-compatible chat completions and keep provider retry behavior close to third-party I/O in the OpenAI transport layer. Configuration must include base URL, API key, model, and retry settings.

## Alternatives
- Direct SDK usage in use cases
- Provider-specific adapters without a shared port
