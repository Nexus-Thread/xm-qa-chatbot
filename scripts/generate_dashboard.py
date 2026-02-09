"""Generate dashboard HTML files from existing database data."""

from __future__ import annotations

import argparse
import logging
import traceback
from pathlib import Path

from qa_chatbot.adapters.output import HtmlDashboardAdapter, SQLiteAdapter
from qa_chatbot.config import LoggingSettings, configure_logging

# ruff: noqa: T201


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate dashboard HTML files from existing database submissions.")
    parser.add_argument(
        "--database-url",
        default="sqlite:///./qa_chatbot.db",
        help="Database connection URL (default: sqlite:///./qa_chatbot.db).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./dashboard_html"),
        help="Output directory for generated HTML files (default: ./dashboard_html).",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Number of recent months to include in dashboards (default: 6).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )
    return parser.parse_args()


def generate_dashboards(
    database_url: str,
    output_dir: Path,
    months_limit: int,
    log_level: str,
) -> None:
    """Generate all dashboard views from existing database data."""
    configure_logging(LoggingSettings(level=log_level))
    logger = logging.getLogger(__name__)

    print("=" * 80)
    print("DASHBOARD GENERATION SCRIPT")
    print("=" * 80)
    print(f"\nDatabase: {database_url}")
    print(f"Output directory: {output_dir}")
    print(f"Months to include: {months_limit}")
    print("=" * 80 + "\n")

    # Initialize adapters
    logger.info("Initializing storage adapter")
    storage = SQLiteAdapter(database_url=database_url, echo=False)
    storage.initialize_schema()

    logger.info("Initializing dashboard adapter")
    dashboard = HtmlDashboardAdapter(storage_port=storage, output_dir=output_dir)

    # Fetch data from storage
    logger.info("Fetching recent months from database")
    recent_months = storage.get_recent_months(limit=months_limit)
    if not recent_months:
        print("❌ No data found in database. Nothing to generate.")
        print("\nTip: Run 'python scripts/seed_database.py' to populate the database.\n")
        return

    logger.info("Fetching all projects from database")
    projects = storage.get_all_projects()
    if not projects:
        print("❌ No projects found in database. Nothing to generate.")
        return

    print(f"📊 Found {len(projects)} projects and {len(recent_months)} recent months\n")

    # Generate dashboards
    generated_files: list[Path] = []

    # 1. Overview dashboard (latest month)
    latest_month = recent_months[0]
    print(f"Generating overview dashboard for {latest_month.to_iso_month()}...")
    overview_path = dashboard.generate_overview(latest_month)
    generated_files.append(overview_path)
    print(f"  ✅ {overview_path}")

    # 2. Team detail dashboards (one per project)
    print(f"\nGenerating team detail dashboards for {len(projects)} projects...")
    for project in projects:
        team_path = dashboard.generate_team_detail(project, recent_months)
        generated_files.append(team_path)
        print(f"  ✅ {team_path}")

    # 3. Trends dashboard (all projects)
    print("\nGenerating trends dashboard...")
    trends_path = dashboard.generate_trends(projects, recent_months)
    generated_files.append(trends_path)
    print(f"  ✅ {trends_path}")

    # Summary
    print("\n" + "=" * 80)
    print(f"✅ SUCCESS: Generated {len(generated_files)} dashboard files")
    print("=" * 80)
    print(f"\nOutput directory: {output_dir}")
    print("\nNext steps:")
    print("  1. Serve the dashboard: python scripts/serve_dashboard.py")
    print(f"  2. Open in browser: http://127.0.0.1:8000/{overview_path.name}")
    print()


def main() -> None:
    """Entry point for the dashboard generation script."""
    args = parse_args()
    try:
        generate_dashboards(
            database_url=args.database_url,
            output_dir=args.output_dir,
            months_limit=args.months,
            log_level=args.log_level,
        )
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
