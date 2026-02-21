"""Submit structured project data for persistence."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain import DomainError, Submission, SubmissionMetrics

if TYPE_CHECKING:
    from collections.abc import Callable

    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.application.ports.output import DashboardPort, MetricsPort, StoragePort

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubmitProjectDataUseCase:
    """Validate and persist a project submission."""

    storage_port: StoragePort
    dashboard_port: DashboardPort | None = None
    metrics_port: MetricsPort | None = None

    def execute(self, command: SubmissionCommand) -> Submission:
        """Persist a project submission, merging with existing data for the same project/month."""
        submit_extra = self._log_extra(
            correlation_id=command.correlation_id,
            project_id=str(command.project_id),
            time_window=str(command.time_window),
        )
        LOGGER.info(
            "Submitting project data",
            extra=submit_extra,
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
            self._generate_dashboards(submission, command.correlation_id)
        saved_extra = self._log_extra(
            correlation_id=command.correlation_id,
            submission_id=submission.id,
            project_id=str(submission.project_id),
            time_window=str(submission.month),
        )
        LOGGER.info(
            "Submission saved",
            extra=saved_extra,
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

    def _generate_dashboards(self, submission: Submission, correlation_id: str | None) -> None:
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
            except DomainError as err:
                dashboard_error_extra = self._log_extra(
                    correlation_id=correlation_id,
                    view=view,
                    project_id=str(submission.project_id),
                    time_window=str(submission.month),
                    error_type=type(err).__name__,
                )
                LOGGER.exception(
                    "Dashboard generation failed",
                    extra=dashboard_error_extra,
                )

    def _log_extra(self, *, correlation_id: str | None, **extra: object) -> dict[str, object]:
        """Build structured log context for this use case."""
        payload: dict[str, object] = {
            "component": self.__class__.__name__,
            **extra,
        }
        if correlation_id is not None:
            payload["correlation_id"] = correlation_id
        return payload
