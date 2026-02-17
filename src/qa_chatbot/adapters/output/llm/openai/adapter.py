"""OpenAI adapter implementation."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from openai import APIError
from pydantic import BaseModel, ValidationError

from qa_chatbot.application.dtos import ExtractionResult
from qa_chatbot.application.ports.output import LLMPort
from qa_chatbot.domain import ExtractionConfidence, ProjectId, SubmissionMetrics, TestCoverageMetrics, TimeWindow
from qa_chatbot.domain.exceptions import InvalidConfigurationError

from .client import build_client
from .exceptions import AmbiguousExtractionError, LLMExtractionError
from .prompts import SYSTEM_PROMPT, TEST_COVERAGE_PROMPT, TIME_WINDOW_PROMPT, build_project_id_prompt
from .retry_logic import DEFAULT_BACKOFF_SECONDS, DEFAULT_MAX_RETRIES
from .schemas import ProjectIdSchema, TestCoverageSchema, TimeWindowSchema

SchemaT = TypeVar("SchemaT", bound=BaseModel)

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.domain.registries import StreamProjectRegistry


@dataclass(frozen=True)
class TokenUsage:
    """Token usage details for a single extraction."""

    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


@dataclass(frozen=True)
class OpenAISettings:
    """Configuration settings for the OpenAI adapter."""

    base_url: str
    api_key: str
    model: str
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS


class OpenAIAdapter(LLMPort):
    """Extracts structured data using an OpenAI-compatible API."""

    def __init__(
        self,
        settings: OpenAISettings,
        client: Any | None = None,  # noqa: ANN401
    ) -> None:
        """Initialize the adapter configuration."""
        self._settings = settings
        self._client = client or build_client(base_url=settings.base_url, api_key=settings.api_key)
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

        try:
            confidence = ExtractionConfidence.from_raw(data.confidence)
        except InvalidConfigurationError:
            confidence = ExtractionConfidence.low()

        return ProjectId.from_raw(data.project_id), confidence

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""
        payload = self._extract_json(conversation, TIME_WINDOW_PROMPT)
        data = self._parse_schema(payload, TimeWindowSchema)
        self._raise_if_blank(data.month, "time window")
        return self._resolve_time_window(data.month, current_date)

    def extract_test_coverage(self, conversation: str) -> TestCoverageMetrics:
        """Extract test coverage metrics from a conversation."""
        payload = self._extract_json(conversation, TEST_COVERAGE_PROMPT)
        data = self._parse_schema(payload, TestCoverageSchema)
        return TestCoverageMetrics(
            manual_total=data.manual_total,
            automated_total=data.automated_total,
            manual_created_in_reporting_month=data.manual_created_in_reporting_month,
            manual_updated_in_reporting_month=data.manual_updated_in_reporting_month,
            automated_created_in_reporting_month=data.automated_created_in_reporting_month,
            automated_updated_in_reporting_month=data.automated_updated_in_reporting_month,
            percentage_automation=None,
        )

    def extract_supported_releases_count(self, conversation: str) -> int | None:
        """Extract supported releases count from a conversation."""
        payload = self._extract_json(conversation, TEST_COVERAGE_PROMPT)
        data = self._parse_schema(payload, TestCoverageSchema)
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
        team_payload = self._extract_json(conversation, project_prompt, history)
        time_payload = self._extract_json(conversation, TIME_WINDOW_PROMPT, history)
        coverage_payload = self._extract_json(conversation, TEST_COVERAGE_PROMPT, history)

        team_data = self._parse_schema(team_payload, ProjectIdSchema)
        time_data = self._parse_schema(time_payload, TimeWindowSchema)
        coverage_data = self._parse_schema(coverage_payload, TestCoverageSchema)
        self._raise_if_blank(team_data.project_id, "project identifier")
        self._raise_if_blank(time_data.month, "time window")

        project_id = ProjectId.from_raw(team_data.project_id)
        time_window = self._resolve_time_window(time_data.month, current_date)

        return ExtractionResult(
            project_id=project_id,
            time_window=time_window,
            metrics=SubmissionMetrics(
                test_coverage=TestCoverageMetrics(
                    manual_total=coverage_data.manual_total,
                    automated_total=coverage_data.automated_total,
                    manual_created_in_reporting_month=coverage_data.manual_created_in_reporting_month,
                    manual_updated_in_reporting_month=coverage_data.manual_updated_in_reporting_month,
                    automated_created_in_reporting_month=coverage_data.automated_created_in_reporting_month,
                    automated_updated_in_reporting_month=coverage_data.automated_updated_in_reporting_month,
                    percentage_automation=None,
                ),
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
        client: Any = self._client
        for attempt in range(self._settings.max_retries):
            try:
                started_at = time.perf_counter()
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *self._normalize_history(history),
                    {"role": "user", "content": f"{prompt}\n\nConversation:\n{conversation}"},
                ]
                response = client.chat.completions.create(
                    model=self._settings.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0,
                )
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                self._last_usage = self._extract_usage(response)
                self._logger.info(
                    "LLM extraction completed",
                    extra={
                        "model": self._settings.model,
                        "prompt_name": prompt.split("\n", maxsplit=1)[0],
                        "elapsed_ms": round(elapsed_ms, 2),
                        "prompt_tokens": self._last_usage.prompt_tokens if self._last_usage else None,
                        "completion_tokens": self._last_usage.completion_tokens if self._last_usage else None,
                        "total_tokens": self._last_usage.total_tokens if self._last_usage else None,
                    },
                )
                message = response.choices[0].message
                if message.content is None:
                    msg = "LLM response did not include content"
                    raise LLMExtractionError(msg)
                return self._parse_json(message.content)
            except APIError as err:
                self._logger.warning(
                    "LLM extraction failed",
                    extra={
                        "model": self._settings.model,
                        "attempt": attempt + 1,
                    },
                )
                if attempt >= self._settings.max_retries - 1:
                    msg = "LLM request failed after retries"
                    raise LLMExtractionError(msg) from err
                self._sleep_backoff(attempt)

        msg = "LLM request failed after retries"
        raise LLMExtractionError(msg)

    @staticmethod
    def _parse_json(payload: str) -> dict[str, Any]:
        """Parse JSON payload into a dictionary."""
        try:
            return json.loads(payload)
        except json.JSONDecodeError as err:
            msg = "LLM response contained invalid JSON"
            raise LLMExtractionError(msg) from err

    def _parse_schema(self, payload: dict[str, Any], schema: type[SchemaT]) -> SchemaT:
        """Validate payload against a Pydantic schema."""
        try:
            return schema.model_validate(payload)
        except ValidationError as err:
            self._logger.exception(
                "Schema validation failed for %s. Payload: %s",
                schema.__name__,
                payload,
            )
            msg = "LLM response did not match expected schema"
            raise LLMExtractionError(msg) from err

    def _resolve_time_window(self, value: str, current_date: date) -> TimeWindow:
        """Resolve time window values into TimeWindow objects."""
        cleaned = value.strip().lower()
        if cleaned in {"current", "current_month"}:
            return TimeWindow.from_date(current_date)
        if cleaned in {"previous", "previous_month", "last"}:
            return TimeWindow.default_for(current_date, grace_period_days=31)
        try:
            year_str, month_str = value.split("-")
            return TimeWindow.from_year_month(int(year_str), int(month_str))
        except ValueError as err:
            message = "Time window must be in YYYY-MM format"
            raise LLMExtractionError(message) from err

    def _sleep_backoff(self, attempt: int) -> None:
        """Sleep with exponential backoff between retries."""
        delay = self._settings.backoff_seconds * (2**attempt)
        time.sleep(delay)

    @staticmethod
    def _raise_if_blank(value: str, label: str) -> None:
        """Raise when a required string value is blank."""
        if not value.strip():
            raise AmbiguousExtractionError(label, is_missing=True)

    @staticmethod
    def _raise_if_missing_int(value: int | None, label: str) -> None:
        """Raise when a required integer is missing."""
        if value is None:
            raise AmbiguousExtractionError(label, is_missing=True)

    @staticmethod
    def _raise_if_ambiguous(label: str) -> None:
        """Raise when LLM response lacks required detail."""
        raise AmbiguousExtractionError(label, is_missing=False)

    @staticmethod
    def _normalize_history(history: list[dict[str, str]] | None) -> list[dict[str, str]]:
        """Normalize history into chat message dicts."""
        if not history:
            return []
        return [{"role": entry.get("role", "user"), "content": entry.get("content", "")} for entry in history if entry.get("content")]

    @staticmethod
    def _extract_usage(response: Any) -> TokenUsage | None:  # noqa: ANN401
        """Extract token usage from the OpenAI response if available."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return None
        return TokenUsage(
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )
