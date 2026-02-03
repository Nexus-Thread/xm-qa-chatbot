"""OpenAI client construction utilities."""

from __future__ import annotations

from openai import OpenAI


def build_client(base_url: str, api_key: str) -> OpenAI:
    """Create an OpenAI-compatible client instance."""
    return OpenAI(base_url=base_url, api_key=api_key)
