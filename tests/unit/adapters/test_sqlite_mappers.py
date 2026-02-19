"""Unit tests for SQLite mapper utilities."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from qa_chatbot.adapters.output.persistence.sqlite.mappers import model_to_submission, time_window_from_iso
from qa_chatbot.adapters.output.persistence.sqlite.models import SubmissionModel
from qa_chatbot.domain import ProjectId, TestCoverageMetrics, TimeWindow


def test_model_to_submission_parses_created_at_string() -> None:
    """Parse ISO datetime strings when mapping model rows back to domain objects."""
    model = SubmissionModel(
        id="12345678-1234-5678-1234-567812345678",
        project_id="project-a",
        month="2026-01",
        created_at="2026-01-10T10:00:00+00:00",
        test_coverage={"manual_total": 4, "automated_total": 2},
        overall_test_cases=None,
        supported_releases_count=1,
        raw_conversation="raw",
    )

    submission = model_to_submission(model)

    assert submission.project_id == ProjectId("project-a")
    assert submission.month == TimeWindow.from_year_month(2026, 1)
    assert submission.created_at == datetime(2026, 1, 10, 10, 0, tzinfo=UTC)
    assert submission.test_coverage == TestCoverageMetrics(manual_total=4, automated_total=2)


def test_time_window_from_iso_raises_for_invalid_shape() -> None:
    """Raise when month strings do not match YYYY-MM shape."""
    with pytest.raises(ValueError, match="not enough values"):
        time_window_from_iso("2026")
