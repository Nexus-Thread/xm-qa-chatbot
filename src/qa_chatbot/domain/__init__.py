"""Domain layer for XM QA chatbot."""

from .entities import BusinessStream, Project, ReportingPeriod, Submission
from .exceptions import (
    DomainError,
    InvalidConfigurationError,
    InvalidProjectIdError,
    InvalidStreamIdError,
    InvalidSubmissionTeamError,
    InvalidTimeWindowError,
    MissingSubmissionDataError,
)
from .registries import (
    ReportingRegistry,
    StreamRegistry,
    build_default_registry,
    build_default_reporting_registry,
)
from .services import ValidationService
from .value_objects import (
    BucketCount,
    CapaStatus,
    DefectLeakage,
    ExtractionConfidence,
    PortfolioAggregates,
    ProjectId,
    QualityMetrics,
    RegressionTimeBlock,
    RegressionTimeEntry,
    StreamId,
    TestCoverageMetrics,
    TimeWindow,
)

__all__ = [
    "BucketCount",
    "BusinessStream",
    "CapaStatus",
    "DefectLeakage",
    "DomainError",
    "ExtractionConfidence",
    "InvalidConfigurationError",
    "InvalidProjectIdError",
    "InvalidStreamIdError",
    "InvalidSubmissionTeamError",
    "InvalidTimeWindowError",
    "MissingSubmissionDataError",
    "PortfolioAggregates",
    "Project",
    "ProjectId",
    "QualityMetrics",
    "RegressionTimeBlock",
    "RegressionTimeEntry",
    "ReportingPeriod",
    "ReportingRegistry",
    "StreamId",
    "StreamRegistry",
    "Submission",
    "TestCoverageMetrics",
    "TimeWindow",
    "ValidationService",
    "build_default_registry",
    "build_default_reporting_registry",
]
