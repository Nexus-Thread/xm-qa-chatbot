"""Factory for the default stream-project registry."""

from __future__ import annotations

from qa_chatbot.domain.entities import BusinessStream, Project
from qa_chatbot.domain.value_objects.stream_id import StreamId

from .config_loader import load_project_filters, project_filters_for
from .registry import StreamProjectRegistry


def build_default_stream_project_registry() -> StreamProjectRegistry:
    """Return the hard-coded stream-project registry from requirements."""
    filters_by_project = load_project_filters()

    streams = (
        BusinessStream(id=StreamId("affiliates"), name="Affiliates", order=1),
        BusinessStream(id=StreamId("backbone_bridge"), name="Backbone Systems / Bridge", order=2),
        BusinessStream(id=StreamId("backbone_platform"), name="Backbone Systems / Platform Systems", order=3),
        BusinessStream(id=StreamId("backbone_trading"), name="Backbone Systems / Trading Platform", order=4),
        BusinessStream(id=StreamId("client_engagement"), name="Client Engagement", order=5),
        BusinessStream(id=StreamId("client_journey"), name="Client Journey", order=6),
        BusinessStream(id=StreamId("funding"), name="Funding", order=7),
        BusinessStream(id=StreamId("internal_systems"), name="Internal Systems", order=8),
        BusinessStream(id=StreamId("mobile"), name="Mobile", order=9),
        BusinessStream(id=StreamId("www_cfa"), name="WWW / Client Face Application (CFA)", order=10),
    )

    projects = (
        Project(
            id="affiliate",
            name="Affiliate",
            business_stream_id=StreamId("affiliates"),
        ),
        Project(
            id="bridge",
            name="Bridge",
            business_stream_id=StreamId("backbone_bridge"),
        ),
        Project(
            id="jthales",
            name="JThales",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="jmanager_server_portal",
            name="jManager Server and Portal",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="symbols_management_service",
            name="Symbols Management Service",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="local_depositors_service",
            name="Local Depositors Service",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="fees_management_service",
            name="Fees Management Service",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="admin_tools_service",
            name="Admin Tools Service",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="funding_service",
            name="Funding Service (Not Live)",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="jtools",
            name="JTools",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="data_access_layer",
            name="Data Access Layer (DAL)",
            business_stream_id=StreamId("backbone_platform"),
        ),
        Project(
            id="metaproxy",
            name="MetaProxy",
            business_stream_id=StreamId("backbone_trading"),
        ),
        Project(
            id="plugins",
            name="Plugins",
            business_stream_id=StreamId("backbone_trading"),
        ),
        Project(
            id="tsda",
            name="TSDA",
            business_stream_id=StreamId("backbone_trading"),
        ),
        Project(
            id="horn",
            name="HORN",
            business_stream_id=StreamId("backbone_trading"),
        ),
        Project(
            id="social_trading_copy",
            name="Social Trading - Copy Trading",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="social_trading_competitions",
            name="Social Trading - Competitions",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="promotions_tool",
            name="Promotions Tool",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="client_loyalty_loyalty",
            name="Client Loyalty - Loyalty",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="client_loyalty_bonus",
            name="Client Loyalty - Bonus",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="market_intelligence",
            name="Market Intelligence",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="artificial_intelligence",
            name="Artificial Intelligence (AI)",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="client_communication",
            name="Client Communication",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="education",
            name="Education",
            business_stream_id=StreamId("client_engagement"),
        ),
        Project(
            id="client_support",
            name="Client Support",
            business_stream_id=StreamId("client_journey"),
        ),
        Project(
            id="client_authentication",
            name="Client Authentication",
            business_stream_id=StreamId("client_journey"),
        ),
        Project(
            id="client_trading",
            name="Client Trading",
            business_stream_id=StreamId("client_journey"),
        ),
        Project(
            id="onboarding_account_mgmt",
            name="Onboarding & Account Management",
            business_stream_id=StreamId("client_journey"),
        ),
        Project(
            id="realtime_communications",
            name="Realtime Communications",
            business_stream_id=StreamId("client_journey"),
        ),
        Project(
            id="payments",
            name="Payments",
            business_stream_id=StreamId("funding"),
        ),
        Project(
            id="withdrawals",
            name="Withdrawals",
            business_stream_id=StreamId("funding"),
        ),
        Project(
            id="kyc",
            name="KYC",
            business_stream_id=StreamId("internal_systems"),
        ),
        Project(
            id="scc",
            name="SCC",
            business_stream_id=StreamId("internal_systems"),
        ),
        Project(
            id="crm",
            name="CRM",
            business_stream_id=StreamId("internal_systems"),
        ),
        Project(
            id="digital_marketing",
            name="Digital Marketing",
            business_stream_id=StreamId("internal_systems"),
        ),
        Project(
            id="mobile_trading_point",
            name="Mobile - XM Trading Point",
            business_stream_id=StreamId("mobile"),
        ),
        Project(
            id="angular_core_web",
            name="Angular Core Web",
            business_stream_id=StreamId("www_cfa"),
        ),
        Project(
            id="angular_www",
            name="Angular WWW",
            business_stream_id=StreamId("www_cfa"),
        ),
    )

    projects_with_filters = tuple(
        Project(
            id=project.id,
            name=project.name,
            business_stream_id=project.business_stream_id,
            jira_filters=project_filters_for(project.id, filters_by_project),
        )
        for project in projects
    )

    return StreamProjectRegistry(streams=streams, projects=projects_with_filters)
