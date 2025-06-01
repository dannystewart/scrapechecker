#!/usr/bin/env python3

"""Contest monitoring script using the generic SiteMonitor framework."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from polykit import PolyArgs, PolyEnv, PolyLog, PolyPath

from scrapechecker.scrapers.contest_scraper import ContestScraper
from scrapechecker.site_monitor import SiteMonitor

if TYPE_CHECKING:
    import argparse

logger = PolyLog.get_logger()
env = PolyEnv()
env.add_var("CONTEST_URL")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description="Monitor pet contest rankings and votes")
    parser.add_argument("url", nargs="?", default=env.contest_url, help="Contest URL to monitor")
    parser.add_argument(
        "--target",
        type=str,
        help="Name of specific contestant to highlight and focus monitoring on",
    )
    parser.add_argument("--test-alert", action="store_true", help="Send a test notification")
    parser.add_argument("--send", action="store_true", help="Send current rankings")
    parser.add_argument(
        "--replay", action="store_true", help="Replay last detected changes for testing"
    )
    parser.add_argument(
        "--data-file", help="File to store contest data (default: user data directory)"
    )
    parser.add_argument(
        "--status-file", help="File to store daily status (default: user data directory)"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for contest monitoring."""
    args = parse_args()

    # Initialize PolyPath for standardized file storage
    paths = PolyPath("scrapechecker")

    # Set default file paths using PolyPath if not provided
    data_file = args.data_file or str(paths.from_data("contest_data.json"))
    status_file = args.status_file or str(paths.from_data("contest_status.json"))

    # Create the contest scraper
    scraper = ContestScraper(url=args.url, target_item=args.target)

    # Create the site monitor
    monitor = SiteMonitor(
        url=args.url,
        site_scraper=scraper,
        data_file=data_file,
        status_file=status_file,
    )

    if args.test_alert:
        # Send test notification with sample contest data
        sample_data = [
            {
                "rank": 1,
                "name": "Roo",
                "votes": 150,
                "is_target": args.target and "roo" in args.target.lower(),
            },
            {
                "rank": 2,
                "name": "Johnny",
                "votes": 140,
                "is_target": False,
            },
        ]

        # Send test alert with formatted message instead of using the generic test method
        test_message = "<b>--- TEST CONTEST NOTIFICATION ---</b>\n\n"
        test_message += "<b>🆕 Current Rankings:</b>\n"
        for item in sample_data:
            formatted = scraper.format_item(item)
            test_message += f"• {formatted}\n"

        monitor.send_telegram_alert(test_message)
        logger.info("Test notification sent!")
        return

    if args.send:
        # Send current rankings without change tracking
        current_rankings = monitor.scraper.scrape_data()
        if current_rankings:
            message = monitor.formatter.format_full_rankings(current_rankings)
            monitor.send_telegram_alert(message)
            logger.info("Current rankings sent! (%s contestants)", len(current_rankings))
        else:
            logger.info("No rankings found.")
        return

    if args.replay:
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
