"""LLM structured extraction adapter implementation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar

from openai import APIError
from pydantic import BaseModel

from qa_chatbot.adapters.output.llm.openai import (
    OpenAIClientProtocol,
    OpenAIResponseError,
    build_client,
    extract_message_content,
    extract_usage,
)
from qa_chatbot.application.dtos import ExtractionResult
from qa_chatbot.application.ports.output import StructuredExtractionPort
from qa_chatbot.domain import ExtractionConfidence, ProjectId, SubmissionMetrics, TestCoverageMetrics, TimeWindow
from qa_chatbot.domain.exceptions import InvalidConfigurationError

from .exceptions import AmbiguousExtractionError, LLMExtractionError
from .history import normalize_history
from .json_response import parse_json_payload, parse_schema_payload
from .mappers import to_test_coverage_metrics
from .parsers import resolve_time_window
from .prompts import SYSTEM_PROMPT, TEST_COVERAGE_PROMPT, TIME_WINDOW_PROMPT, build_project_id_prompt
from .schemas import ProjectIdSchema, TestCoverageSchema, TimeWindowSchema
from .settings import TokenUsage

SchemaT = TypeVar("SchemaT", bound=BaseModel)

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.domain.registries import StreamProjectRegistry

    from .settings import OpenAISettings


class OpenAIStructuredExtractionAdapter(StructuredExtractionPort):
    """Extracts structured data using an OpenAI-compatible API."""

    def __init__(
        self,
        settings: OpenAISettings,
        client: OpenAIClientProtocol | None = None,
    ) -> None:
        """Initialize the adapter configuration."""
        self._settings = settings
        if client is not None:
            self._client = client
        else:
            self._client = build_client(settings)
        self._last_usage: TokenUsage | None = None
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def last_usage(self) -> TokenUsage | None:
        """Return token usage for the most recent call."""
        return self._last_usage

    def extract_project_id(
        self,
        conversation: str,
        registry: StreamProjectRegistry,
    ) -> tuple[ProjectId, ExtractionConfidence]:
        """Extract a project identifier from a conversation."""
        prompt = build_project_id_prompt(registry)
        payload = self._extract_json(conversation, prompt)
        data = self._parse_schema(payload, ProjectIdSchema)
        self._raise_if_blank(data.project_id, "project identifier")
        matched_project = registry.find_project(data.project_id)
        if matched_project is None:
            self._raise_if_ambiguous("project identifier")

        try:
            confidence = ExtractionConfidence.from_raw(data.confidence)
        except InvalidConfigurationError:
            confidence = ExtractionConfidence.low()

        return ProjectId.from_raw(matched_project.id), confidence

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""
        payload = self._extract_json(conversation, TIME_WINDOW_PROMPT)
        data = self._parse_schema(payload, TimeWindowSchema)
        self._raise_if_blank(data.month, "time window")
        return resolve_time_window(data.month, current_date)

    def extract_test_coverage(self, conversation: str) -> TestCoverageMetrics:
        """Extract test coverage metrics from a conversation."""
        data = self._extract_test_coverage_data(conversation)
        return to_test_coverage_metrics(data)

    def extract_supported_releases_count(self, conversation: str) -> int | None:
        """Extract supported releases count from a conversation."""
        data = self._extract_test_coverage_data(conversation)
        return data.supported_releases_count

    def extract_with_history(
        self,
        conversation: str,
        history: list[dict[str, str]] | None,
        current_date: date,
        registry: StreamProjectRegistry,
    ) -> ExtractionResult:
        """Extract structured data using conversation history."""
        project_prompt = build_project_id_prompt(registry)
        project_payload = self._extract_json(conversation, project_prompt, history)
        time_payload = self._extract_json(conversation, TIME_WINDOW_PROMPT, history)
        coverage_payload = self._extract_json(conversation, TEST_COVERAGE_PROMPT, history)

        project_data = self._parse_schema(project_payload, ProjectIdSchema)
        time_data = self._parse_schema(time_payload, TimeWindowSchema)
        coverage_data = self._parse_schema(coverage_payload, TestCoverageSchema)
        self._raise_if_blank(project_data.project_id, "project identifier")
        self._raise_if_blank(time_data.month, "time window")
        matched_project = registry.find_project(project_data.project_id)
        if matched_project is None:
            self._raise_if_ambiguous("project identifier")

        project_id = ProjectId.from_raw(matched_project.id)
        time_window = resolve_time_window(time_data.month, current_date)

        return ExtractionResult(
            project_id=project_id,
            time_window=time_window,
            metrics=SubmissionMetrics(
                test_coverage=to_test_coverage_metrics(coverage_data),
                overall_test_cases=None,
                supported_releases_count=coverage_data.supported_releases_count,
            ),
        )

    def _extract_json(
        self,
        conversation: str,
        prompt: str,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Call the OpenAI API and extract JSON content."""
        client = self._client
        normalized_history = normalize_history(history)
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *normalized_history,
                {"role": "user", "content": f"{prompt}\n\nConversation:\n{conversation}"},
            ]
            response = client.create_json_completion(
                model=self._settings.model,
                messages=messages,
            )
            usage = extract_usage(response)
            self._last_usage = None
            if usage is not None:
                self._last_usage = TokenUsage(
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                )
            self._logger.info(
                "LLM extraction completed",
                extra={
                    "model": self._settings.model,
                    "prompt_name": prompt.split("\n", maxsplit=1)[0],
                    "prompt_tokens": self._last_usage.prompt_tokens if self._last_usage else None,
                    "completion_tokens": self._last_usage.completion_tokens if self._last_usage else None,
                    "total_tokens": self._last_usage.total_tokens if self._last_usage else None,
                },
            )
            content = extract_message_content(response)
            return parse_json_payload(content)
        except OpenAIResponseError as err:
            msg = str(err)
            raise LLMExtractionError(msg) from err
        except APIError as err:
            self._logger.exception(
                "LLM extraction failed",
                extra={
                    "model": self._settings.model,
                },
            )
            msg = "LLM request failed after retries"
            raise LLMExtractionError(msg) from err

    def _parse_schema(self, payload: dict[str, Any], schema: type[SchemaT]) -> SchemaT:
        """Validate payload against a Pydantic schema."""
        return parse_schema_payload(payload, schema, self._logger)

    def _extract_test_coverage_data(
        self,
        conversation: str,
        history: list[dict[str, str]] | None = None,
    ) -> TestCoverageSchema:
        """Extract and validate coverage payload for reuse by coverage methods."""
        payload = self._extract_json(conversation, TEST_COVERAGE_PROMPT, history)
        return self._parse_schema(payload, TestCoverageSchema)

    @staticmethod
    def _raise_if_blank(value: str, label: str) -> None:
        """Raise when a required string value is blank."""
        if not value.strip():
            raise AmbiguousExtractionError(label, is_missing=True)

    @staticmethod
    def _raise_if_ambiguous(label: str) -> NoReturn:
        """Raise when LLM response lacks required detail."""
        raise AmbiguousExtractionError(label, is_missing=False)
