"""Playwright e2e test for the chatbot positive flow."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from socket import AF_INET, SOCK_STREAM, socket
from time import sleep
from typing import TYPE_CHECKING
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from qa_chatbot.adapters.input.gradio import GradioAdapter, GradioSettings
from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationManager
from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitProjectDataUseCase
from qa_chatbot.application.dtos import CoverageExtractionResult, ExtractionResult, HistoryExtractionRequest
from qa_chatbot.domain import (
    ExtractionConfidence,
    InvalidMetricInputError,
    InvalidProjectIdError,
    InvalidTimeWindowError,
    ProjectId,
    Submission,
    SubmissionMetrics,
    TestCoverageMetrics,
    TimeWindow,
    build_default_stream_project_registry,
)

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

PROJECT_INPUT = "affiliate"
MONTH_INPUT = "2026-01"
COVERAGE_INPUT = "manual 10 automated 5 supported releases 2"
CONFIRM_INPUT = "yes"


@dataclass(frozen=True)
class _ChatbotServer:
    """Container for running chatbot server details."""

    base_url: str
    storage: _FakeStorage


if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import date

    from playwright.sync_api import Page

    from qa_chatbot.domain.registries import StreamProjectRegistry


@dataclass
class _FakeLLM:
    """Deterministic extraction adapter for e2e testing."""

    def extract_project_id(
        self,
        conversation: str,
        registry: StreamProjectRegistry,
    ) -> tuple[ProjectId, ExtractionConfidence]:
        normalized = conversation.strip().lower()
        if not normalized:
            msg = "Missing project identifier"
            raise InvalidProjectIdError(msg)

        project_id = ProjectId.from_raw(normalized)
        if registry.find_project(project_id.value) is None:
            msg = f"Unknown project identifier: {project_id.value}"
            raise InvalidProjectIdError(msg)

        return project_id, ExtractionConfidence.high()

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        _ = current_date
        normalized = conversation.strip()
        match = re.fullmatch(r"(\d{4})-(\d{2})", normalized)
        if match is None:
            msg = "Month must be in YYYY-MM format"
            raise InvalidTimeWindowError(msg)

        year = int(match.group(1))
        month = int(match.group(2))
        return TimeWindow.from_year_month(year, month)

    def extract_coverage(self, conversation: str) -> CoverageExtractionResult:
        manual_total, automated_total, supported_releases_count = self._parse_coverage_message(conversation)
        total = manual_total + automated_total
        percentage_automation = round((automated_total / total) * 100, 2) if total > 0 else 0.0

        return CoverageExtractionResult(
            metrics=TestCoverageMetrics(
                manual_total=manual_total,
                automated_total=automated_total,
                manual_created_in_reporting_month=0,
                manual_updated_in_reporting_month=0,
                automated_created_in_reporting_month=0,
                automated_updated_in_reporting_month=0,
                percentage_automation=percentage_automation,
            ),
            supported_releases_count=supported_releases_count,
        )

    def extract_with_history(
        self,
        request: HistoryExtractionRequest,
        current_date: date,
        registry: StreamProjectRegistry,
    ) -> ExtractionResult:
        project_id = request.known_project_id
        if project_id is None:
            project_id, _ = self.extract_project_id(request.conversation, registry)

        time_window = request.known_time_window
        if time_window is None:
            time_window = self.extract_time_window(request.conversation, current_date)

        test_coverage = request.known_test_coverage
        supported_releases_count = request.known_supported_releases_count
        if test_coverage is None or supported_releases_count is None:
            extracted_coverage = self.extract_coverage(request.conversation)
            if test_coverage is None:
                test_coverage = extracted_coverage.metrics
            if supported_releases_count is None:
                supported_releases_count = extracted_coverage.supported_releases_count

        return ExtractionResult(
            project_id=project_id,
            time_window=time_window,
            metrics=SubmissionMetrics(
                test_coverage=test_coverage,
                overall_test_cases=None,
                supported_releases_count=supported_releases_count,
            ),
        )

    @staticmethod
    def _parse_coverage_message(conversation: str) -> tuple[int, int, int]:
        normalized = conversation.strip().lower()
        match = re.fullmatch(
            r"manual\s+(\d+)\s+automated\s+(\d+)\s+supported\s+releases\s+(\d+)",
            normalized,
        )
        if match is None:
            msg = "Coverage must be: manual <n> automated <n> supported releases <n>"
            raise InvalidMetricInputError(msg)

        manual_total = int(match.group(1))
        automated_total = int(match.group(2))
        supported_releases_count = int(match.group(3))
        return manual_total, automated_total, supported_releases_count


@dataclass
class _FakeStorage:
    """In-memory storage for deterministic e2e assertions."""

    submissions: list[Submission] = field(default_factory=list)

    def save_submission(self, submission: Submission) -> None:
        """Persist submission in memory."""
        self.submissions.append(submission)

    def get_submissions_by_project(self, project_id: ProjectId, month: TimeWindow) -> list[Submission]:
        """Return submissions filtered by project and month."""
        return [submission for submission in self.submissions if submission.project_id == project_id and submission.month == month]

    def get_all_projects(self) -> list[ProjectId]:
        """Return distinct project identifiers."""
        return list({submission.project_id for submission in self.submissions})

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        """Return submissions filtered by month."""
        return [submission for submission in self.submissions if submission.month == month]

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        """Return recent months from stored submissions."""
        seen: set[TimeWindow] = set()
        months: list[TimeWindow] = []
        submissions = sorted(self.submissions, key=lambda submission: submission.created_at, reverse=True)
        for submission in submissions:
            month = submission.month
            if month in seen:
                continue
            months.append(month)
            seen.add(month)
            if len(months) == limit:
                break
        return months

    def get_overall_test_cases_by_month(self, month: TimeWindow) -> int | None:
        """Return no aggregate overall test cases for e2e fake."""
        _ = month
        return None


@pytest.fixture(scope="module")
def chatbot_server() -> Iterator[_ChatbotServer]:
    """Start a deterministic local Gradio server for browser e2e."""
    port = _find_free_port()
    settings = GradioSettings(server_port=port, share=False, rate_limit_requests=100)
    extractor = ExtractStructuredDataUseCase(llm_port=_FakeLLM())
    storage = _FakeStorage()
    submitter = SubmitProjectDataUseCase(storage_port=storage)
    manager = ConversationManager(
        extractor=extractor,
        submitter=submitter,
        registry=build_default_stream_project_registry(),
    )
    adapter = GradioAdapter(manager=manager, settings=settings)
    app = adapter._build_ui()  # noqa: SLF001
    app.launch(
        server_name="127.0.0.1",
        server_port=port,
        share=False,
        show_error=True,
        prevent_thread_lock=True,
    )

    base_url = f"http://127.0.0.1:{port}"
    _wait_for_server(base_url)

    yield _ChatbotServer(base_url=base_url, storage=storage)

    app.close()


def test_chatbot_positive_flow_playwright(page: Page, chatbot_server: _ChatbotServer) -> None:
    """Run a browser-level positive flow and verify save confirmation."""
    page.goto(chatbot_server.base_url, wait_until="domcontentloaded")

    page.get_by_text("Which stream/project are you reporting for?").first.wait_for()
    input_box = page.get_by_placeholder("Type your update here...")

    input_box.fill(PROJECT_INPUT)
    input_box.press("Enter")
    page.get_by_text("Which reporting month should be used?").wait_for()

    input_box.fill(MONTH_INPUT)
    input_box.press("Enter")
    page.get_by_text("Share test coverage details").wait_for()

    input_box.fill(COVERAGE_INPUT)
    input_box.press("Enter")
    page.get_by_text("Reply with 'yes' to save").wait_for()

    input_box.fill(CONFIRM_INPUT)
    input_box.press("Enter")
    page.get_by_text("Thanks! Your update has been saved.").wait_for()
    _assert_saved_submission(chatbot_server.storage)


def _assert_saved_submission(storage: _FakeStorage) -> None:
    assert len(storage.submissions) == 1


def _find_free_port() -> int:
    with socket(AF_INET, SOCK_STREAM) as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        server_socket.listen(1)
        return int(server_socket.getsockname()[1])


def _wait_for_server(base_url: str, *, retries: int = 100, sleep_seconds: float = 0.1) -> None:
    for _ in range(retries):
        try:
            with urlopen(base_url, timeout=0.2):  # noqa: S310
                return
        except URLError:
            sleep(sleep_seconds)

    msg = f"Gradio test server did not start in time at {base_url}"
    raise RuntimeError(msg)
