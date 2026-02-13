"""Business stream and project registry."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.entities import BusinessStream, Project
from qa_chatbot.domain.exceptions import InvalidConfigurationError


@dataclass(frozen=True)
class StreamRegistry:
    """Registry of business streams and projects."""

    streams: tuple[BusinessStream, ...]
    projects: tuple[Project, ...]

    def __post_init__(self) -> None:
        """Validate registry consistency."""
        stream_ids = {stream.id for stream in self.streams}
        if len(stream_ids) != len(self.streams):
            msg = "Business stream IDs must be unique"
            raise InvalidConfigurationError(msg)
        project_ids = {project.id for project in self.projects}
        if len(project_ids) != len(self.projects):
            msg = "Project IDs must be unique"
            raise InvalidConfigurationError(msg)
        for project in self.projects:
            if project.business_stream_id not in stream_ids:
                msg = f"Project {project.id} references unknown stream {project.business_stream_id}"
                raise InvalidConfigurationError(msg)

    def active_projects(self) -> tuple[Project, ...]:
        """Return active projects."""
        return self.projects

    def projects_for_stream(self, stream_id: str) -> tuple[Project, ...]:
        """Return projects for a given stream."""
        return tuple(project for project in self.projects if project.business_stream_id == stream_id)

    def stream_name(self, stream_id: str) -> str:
        """Return the stream name for an id."""
        for stream in self.streams:
            if stream.id == stream_id:
                return stream.name
        msg = f"Unknown stream id {stream_id}"
        raise InvalidConfigurationError(msg)

    def find_project(self, project_id: str) -> Project | None:
        """Find a project by id or name."""
        normalized = project_id.strip().lower()
        for project in self.projects:
            if project.id.lower() == normalized or project.name.lower() == normalized:
                return project
        return None


def build_default_registry() -> StreamRegistry:
    """Return the hard-coded stream registry from requirements."""
    streams = (
        BusinessStream(id="affiliates", name="Affiliates", order=1),
        BusinessStream(id="backbone_bridge", name="Backbone Systems / Bridge", order=2),
        BusinessStream(id="backbone_platform", name="Backbone Systems / Platform Systems", order=3),
        BusinessStream(id="backbone_trading", name="Backbone Systems / Trading Platform", order=4),
        BusinessStream(id="client_engagement", name="Client Engagement", order=5),
        BusinessStream(id="client_journey", name="Client Journey", order=6),
        BusinessStream(id="funding", name="Funding", order=7),
        BusinessStream(id="internal_systems", name="Internal Systems", order=8),
        BusinessStream(id="mobile", name="Mobile", order=9),
        BusinessStream(id="www_cfa", name="WWW / Client Face Application (CFA)", order=10),
    )

    projects = (
        Project(id="affiliate", name="Affiliate", business_stream_id="affiliates"),
        Project(id="bridge", name="Bridge", business_stream_id="backbone_bridge"),
        Project(id="jthales", name="JThales", business_stream_id="backbone_platform"),
        Project(
            id="jmanager_server_portal",
            name="jManager Server and Portal",
            business_stream_id="backbone_platform",
        ),
        Project(
            id="symbols_management_service",
            name="Symbols Management Service",
            business_stream_id="backbone_platform",
        ),
        Project(
            id="local_depositors_service",
            name="Local Depositors Service",
            business_stream_id="backbone_platform",
        ),
        Project(
            id="fees_management_service",
            name="Fees Management Service",
            business_stream_id="backbone_platform",
        ),
        Project(
            id="admin_tools_service",
            name="Admin Tools Service",
            business_stream_id="backbone_platform",
        ),
        Project(
            id="funding_service",
            name="Funding Service (Not Live)",
            business_stream_id="backbone_platform",
        ),
        Project(id="jtools", name="JTools", business_stream_id="backbone_platform"),
        Project(
            id="data_access_layer",
            name="Data Access Layer (DAL)",
            business_stream_id="backbone_platform",
        ),
        Project(id="metaproxy", name="MetaProxy", business_stream_id="backbone_trading"),
        Project(id="plugins", name="Plugins", business_stream_id="backbone_trading"),
        Project(id="tsda", name="TSDA", business_stream_id="backbone_trading"),
        Project(id="horn", name="HORN", business_stream_id="backbone_trading"),
        Project(
            id="social_trading_copy",
            name="Social Trading - Copy Trading",
            business_stream_id="client_engagement",
        ),
        Project(
            id="social_trading_competitions",
            name="Social Trading - Competitions",
            business_stream_id="client_engagement",
        ),
        Project(
            id="promotions_tool",
            name="Promotions Tool",
            business_stream_id="client_engagement",
        ),
        Project(
            id="client_loyalty_loyalty",
            name="Client Loyalty - Loyalty",
            business_stream_id="client_engagement",
        ),
        Project(
            id="client_loyalty_bonus",
            name="Client Loyalty - Bonus",
            business_stream_id="client_engagement",
        ),
        Project(
            id="market_intelligence",
            name="Market Intelligence",
            business_stream_id="client_engagement",
        ),
        Project(
            id="artificial_intelligence",
            name="Artificial Intelligence (AI)",
            business_stream_id="client_engagement",
        ),
        Project(
            id="client_communication",
            name="Client Communication",
            business_stream_id="client_engagement",
        ),
        Project(id="education", name="Education", business_stream_id="client_engagement"),
        Project(id="client_support", name="Client Support", business_stream_id="client_journey"),
        Project(
            id="client_authentication",
            name="Client Authentication",
            business_stream_id="client_journey",
        ),
        Project(id="client_trading", name="Client Trading", business_stream_id="client_journey"),
        Project(
            id="onboarding_account_mgmt",
            name="Onboarding & Account Management",
            business_stream_id="client_journey",
        ),
        Project(
            id="realtime_communications",
            name="Realtime Communications",
            business_stream_id="client_journey",
        ),
        Project(id="payments", name="Payments", business_stream_id="funding"),
        Project(id="withdrawals", name="Withdrawals", business_stream_id="funding"),
        Project(id="kyc", name="KYC", business_stream_id="internal_systems"),
        Project(id="scc", name="SCC", business_stream_id="internal_systems"),
        Project(id="crm", name="CRM", business_stream_id="internal_systems"),
        Project(
            id="digital_marketing",
            name="Digital Marketing",
            business_stream_id="internal_systems",
        ),
        Project(
            id="mobile_trading_point",
            name="Mobile - XM Trading Point",
            business_stream_id="mobile",
        ),
        Project(id="angular_core_web", name="Angular Core Web", business_stream_id="www_cfa"),
        Project(id="angular_www", name="Angular WWW", business_stream_id="www_cfa"),
    )

    return StreamRegistry(streams=streams, projects=projects)
