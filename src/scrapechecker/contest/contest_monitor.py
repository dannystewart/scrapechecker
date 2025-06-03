#!/usr/bin/env python3

"""Contest monitoring script using the generic SiteMonitor framework."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from polykit import PolyArgs, PolyEnv, PolyLog, PolyPath

from scrapechecker.contest.contest_formatter import ContestFormatter
from scrapechecker.contest.contest_scraper import ContestScraper
from scrapechecker.site_monitor import SiteMonitor

if TYPE_CHECKING:
    import argparse

logger = PolyLog.get_logger()
env = PolyEnv()
env.add_var("CONTEST_URL")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description="Monitor Roo's pet contest rankings and votes", min_arg_width=24)
    parser.add_argument(
        "--current",
        action="store_true",
        help="Show current status with change detection but don't save data",
    )
    parser.add_argument(
        "--previous", action="store_true", help="replay last detected changes for testing"
    )
    parser.add_argument(
        "--data-dir", help="directory to store contest data (default: user data directory)"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for contest monitoring."""
    args = parse_args()

    # Initialize PolyPath for standardized file storage
    paths = PolyPath("scrapechecker")

    # Set default data directory using PolyPath if not provided
    if args.data_dir:
        data_file = str(Path(args.data_dir) / "contest_data.json")
        status_file = str(Path(args.data_dir) / "contest_status.json")
    else:
        data_file = str(paths.from_data("contest_data.json"))
        status_file = str(paths.from_data("contest_status.json"))

    # Set the URL
    url = env.contest_url

    # Create the contest scraper
    scraper = ContestScraper(url=url, target_item="roo")

    # Create the contest formatter
    formatter = ContestFormatter(scraper)

    # Create the site monitor
    monitor = SiteMonitor(
        url=url,
        site_scraper=scraper,
        formatter=formatter,
        data_file=data_file,
        status_file=status_file,
    )

    if args.current:
        # Check current status with change detection but don't save data
        monitor.check_current_status()
        return

    if args.previous:
        # Replay last detected changes for testing
        monitor.replay_last_changes()
        return

    # Run the monitoring
    try:
        monitor.monitor()
        logger.info("Contest monitoring completed successfully!")
    except Exception as e:
        logger.error("Error during contest monitoring: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
