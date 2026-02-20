"""Generate dashboard artifacts from existing database data."""

from __future__ import annotations

import argparse
import logging
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

from qa_chatbot.adapters.input import EnvSettingsAdapter
from qa_chatbot.adapters.output import (
    CompositeDashboardAdapter,
    ConfluenceDashboardAdapter,
    HtmlDashboardAdapter,
    MockJiraAdapter,
    SQLiteAdapter,
)
from qa_chatbot.application import GenerateMonthlyReportUseCase, GetDashboardDataUseCase
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.config import LoggingSettings, configure_logging
from qa_chatbot.domain import build_default_stream_project_registry

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import AppSettings
    from qa_chatbot.domain import ProjectId, TimeWindow

LOGGER = logging.getLogger(__name__)

# ruff: noqa: T201


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate dashboard files from existing database submissions.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Database connection URL (default: value from env settings).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for generated dashboard files (default: value from env settings).",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Number of recent months to include in dashboards (default: 6).",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: value from env settings).",
    )
    return parser.parse_args()


def generate_dashboards(
    database_url: str,
    output_dir: Path,
    months_limit: int,
    log_level: str,
    settings: AppSettings,
) -> None:
    """Generate all dashboard views from existing database data."""
    configure_logging(LoggingSettings(level=log_level))

    print("=" * 80)
    print("DASHBOARD GENERATION SCRIPT")
    print("=" * 80)
    print(f"\nDatabase: {database_url}")
    print(f"Output directory: {output_dir}")
    print(f"Jira base URL: {settings.jira_base_url}")
    print(f"Months to include: {months_limit}")
    print("=" * 80 + "\n")

    storage = _build_storage(
        database_url=database_url,
        timeout_seconds=settings.database_timeout_seconds,
    )
    dashboard = _build_dashboard_adapter(storage=storage, output_dir=output_dir, settings=settings)
    recent_months, projects = _load_generation_inputs(storage=storage, months_limit=months_limit)
    if recent_months is None or projects is None:
        return
    print(f"📊 Found {len(projects)} projects and {len(recent_months)} recent months\n")
    generated_files, overview_path = _generate_views(
        dashboard=dashboard,
        projects=projects,
        recent_months=recent_months,
    )
    _print_summary(output_dir=output_dir, generated_files=generated_files, overview_path=overview_path)


def _build_storage(database_url: str, timeout_seconds: float) -> SQLiteAdapter:
    LOGGER.info("Initializing storage adapter")
    storage = SQLiteAdapter(
        database_url=database_url,
        echo=False,
        timeout_seconds=timeout_seconds,
    )
    storage.initialize_schema()
    return storage


def _build_dashboard_adapter(
    storage: SQLiteAdapter,
    output_dir: Path,
    settings: AppSettings,
) -> CompositeDashboardAdapter:
    LOGGER.info("Initializing dashboard adapter")
    registry = build_default_stream_project_registry()
    edge_case_policy = EdgeCasePolicy()
    jira_adapter = MockJiraAdapter(
        registry=registry,
        jira_base_url=settings.jira_base_url,
        jira_username=settings.jira_username,
        jira_api_token=settings.jira_api_token,
    )
    report_use_case = GenerateMonthlyReportUseCase(
        storage_port=storage,
        jira_port=jira_adapter,
        registry=registry,
        timezone="UTC",
        edge_case_policy=edge_case_policy,
    )
    dashboard_data_use_case = GetDashboardDataUseCase(storage_port=storage)

    html_dashboard = HtmlDashboardAdapter(
        get_dashboard_data_use_case=dashboard_data_use_case,
        generate_monthly_report_use_case=report_use_case,
        output_dir=output_dir,
        tailwind_script_src=settings.dashboard_tailwind_script_src,
        plotly_script_src=settings.dashboard_plotly_script_src,
    )
    confluence_dashboard = ConfluenceDashboardAdapter(
        get_dashboard_data_use_case=dashboard_data_use_case,
        generate_monthly_report_use_case=report_use_case,
        output_dir=output_dir,
    )
    return CompositeDashboardAdapter(adapters=(html_dashboard, confluence_dashboard))


def _load_generation_inputs(
    storage: SQLiteAdapter,
    months_limit: int,
) -> tuple[list[TimeWindow], list[ProjectId]] | tuple[None, None]:
    LOGGER.info("Fetching recent months from database")
    recent_months = storage.get_recent_months(limit=months_limit)
    if not recent_months:
        print("❌ No data found in database. Nothing to generate.")
        print("\nTip: Run 'python scripts/seed_database.py' to populate the database.\n")
        return None, None

    LOGGER.info("Fetching all projects from database")
    projects = storage.get_all_projects()
    if not projects:
        print("❌ No projects found in database. Nothing to generate.")
        return None, None
    return recent_months, projects


def _generate_views(
    dashboard: CompositeDashboardAdapter,
    projects: list[ProjectId],
    recent_months: list[TimeWindow],
) -> tuple[list[Path], Path]:
    generated_files: list[Path] = []
    latest_month = recent_months[0]
    print(f"Generating overview dashboard for {latest_month.to_iso_month()}...")
    overview_path = dashboard.generate_overview(latest_month)
    generated_files.append(overview_path)
    print(f"  ✅ {overview_path}")

    print(f"\nGenerating project detail dashboards for {len(projects)} projects...")
    for project in projects:
        project_path = dashboard.generate_project_detail(project, recent_months)
        generated_files.append(project_path)
        print(f"  ✅ {project_path}")

    print("\nGenerating trends dashboard...")
    trends_path = dashboard.generate_trends(projects, recent_months)
    generated_files.append(trends_path)
    print(f"  ✅ {trends_path}")
    return generated_files, overview_path


def _print_summary(output_dir: Path, generated_files: list[Path], overview_path: Path) -> None:
    print("\n" + "=" * 80)
    print(f"✅ SUCCESS: Generated {len(generated_files)} dashboard files")
    print("=" * 80)
    print(f"\nOutput directory: {output_dir}")
    print("\nNext steps:")
    print("  1. Serve the dashboard: python scripts/serve_dashboard.py")
    print(f"  2. Open in browser: http://127.0.0.1:8000/{overview_path.name}")
    print("  3. Confluence-ready files are generated as *.confluence.html in the same directory")
    print()


def main() -> None:
    """Entry point for the dashboard generation script."""
    settings = EnvSettingsAdapter().load()
    args = parse_args()
    try:
        generate_dashboards(
            database_url=args.database_url or settings.database_url,
            output_dir=args.output_dir or Path(settings.dashboard_output_dir),
            months_limit=args.months,
            log_level=args.log_level or settings.log_level,
            settings=settings,
        )
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
