"""OpenAI adapter implementation."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from openai import APIError
from pydantic import BaseModel, ValidationError

from qa_chatbot.application.ports.output import LLMPort
from qa_chatbot.domain import DailyUpdate, LLMExtractionError, ProjectStatus, QAMetrics, TeamId, TimeWindow

from .client import build_client
from .prompts import (
    DAILY_UPDATE_PROMPT,
    PROJECT_STATUS_PROMPT,
    QA_METRICS_PROMPT,
    SYSTEM_PROMPT,
    TEAM_ID_PROMPT,
    TIME_WINDOW_PROMPT,
)
from .retry_logic import DEFAULT_BACKOFF_SECONDS, DEFAULT_MAX_RETRIES
from .schemas import (
    DailyUpdateSchema,
    ProjectStatusSchema,
    QAMetricsSchema,
    TeamIdSchema,
    TimeWindowSchema,
)

if TYPE_CHECKING:
    from datetime import date

    from openai import OpenAI


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
        client: OpenAI | None = None,
    ) -> None:
        """Initialize the adapter configuration."""
        self._settings = settings
        self._client = client or build_client(base_url=settings.base_url, api_key=settings.api_key)
        self._last_usage: TokenUsage | None = None

    @property
    def last_usage(self) -> TokenUsage | None:
        """Return token usage for the most recent call."""
        return self._last_usage

    def extract_team_id(self, conversation: str) -> TeamId:
        """Extract a team identifier from a conversation."""
        payload = self._extract_json(conversation, TEAM_ID_PROMPT)
        data = self._parse_schema(payload, TeamIdSchema)
        return TeamId.from_raw(data.team_id)

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""
        payload = self._extract_json(conversation, TIME_WINDOW_PROMPT)
        data = self._parse_schema(payload, TimeWindowSchema)
        if data.month.strip().lower() in {"current", "current_month"}:
            return TimeWindow.from_date(current_date)
        if data.month.strip().lower() in {"previous", "previous_month", "last"}:
            return TimeWindow.default_for(current_date, grace_period_days=31)
        try:
            year_str, month_str = data.month.split("-")
            return TimeWindow.from_year_month(int(year_str), int(month_str))
        except ValueError as err:
            message = "Time window must be in YYYY-MM format"
            raise LLMExtractionError(message) from err

    def extract_qa_metrics(self, conversation: str) -> QAMetrics:
        """Extract QA metrics from a conversation."""
        payload = self._extract_json(conversation, QA_METRICS_PROMPT)
        data = self._parse_schema(payload, QAMetricsSchema)
        return QAMetrics(
            tests_passed=data.tests_passed,
            tests_failed=data.tests_failed,
            test_coverage_percent=data.test_coverage_percent,
            bug_count=data.bug_count,
            critical_bugs=data.critical_bugs,
            deployment_ready=data.deployment_ready,
        )

    def extract_project_status(self, conversation: str) -> ProjectStatus:
        """Extract project status updates from a conversation."""
        payload = self._extract_json(conversation, PROJECT_STATUS_PROMPT)
        data = self._parse_schema(payload, ProjectStatusSchema)
        return ProjectStatus(
            sprint_progress_percent=data.sprint_progress_percent,
            blockers=tuple(data.blockers),
            milestones_completed=tuple(data.milestones_completed),
            risks=tuple(data.risks),
        )

    def extract_daily_update(self, conversation: str) -> DailyUpdate:
        """Extract a daily update from a conversation."""
        payload = self._extract_json(conversation, DAILY_UPDATE_PROMPT)
        data = self._parse_schema(payload, DailyUpdateSchema)
        return DailyUpdate(
            completed_tasks=tuple(data.completed_tasks),
            planned_tasks=tuple(data.planned_tasks),
            capacity_hours=data.capacity_hours,
            issues=tuple(data.issues),
        )

    def _extract_json(self, conversation: str, prompt: str) -> dict[str, Any]:
        """Call the OpenAI API and extract JSON content."""
        for attempt in range(self._settings.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._settings.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"{prompt}\n\nConversation:\n{conversation}"},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0,
                )
                self._last_usage = self._extract_usage(response)
                message = response.choices[0].message
                if message.content is None:
                    msg = "LLM response did not include content"
                    raise LLMExtractionError(msg)
                return self._parse_json(message.content)
            except APIError as err:
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

    @staticmethod
    def _parse_schema(payload: dict[str, Any], schema: type[BaseModel]) -> BaseModel:
        """Validate payload against a Pydantic schema."""
        try:
            return schema.model_validate(payload)
        except ValidationError as err:
            msg = "LLM response did not match expected schema"
            raise LLMExtractionError(msg) from err

    def _sleep_backoff(self, attempt: int) -> None:
        """Sleep with exponential backoff between retries."""
        delay = self._settings.backoff_seconds * (2**attempt)
        time.sleep(delay)

    @staticmethod
    def _extract_usage(response: Any) -> TokenUsage | None:
        """Extract token usage from the OpenAI response if available."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return None
        return TokenUsage(
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )
