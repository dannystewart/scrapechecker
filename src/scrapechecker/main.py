"""Generic main entry point for the monitoring framework."""

from __future__ import annotations

from typing import TYPE_CHECKING

from polykit import PolyArgs

from scrapechecker.scrapers.simple_scraper import ProductScraper, SimpleScraper
from scrapechecker.site_monitor import SiteMonitor

if TYPE_CHECKING:
    import argparse


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description="Monitor websites for changes")
    parser.add_argument("url", help="URL to monitor")
    parser.add_argument(
        "--scraper-type",
        choices=["simple", "product"],
        default="simple",
        help="Type of scraper to use",
    )
    parser.add_argument(
        "--css-selector", default="body", help="CSS selector for simple scraper (default: body)"
    )
    parser.add_argument(
        "--attribute",
        default="text",
        help="Attribute to extract for simple scraper (default: text)",
    )
    parser.add_argument(
        "--data-file", default="monitoring_data.json", help="File to store monitoring data"
    )
    parser.add_argument("--test", action="store_true", help="Send a test notification")
    return parser.parse_args()


def main():
    """Monitor a website using the generic framework.

    Raises:
        ValueError: If an unknown scraper type is specified.
    """
    args = parse_args()

    # Create appropriate scraper based on type
    if args.scraper_type == "simple":
        scraper = SimpleScraper(css_selector=args.css_selector, attribute=args.attribute)
    elif args.scraper_type == "product":
        scraper = ProductScraper(url=args.url)
    else:
        msg = f"Unknown scraper type: {args.scraper_type}"
        raise ValueError(msg)

    # Create monitor
    monitor = SiteMonitor(url=args.url, site_scraper=scraper, data_file=args.data_file)

    if args.test:
        monitor.send_test_alert()
    else:
        monitor.monitor()


if __name__ == "__main__":
    main()
