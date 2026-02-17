"""Domain layer for XM QA chatbot."""

from .entities import BusinessStream, JiraPriorityFilterGroup, JiraProjectFilters, Project, ReportingPeriod, Submission
from .exceptions import (
    DomainError,
    InvalidConfigurationError,
    InvalidProjectIdError,
    InvalidStreamIdError,
    InvalidSubmissionTeamError,
    InvalidTimeWindowError,
    MissingSubmissionDataError,
    StorageOperationError,
)
from .registries import StreamProjectRegistry, build_default_stream_project_registry
from .value_objects import (
    BucketCount,
    DefectLeakage,
    ExtractionConfidence,
    PortfolioAggregates,
    ProjectId,
    QualityMetrics,
    StreamId,
    SubmissionMetrics,
    TestCoverageMetrics,
    TimeWindow,
)

__all__ = [
    "BucketCount",
    "BusinessStream",
    "DefectLeakage",
    "DomainError",
    "ExtractionConfidence",
    "InvalidConfigurationError",
    "InvalidProjectIdError",
    "InvalidStreamIdError",
    "InvalidSubmissionTeamError",
    "InvalidTimeWindowError",
    "JiraPriorityFilterGroup",
    "JiraProjectFilters",
    "MissingSubmissionDataError",
    "PortfolioAggregates",
    "Project",
    "ProjectId",
    "QualityMetrics",
    "ReportingPeriod",
    "StorageOperationError",
    "StreamId",
    "StreamProjectRegistry",
    "Submission",
    "SubmissionMetrics",
    "TestCoverageMetrics",
    "TimeWindow",
    "build_default_stream_project_registry",
]
