"""Generic site monitoring framework."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from polykit import PolyEnv, PolyLog

from scrapechecker.change_finder import ChangeFinder
from scrapechecker.telegram import TelegramSender
from scrapechecker.web_scraper import WebScraper

if TYPE_CHECKING:
    from scrapechecker.base_formatter import BaseFormatter
    from scrapechecker.base_scraper import BaseScraper

ItemType = TypeVar("ItemType")


class SiteMonitor[ItemType]:
    """Generic site monitoring framework.

    This class provides a generic framework for monitoring websites for changes.
    It can be used with any scraper and formatter implementation.

    Args:
        url: The URL to monitor.
        site_scraper: The scraper for extracting data from the site.
        formatter: The formatter for displaying items and changes.
        enable_telegram: Whether to enable Telegram notifications.
        data_file: File to store monitoring data.
    """

    def __init__(
        self,
        url: str,
        site_scraper: BaseScraper[ItemType],
        formatter: BaseFormatter[ItemType],
        enable_telegram: bool = True,
        data_file: str = "monitoring_data.json",
    ) -> None:
        """Initialize the site monitor."""
        self.logger = PolyLog.get_logger()
        self.env = PolyEnv()
        self.url = url
        self.site_scraper = site_scraper
        self.formatter = formatter
        self.data_file = data_file

        # Configure environment variables for Telegram
        self.env.add_var("TELEGRAM_API_TOKEN")
        self.env.add_var("TELEGRAM_CHAT_ID")

        # Initialize components
        self.change_finder = ChangeFinder(site_scraper)
        self.web_scraper = WebScraper(url, site_scraper)

        # Configure Telegram if enabled
        if enable_telegram:
            self._configure_telegram()

    def check_current_status(self) -> None:
        """Check current status with change detection but don't save data."""
        self.logger.info("Checking current status with change detection...")

        # Get current data using WebScraper
        current_items = self.web_scraper.scrape_data()
        previous_items = self.load_previous_data()

        # Convert items to dict format for change detection
        current_data = [
            item.to_dict() if hasattr(item, "to_dict") else item for item in current_items
        ]

        # Find changes
        new_items, removed_items, changed_items = self.change_finder.find_changes(
            current_data, previous_items
        )

        # Send notifications if there are any changes (focused filtering applied in formatter)
        if new_items or removed_items or changed_items:
            message = self.formatter.format_changes_message(
                new_items, removed_items, changed_items, current_data
            )
            if message and "Key Change" in message:
                self.send_telegram_alert(message)
                self.logger.info("Current status sent with change detection!")
            else:
                self.logger.info("No relevant changes detected for notifications.")
        else:
            self.logger.info("No changes detected between current and saved data.")

    def monitor(self) -> None:
        """Monitor the site for changes and send notifications."""
        self.logger.info("Starting monitoring for %s", self.url)

        # Get current data using WebScraper
        current_items = self.web_scraper.scrape_data()
        previous_items = self.load_previous_data()

        # Convert items to dict format for change detection
        current_data = [
            item.to_dict() if hasattr(item, "to_dict") else item for item in current_items
        ]

        # Find changes
        new_items, removed_items, changed_items = self.change_finder.find_changes(
            current_data, previous_items
        )

        # Send notifications if there are any changes (focused filtering applied in formatter)
        if new_items or removed_items or changed_items:
            message = self.formatter.format_changes_message(
                new_items, removed_items, changed_items, current_data
            )
            if message and "Key Change" in message:
                self.send_telegram_alert(message)
                self.logger.info("Changes detected and notification sent!")
            else:
                self.logger.info("Changes detected but no relevant notifications to send.")
        else:
            self.logger.info("No changes detected.")

        # Display current items
        self.logger.info("Current items:")
        for item in current_items:
            self.logger.info("  %s", self.formatter.display_item(item))

        # Save current data (use converted dict format for JSON serialization)
        self.save_current_data(current_data)

    def _configure_telegram(self) -> None:
        """Configure Telegram notifications."""
        if self.env.telegram_api_token and self.env.telegram_chat_id:
            self.telegram_sender = TelegramSender(
                self.env.telegram_api_token, self.env.telegram_chat_id
            )
            self.logger.info("Telegram notifications enabled.")
        else:
            self.telegram_sender = None
            self.logger.warning(
                "Telegram notifications disabled. Set TELEGRAM_API_TOKEN and TELEGRAM_CHAT_ID."
            )

    def send_telegram_alert(self, message: str) -> None:
        """Send a Telegram alert."""
        if self.telegram_sender:
            try:
                self.telegram_sender.send_message(message)
                self.logger.info("Telegram alert sent successfully.")
            except Exception as e:
                self.logger.error("Failed to send Telegram alert: %s", str(e))
        else:
            self.logger.warning("Telegram not configured. Alert not sent.")

    def load_previous_data(self) -> list[dict[str, Any]]:
        """Load previous data from file."""
        try:
            with Path(self.data_file).open(encoding="utf-8") as f:
                data = json.load(f)
                # Handle both old format (list) and new format (dict with current/previous)
                if isinstance(data, list):
                    return data
                return data.get("current", [])
        except FileNotFoundError:
            self.logger.info("No previous data found. This might be the first run.")
            return []
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse previous data: %s", str(e))
            return []

    def save_current_data(self, items: list[dict[str, Any]]) -> None:
        """Save current data to file with history."""
        try:
            # Load existing data to preserve history
            existing_data: dict[str, Any] = {}
            try:
                with Path(self.data_file).open(encoding="utf-8") as f:
                    existing_data = json.load(f)
                    # Handle migration from old format
                    if isinstance(existing_data, list):
                        existing_data = {"current": existing_data}
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            # Create new data structure with history
            new_data = {
                "current": items,
                "previous": existing_data.get("current", []),
                "timestamp": datetime.now(UTC).isoformat(),
                "previous_timestamp": existing_data.get("timestamp"),
            }

            with Path(self.data_file).open("w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=2)
            self.logger.debug("Data saved to %s", self.data_file)
        except Exception as e:
            self.logger.error("Failed to save data: %s", str(e))

    def replay_last_changes(self) -> str | None:
        """Replay the last detected changes for testing."""
        self.logger.info("Replaying last detected changes...")

        try:
            with Path(self.data_file).open(encoding="utf-8") as f:
                data = json.load(f)

            # Handle both old and new data formats
            if isinstance(data, list):
                self.logger.warning("No change history available in old data format.")
                return None

            current_data = data.get("current", [])
            previous_data = data.get("previous", [])

            if not current_data or not previous_data:
                self.logger.warning(
                    "Insufficient data for replay. Need both current and previous data."
                )
                return None

            # Find changes using the same logic as monitor()
            new_items, removed_items, changed_items = self.change_finder.find_changes(
                current_data, previous_data
            )

            if new_items or removed_items or changed_items:
                message = self.formatter.format_changes_message(
                    new_items, removed_items, changed_items, current_data
                )
                self.logger.info(
                    "Replayed changes: %d new, %d removed, %d changed",
                    len(new_items),
                    len(removed_items),
                    len(changed_items),
                )
                return message
            self.logger.info("No changes found in replay data.")
            return None

        except FileNotFoundError:
            self.logger.error("No data file found for replay.")
            return None
        except Exception as e:
            self.logger.error("Failed to replay changes: %s", str(e))
            return None
