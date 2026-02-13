"""Application entry point for the Gradio chatbot."""

from __future__ import annotations

from pathlib import Path

from qa_chatbot.adapters.input import EnvSettingsAdapter, GradioAdapter, GradioSettings
from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationManager
from qa_chatbot.adapters.output import (
    CompositeDashboardAdapter,
    ConfluenceDashboardAdapter,
    HtmlDashboardAdapter,
    InMemoryMetricsAdapter,
    OpenAIAdapter,
    SQLiteAdapter,
)
from qa_chatbot.adapters.output.llm.openai import OpenAISettings
from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitTeamDataUseCase
from qa_chatbot.config import LoggingSettings, configure_logging


def main() -> None:
    """Run the chatbot application."""
    settings = EnvSettingsAdapter().load()
    configure_logging(
        LoggingSettings(
            level=settings.log_level,
        )
    )
    storage = SQLiteAdapter(database_url=settings.database_url, echo=settings.database_echo)
    storage.initialize_schema()

    dashboard_output_dir = Path(settings.dashboard_output_dir)
    html_dashboard_adapter = HtmlDashboardAdapter(
        storage_port=storage,
        output_dir=dashboard_output_dir,
        jira_base_url=settings.jira_base_url,
        jira_username=settings.jira_username,
        jira_api_token=settings.jira_api_token,
    )
    confluence_dashboard_adapter = ConfluenceDashboardAdapter(
        storage_port=storage,
        output_dir=dashboard_output_dir,
        jira_base_url=settings.jira_base_url,
        jira_username=settings.jira_username,
        jira_api_token=settings.jira_api_token,
    )
    dashboard_adapter = CompositeDashboardAdapter(
        adapters=(html_dashboard_adapter, confluence_dashboard_adapter),
    )

    llm_adapter = OpenAIAdapter(
        settings=OpenAISettings(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    )
    metrics_adapter = InMemoryMetricsAdapter()
    extractor = ExtractStructuredDataUseCase(llm_port=llm_adapter, metrics_port=metrics_adapter)
    submitter = SubmitTeamDataUseCase(
        storage_port=storage,
        dashboard_port=dashboard_adapter,
        metrics_port=metrics_adapter,
    )
    manager = ConversationManager(extractor=extractor, submitter=submitter)

    gradio_settings = GradioSettings(
        server_port=settings.server_port,
        share=settings.share,
        input_max_chars=settings.input_max_chars,
        rate_limit_requests=settings.rate_limit_requests,
        rate_limit_window_seconds=settings.rate_limit_window_seconds,
    )
    GradioAdapter(manager=manager, settings=gradio_settings).launch()


if __name__ == "__main__":
    main()
