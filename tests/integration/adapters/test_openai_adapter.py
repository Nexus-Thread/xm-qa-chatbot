"""Integration tests for OpenAI transport adapter with Ollama."""

from __future__ import annotations

import json
import os

import pytest

from qa_chatbot.adapters.output.llm.openai import OpenAIClientSettings, build_client, extract_message_content


@pytest.mark.skipif(
    os.getenv("OLLAMA_BASE_URL") is None,
    reason="OLLAMA_BASE_URL not configured",
)
def test_openai_adapter_with_ollama_returns_hello_world_json() -> None:
    """Send a hello-world prompt via OpenAI transport client."""
    settings = OpenAIClientSettings(
        base_url=os.environ["OLLAMA_BASE_URL"],
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
    )
    client = build_client(settings)
    model = os.getenv("OLLAMA_MODEL", "llama2")

    response = client.create_json_completion(
        model=model,
        messages=[
            {
                "role": "system",
                "content": 'Reply with a JSON object containing key "message" and value "hello world".',
            },
            {
                "role": "user",
                "content": "Say hello world",
            },
        ],
    )
    content = extract_message_content(response)
    payload = json.loads(content)

    assert isinstance(payload, dict)
    assert "message" in payload
    assert str(payload["message"]).strip().lower() == "hello world"
