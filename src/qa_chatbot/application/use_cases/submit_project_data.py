"""Submit structured project data for persistence."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from qa_chatbot.domain import Submission, SubmissionMetrics

if TYPE_CHECKING:
    from collections.abc import Callable

    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.application.ports.output import DashboardPort, MetricsPort, StoragePort


@dataclass(frozen=True)
class SubmitProjectDataUseCase:
    """Validate and persist a project submission."""

    storage_port: StoragePort
    dashboard_port: DashboardPort | None = None
    metrics_port: MetricsPort | None = None
    _logger: logging.Logger = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize logging for the use case."""
        object.__setattr__(self, "_logger", logging.getLogger(self.__class__.__name__))

    def execute(self, command: SubmissionCommand) -> Submission:
        """Persist a project submission, merging with existing data for the same project/month."""
        self._logger.info(
            "Submitting project data",
            extra={
                "project_id": str(command.project_id),
                "time_window": str(command.time_window),
            },
        )
        merged_metrics = self._merge_with_existing(command)
        submission = Submission.create(
            project_id=command.project_id,
            month=command.time_window,
            metrics=merged_metrics,
            raw_conversation=command.raw_conversation,
            created_at=command.created_at,
        )
        self.storage_port.save_submission(submission)
        if self.metrics_port is not None:
            self.metrics_port.record_submission(submission.project_id, submission.month)
        if self.dashboard_port is not None:
            self._generate_dashboards(submission)
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
    ) -> SubmissionMetrics:
        """Merge incoming data with any existing submission for the same project/month."""
        existing_submissions = self.storage_port.get_submissions_by_project(
            command.project_id,
            command.time_window,
        )
        if not existing_submissions:
            return command.metrics

        existing = max(existing_submissions, key=lambda s: s.created_at)
        return command.metrics.merge_with(existing.metrics)

    def _generate_dashboards(self, submission: Submission) -> None:
        """Generate dashboards without failing the submission flow on render errors."""
        if self.dashboard_port is None:
            return
        dashboard_port = self.dashboard_port

        recent_months = self.storage_port.get_recent_months(limit=6)
        projects = self.storage_port.get_all_projects()
        operations: tuple[tuple[str, Callable[[], object]], ...] = (
            (
                "overview",
                lambda: dashboard_port.generate_overview(submission.month),
            ),
            (
                "project_detail",
                lambda: dashboard_port.generate_project_detail(submission.project_id, recent_months),
            ),
            (
                "trends",
                lambda: dashboard_port.generate_trends(projects, recent_months),
            ),
        )
        for view, operation in operations:
            try:
                operation()
            except Exception:
                self._logger.exception(
                    "Dashboard generation failed",
                    extra={
                        "view": view,
                        "project_id": str(submission.project_id),
                        "time_window": str(submission.month),
                    },
                )
