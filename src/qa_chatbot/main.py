"""Application entry point for the Gradio chatbot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from qa_chatbot.adapters.input import GradioAdapter, GradioSettings
from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationManager
from qa_chatbot.adapters.output import HtmlDashboardAdapter, OpenAIAdapter, SQLiteAdapter
from qa_chatbot.adapters.output.llm.openai import OpenAISettings
from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitTeamDataUseCase


@dataclass(frozen=True)
class AppSettings:
    """Configuration for the chatbot application."""

    openai_base_url: str
    openai_api_key: str
    openai_model: str
    database_url: str
    database_echo: bool
    dashboard_output_dir: str
    server_port: int
    share: bool


def main() -> None:
    """Run the chatbot application."""
    settings = load_settings()
    storage = SQLiteAdapter(database_url=settings.database_url, echo=settings.database_echo)
    storage.initialize_schema()

    dashboard_output_dir = Path(settings.dashboard_output_dir)
    dashboard_adapter = HtmlDashboardAdapter(storage_port=storage, output_dir=dashboard_output_dir)

    llm_adapter = OpenAIAdapter(
        settings=OpenAISettings(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    )
    extractor = ExtractStructuredDataUseCase(llm_port=llm_adapter)
    submitter = SubmitTeamDataUseCase(storage_port=storage, dashboard_port=dashboard_adapter)
    manager = ConversationManager(extractor=extractor, submitter=submitter)

    gradio_settings = GradioSettings(server_port=settings.server_port, share=settings.share)
    GradioAdapter(manager=manager, settings=gradio_settings).launch()


def load_settings() -> AppSettings:
    """Load application settings from environment variables."""
    return AppSettings(
        openai_base_url=os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", "ollama"),
        openai_model=os.environ.get("OPENAI_MODEL", "llama2"),
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./qa_chatbot.db"),
        database_echo=_read_bool("DATABASE_ECHO", default=False),
        dashboard_output_dir=os.environ.get("DASHBOARD_OUTPUT_DIR", "./dashboard_html"),
        server_port=int(os.environ.get("GRADIO_SERVER_PORT", "7860")),
        share=_read_bool("GRADIO_SHARE", default=False),
    )


def _read_bool(name: str, default: bool) -> bool:
    """Parse boolean environment variables."""
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y"}


if __name__ == "__main__":
    main()
