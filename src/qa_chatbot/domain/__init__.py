"""Domain layer for XM QA chatbot."""

from .entities import BusinessStream, Project, ReportingPeriod, Submission, TeamData
from .exceptions import (
    AmbiguousExtractionError,
    DashboardRenderError,
    DomainError,
    InvalidConfigurationError,
    InvalidProjectIdError,
    InvalidSubmissionTeamError,
    InvalidTimeWindowError,
    LLMExtractionError,
    MissingSubmissionDataError,
)
from .registries import StreamRegistry, build_default_registry
from .services import ValidationService
from .value_objects import (
    BucketCount,
    CapaStatus,
    DefectLeakage,
    PortfolioAggregates,
    PriorityBucket,
    PriorityMapping,
    ProjectId,
    QualityMetrics,
    RegressionTimeBlock,
    RegressionTimeEntry,
    TestCoverageMetrics,
    TimeWindow,
)

__all__ = [
    "AmbiguousExtractionError",
    "BucketCount",
    "BusinessStream",
    "CapaStatus",
    "DashboardRenderError",
    "DefectLeakage",
    "DomainError",
    "InvalidConfigurationError",
    "InvalidProjectIdError",
    "InvalidSubmissionTeamError",
    "InvalidTimeWindowError",
    "LLMExtractionError",
    "MissingSubmissionDataError",
    "PortfolioAggregates",
    "PriorityBucket",
    "PriorityMapping",
    "Project",
    "ProjectId",
    "QualityMetrics",
    "RegressionTimeBlock",
    "RegressionTimeEntry",
    "ReportingPeriod",
    "StreamRegistry",
    "Submission",
    "TeamData",
    "TestCoverageMetrics",
    "TimeWindow",
    "ValidationService",
    "build_default_registry",
]
