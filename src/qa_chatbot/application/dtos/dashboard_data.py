"""Dashboard data transfer objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain import ProjectId, TimeWindow


@dataclass(frozen=True)
class TeamOverviewCard:
    """Summary for a project on the overview dashboard."""

    team_id: ProjectId
    month: TimeWindow
    qa_metrics: dict[str, float | int | bool | None]
    project_status: dict[str, float | list[str] | None]
    daily_update: dict[str, float | list[str] | None]


@dataclass(frozen=True)
class OverviewDashboardData:
    """Data needed for the overview dashboard."""

    month: TimeWindow
    teams: list[TeamOverviewCard]


@dataclass(frozen=True)
class TeamMonthlySnapshot:
    """Per-month snapshot for a project."""

    month: TimeWindow
    qa_metrics: dict[str, float | int | bool | None]
    project_status: dict[str, float | list[str] | None]
    daily_update: dict[str, float | list[str] | None]


@dataclass(frozen=True)
class TeamDetailDashboardData:
    """Data needed for a project detail dashboard."""

    team_id: ProjectId
    snapshots: list[TeamMonthlySnapshot]


@dataclass(frozen=True)
class TrendSeries:
    """Trend series for a single metric across months."""

    label: str
    values: list[float | int | None]


@dataclass(frozen=True)
class TrendsDashboardData:
    """Data needed for the trends dashboard."""

    teams: list[ProjectId]
    months: list[TimeWindow]
    qa_metric_series: dict[str, list[TrendSeries]]
    project_metric_series: dict[str, list[TrendSeries]]
