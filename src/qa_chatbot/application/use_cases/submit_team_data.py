"""Submit structured team data for persistence."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from qa_chatbot.domain import Submission, TestCoverageMetrics

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.application.ports.output import DashboardPort, MetricsPort, StoragePort


@dataclass(frozen=True)
class SubmitTeamDataUseCase:
    """Validate and persist a team submission."""

    storage_port: StoragePort
    dashboard_port: DashboardPort | None = None
    metrics_port: MetricsPort | None = None
    _logger: logging.Logger = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize logging for the use case."""
        object.__setattr__(self, "_logger", logging.getLogger(self.__class__.__name__))

    def execute(self, command: SubmissionCommand) -> Submission:
        """Persist a team submission, merging with existing data for the same project/month."""
        self._logger.info(
            "Submitting project data",
            extra={
                "project_id": str(command.project_id),
                "time_window": str(command.time_window),
            },
        )
        merged_coverage, merged_overall, merged_supported_releases = self._merge_with_existing(command)
        submission = Submission.create(
            project_id=command.project_id,
            month=command.time_window,
            test_coverage=merged_coverage,
            overall_test_cases=merged_overall,
            supported_releases_count=merged_supported_releases,
            raw_conversation=command.raw_conversation,
            created_at=command.created_at,
        )
        self.storage_port.save_submission(submission)
        if self.metrics_port is not None:
            self.metrics_port.record_submission(submission.project_id, submission.month)
        if self.dashboard_port is not None:
            recent_months = self.storage_port.get_recent_months(limit=6)
            projects = self.storage_port.get_all_projects()
            self.dashboard_port.generate_overview(submission.month)
            self.dashboard_port.generate_team_detail(submission.project_id, recent_months)
            self.dashboard_port.generate_trends(projects, recent_months)
        self._logger.info(
            "Submission saved",
            extra={
                "submission_id": submission.id,
                "project_id": str(submission.project_id),
                "time_window": str(submission.month),
            },
        )
        return submission

    def _merge_with_existing(
        self,
        command: SubmissionCommand,
    ) -> tuple[TestCoverageMetrics | None, int | None, int | None]:
        """Merge incoming data with any existing submission for the same project/month."""
        existing_submissions = self.storage_port.get_submissions_by_project(
            command.project_id,
            command.time_window,
        )
        if not existing_submissions:
            return command.test_coverage, command.overall_test_cases, command.supported_releases_count

        existing = max(existing_submissions, key=lambda s: s.created_at)

        merged_coverage = command.test_coverage
        merged_coverage = merged_coverage.merge_with(existing.test_coverage) if merged_coverage is not None else existing.test_coverage

        merged_overall = command.overall_test_cases if command.overall_test_cases is not None else existing.overall_test_cases
        merged_supported_releases = (
            command.supported_releases_count if command.supported_releases_count is not None else existing.supported_releases_count
        )
        return merged_coverage, merged_overall, merged_supported_releases
