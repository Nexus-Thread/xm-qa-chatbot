"""Factory for the default stream-project registry."""

from __future__ import annotations

from qa_chatbot.domain.entities import BusinessStream, JiraPriorityFilterGroup, JiraProjectFilters, Project
from qa_chatbot.domain.value_objects.stream_id import StreamId

from .registry import StreamProjectRegistry


def build_default_stream_project_registry() -> StreamProjectRegistry:
    """Return the hard-coded stream-project registry from requirements."""
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
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = AFFILIATE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = AFFILIATE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = AFFILIATE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = AFFILIATE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="bridge",
            name="Bridge",
            business_stream_id=StreamId("backbone_bridge"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = BRIDGE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = BRIDGE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = BRIDGE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = BRIDGE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="jthales",
            name="JThales",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = JTHALES AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = JTHALES AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = JTHALES AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = JTHALES AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="jmanager_server_portal",
            name="jManager Server and Portal",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = JMGR AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = JMGR AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = JMGR AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = JMGR AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="symbols_management_service",
            name="Symbols Management Service",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = SYM AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = SYM AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = SYM AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = SYM AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="local_depositors_service",
            name="Local Depositors Service",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = LDS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = LDS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = LDS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = LDS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="fees_management_service",
            name="Fees Management Service",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = FEES AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = FEES AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = FEES AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = FEES AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="admin_tools_service",
            name="Admin Tools Service",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = ADMIN AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ADMIN AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = ADMIN AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ADMIN AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="funding_service",
            name="Funding Service (Not Live)",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = FUNDING_SERVICE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = FUNDING_SERVICE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = FUNDING_SERVICE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = FUNDING_SERVICE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="jtools",
            name="JTools",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = JTOOLS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = JTOOLS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = JTOOLS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = JTOOLS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="data_access_layer",
            name="Data Access Layer (DAL)",
            business_stream_id=StreamId("backbone_platform"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = DAL AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = DAL AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = DAL AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = DAL AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="metaproxy",
            name="MetaProxy",
            business_stream_id=StreamId("backbone_trading"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = META AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = META AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = META AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = META AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="plugins",
            name="Plugins",
            business_stream_id=StreamId("backbone_trading"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = PLUG AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = PLUG AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = PLUG AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = PLUG AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="tsda",
            name="TSDA",
            business_stream_id=StreamId("backbone_trading"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = TSDA AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = TSDA AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = TSDA AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = TSDA AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="horn",
            name="HORN",
            business_stream_id=StreamId("backbone_trading"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = HORN AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = HORN AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = HORN AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = HORN AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="social_trading_copy",
            name="Social Trading - Copy Trading",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = SOCIAL_TRADING_COPY AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = SOCIAL_TRADING_COPY AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = SOCIAL_TRADING_COPY AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = SOCIAL_TRADING_COPY AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="social_trading_competitions",
            name="Social Trading - Competitions",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = SOCIAL_TRADING_COMPETITIONS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = SOCIAL_TRADING_COMPETITIONS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = SOCIAL_TRADING_COMPETITIONS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = SOCIAL_TRADING_COMPETITIONS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="promotions_tool",
            name="Promotions Tool",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = PROMOTIONS_TOOL AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = PROMOTIONS_TOOL AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = PROMOTIONS_TOOL AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = PROMOTIONS_TOOL AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="client_loyalty_loyalty",
            name="Client Loyalty - Loyalty",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_LOYALTY_LOYALTY AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_LOYALTY_LOYALTY AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_LOYALTY_LOYALTY AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_LOYALTY_LOYALTY AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="client_loyalty_bonus",
            name="Client Loyalty - Bonus",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_LOYALTY_BONUS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_LOYALTY_BONUS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_LOYALTY_BONUS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_LOYALTY_BONUS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="market_intelligence",
            name="Market Intelligence",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = MARKET_INTELLIGENCE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = MARKET_INTELLIGENCE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = MARKET_INTELLIGENCE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = MARKET_INTELLIGENCE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="artificial_intelligence",
            name="Artificial Intelligence (AI)",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = ARTIFICIAL_INTELLIGENCE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ARTIFICIAL_INTELLIGENCE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = ARTIFICIAL_INTELLIGENCE AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ARTIFICIAL_INTELLIGENCE AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="client_communication",
            name="Client Communication",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_COMMUNICATION AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_COMMUNICATION AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_COMMUNICATION AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_COMMUNICATION AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="education",
            name="Education",
            business_stream_id=StreamId("client_engagement"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = EDUCATION AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = EDUCATION AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = EDUCATION AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = EDUCATION AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="client_support",
            name="Client Support",
            business_stream_id=StreamId("client_journey"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_SUPPORT AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_SUPPORT AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_SUPPORT AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_SUPPORT AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="client_authentication",
            name="Client Authentication",
            business_stream_id=StreamId("client_journey"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_AUTHENTICATION AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_AUTHENTICATION AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = CLIENT_AUTHENTICATION AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLIENT_AUTHENTICATION AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="client_trading",
            name="Client Trading",
            business_stream_id=StreamId("client_journey"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = CLTR AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLTR AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = CLTR AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CLTR AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="onboarding_account_mgmt",
            name="Onboarding & Account Management",
            business_stream_id=StreamId("client_journey"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = ONBOARDING_ACCOUNT_MGMT AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ONBOARDING_ACCOUNT_MGMT AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = ONBOARDING_ACCOUNT_MGMT AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ONBOARDING_ACCOUNT_MGMT AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="realtime_communications",
            name="Realtime Communications",
            business_stream_id=StreamId("client_journey"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = REALTIME_COMMUNICATIONS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = REALTIME_COMMUNICATIONS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = REALTIME_COMMUNICATIONS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = REALTIME_COMMUNICATIONS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="payments",
            name="Payments",
            business_stream_id=StreamId("funding"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = PAY AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = PAY AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = PAY AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = PAY AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="withdrawals",
            name="Withdrawals",
            business_stream_id=StreamId("funding"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = WITHDRAWALS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = WITHDRAWALS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = WITHDRAWALS AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = WITHDRAWALS AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="kyc",
            name="KYC",
            business_stream_id=StreamId("internal_systems"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = KYC AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = KYC AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = KYC AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = KYC AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="scc",
            name="SCC",
            business_stream_id=StreamId("internal_systems"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = SCC AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = SCC AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = SCC AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = SCC AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="crm",
            name="CRM",
            business_stream_id=StreamId("internal_systems"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = CRM AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CRM AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = CRM AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = CRM AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="digital_marketing",
            name="Digital Marketing",
            business_stream_id=StreamId("internal_systems"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = DIGITAL_MARKETING AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = DIGITAL_MARKETING AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = DIGITAL_MARKETING AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = DIGITAL_MARKETING AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="mobile_trading_point",
            name="Mobile - XM Trading Point",
            business_stream_id=StreamId("mobile"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = MOBILE_TRADING_POINT AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = MOBILE_TRADING_POINT AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = MOBILE_TRADING_POINT AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = MOBILE_TRADING_POINT AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="angular_core_web",
            name="Angular Core Web",
            business_stream_id=StreamId("www_cfa"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = ANGULAR_CORE_WEB AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ANGULAR_CORE_WEB AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = ANGULAR_CORE_WEB AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ANGULAR_CORE_WEB AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
        Project(
            id="angular_www",
            name="Angular WWW",
            business_stream_id=StreamId("www_cfa"),
            jira_filters=JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2='project = ANGULAR_WWW AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ANGULAR_WWW AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2='project = ANGULAR_WWW AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                    p3_p4='project = ANGULAR_WWW AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                ),
            ),
        ),
    )

    return StreamProjectRegistry(streams=streams, projects=projects)
