"""Generic site monitoring framework."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from polykit import TZ, PolyEnv, PolyLog

from scrapechecker.change_finder import ChangeFinder
from scrapechecker.formatter import Formatter
from scrapechecker.telegram import TelegramSender
from scrapechecker.web_scraper import WebScraper

if TYPE_CHECKING:
    from scrapechecker.base_scraper import BaseScraper


class SiteMonitor:
    """Generic site monitoring framework.

    Args:
        url: The URL to monitor.
        site_scraper: The site-specific scraper implementation.
        enable_telegram: Whether to enable Telegram notifications.
        data_file: File to store monitoring data.
        status_file: File to store daily status.
    """

    def __init__(
        self,
        url: str,
        site_scraper: BaseScraper,
        enable_telegram: bool = True,
        data_file: str = "monitoring_data.json",
        status_file: str = "daily_status.json",
    ) -> None:
        """Initialize the site monitor."""
        self.logger = PolyLog.get_logger()
        self.env = PolyEnv()
        self.url = url
        self.site_scraper = site_scraper
        self.data_file = data_file
        self.status_file = status_file

        # Configure environment variables for Telegram
        self.env.add_var("TELEGRAM_API_TOKEN")
        self.env.add_var("TELEGRAM_CHAT_ID")

        # Configure Telegram if enabled
        if enable_telegram:
            self._configure_telegram()

        # Initialize components
        self.scraper = WebScraper(url, site_scraper)
        self.formatter = Formatter(site_scraper)
        self.change_finder = ChangeFinder(site_scraper)

    def monitor(self) -> None:
        """Run the monitoring process."""
        current_items = self.scraper.scrape_data()
        previous_items = self.load_previous_data()

        new_items, removed_items, changed_items = self.change_finder.find_changes(
            current_items, previous_items
        )

        # Update daily status
        self.update_daily_status(new_items, removed_items, changed_items)

        # Send notifications if there are any changes (focused filtering applied in formatter)
        if new_items or removed_items or changed_items:
            message = self.formatter.format_changes_message(
                new_items, removed_items, changed_items, current_items
            )

            # Only send if the formatted message has actual content
            if message and "Key Change" in message:
                self.send_telegram_alert(message)
            else:
                self.logger.info("No relevant changes detected for notifications.")
        else:
            self.logger.info("No changes detected.")

        # Display results
        if not current_items:
            self.logger.info("No items found.")
        else:
            self.logger.debug("Found %s items:", len(current_items))
            for item in current_items:
                self.formatter.display_item(item)

        # Save current data
        self.save_current_data(current_items)

        # Send daily status update (will only send on first run of the day)
        self.send_daily_status(len(current_items))

    def _configure_telegram(self) -> None:
        """Configure Telegram notifications."""
        if self.env.telegram_api_token and self.env.telegram_chat_id:
            try:
                self.telegram = TelegramSender(
                    self.env.telegram_api_token, self.env.telegram_chat_id
                )
                self.logger.debug("Telegram notifications enabled.")
            except Exception as e:
                self.logger.error("Failed to initialize Telegram: %s", str(e))
                self.telegram = None
        else:
            self.telegram = None
            self.logger.warning("Telegram notifications are not enabled.")

    def send_telegram_alert(self, message: str) -> None:
        """Send a Telegram alert."""
        if hasattr(self, "telegram") and self.telegram:
            try:
                self.telegram.send_message(message, parse_mode="HTML")
                self.logger.info("Telegram alert sent successfully.")
            except Exception as e:
                self.logger.error("Failed to send Telegram alert: %s", str(e))
        else:
            self.logger.warning("Telegram notifications are not enabled. Message not sent.")

    def load_previous_data(self) -> list[dict[str, Any]]:
        """Load previous data from file."""
        try:
            with Path(self.data_file).open(encoding="utf-8") as f:
                data = json.load(f)

            # Handle both old format (list) and new format (dict with history)
            if isinstance(data, list):
                self.logger.debug("Previous data loaded from %s (legacy format).", self.data_file)
                return data
            if isinstance(data, dict) and "current" in data:
                self.logger.debug("Previous data loaded from %s.", self.data_file)
                return data["current"]

            self.logger.warning("Unexpected data format in %s. Starting fresh.", self.data_file)
            return []
        except FileNotFoundError:
            self.logger.warning("No previous data file found. Starting fresh.")
            return []
        except json.JSONDecodeError:
            self.logger.error("Error decoding previous data file. Starting fresh.")
            return []

    def save_current_data(self, items: list[dict[str, Any]]) -> None:
        """Save current data to file with history."""
        try:
            # Load existing data to preserve history
            existing_data: dict[str, Any] = {}
            try:
                with Path(self.data_file).open(encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # Handle legacy format
                    if isinstance(loaded_data, list):
                        existing_data = {"current": loaded_data}
                    elif isinstance(loaded_data, dict):
                        existing_data = loaded_data
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            # Create new data structure with history
            new_data = {
                "current": items,
                "previous": existing_data.get("current", []),
                "timestamp": datetime.now(tz=TZ).isoformat(),
                "previous_timestamp": existing_data.get("timestamp"),
            }

            with Path(self.data_file).open("w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=2)
            self.logger.debug("Data saved to %s with history.", self.data_file)
        except Exception as e:
            self.logger.error("Failed to save data: %s", str(e))

    def send_daily_status(self, items_checked: int):
        """Send a daily status update on the first run of each day."""
        today = datetime.now(tz=TZ).date()
        now = datetime.now(tz=TZ)

        try:
            with Path(self.status_file).open(encoding="utf-8") as f:
                status_data = json.load(f)
        except FileNotFoundError:
            status_data = {"last_sent": None, "changes": 0}

        last_sent = (
            datetime.strptime(status_data["last_sent"], "%Y-%m-%d").replace(tzinfo=TZ).date()
            if status_data["last_sent"]
            else None
        )
        changes = status_data["changes"]

        if last_sent is None or last_sent < today:
            last_report_date = last_sent.strftime("%Y-%m-%d") if last_sent else "N/A"
            message = (
                f"<b>📅 Daily Status Update ({today}):</b>\n\n"
                f"✅ <b>Monitor Status:</b> Running smoothly at {now.strftime('%I:%M %p')}.\n"
                f"🔍 <b>Items Tracked:</b> {items_checked}\n"
                f"📈 <b>Changes Detected:</b> {changes} update{'s' if changes != 1 else ''} since {last_report_date}.\n\n"
                f"⏰ Next update will be tomorrow!"
            )
            self.send_telegram_alert(message)
            self.logger.debug("Sent daily status: %s", message)

            # Reset the counter and update last sent date
            status_data = {"last_sent": today.strftime("%Y-%m-%d"), "changes": 0}
        else:
            self.logger.debug("Daily status already sent today. Next update will be tomorrow.")

        with Path(self.status_file).open("w", encoding="utf-8") as f:
            json.dump(status_data, f)

    def update_daily_status(
        self,
        new_items: list[dict[str, Any]],
        removed_items: list[dict[str, Any]],
        changed_items: list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]],
    ):
        """Update the daily status with new changes."""
        try:
            with Path(self.status_file).open(encoding="utf-8") as f:
                status_data = json.load(f)
        except FileNotFoundError:
            status_data = {"last_sent": None, "changes": 0}

        # Ensure changes is an integer before adding to it
        if (
            "changes" not in status_data
            or not isinstance(status_data["changes"], int)
            or status_data["changes"] is None
        ):
            status_data["changes"] = 0

        # Calculate total changes
        total_changes = len(new_items) + len(removed_items) + len(changed_items)
        status_data["changes"] = int(status_data["changes"]) + total_changes

        with Path(self.status_file).open("w", encoding="utf-8") as f:
            json.dump(status_data, f)

    def send_test_alert(self, sample_data: list[dict[str, Any]] | None = None):
        """Send a test notification with sample data."""
        self.logger.info("Sending test alert via Telegram.")

        if sample_data is None:
            sample_data = [{"test": "data", "id": "1"}, {"test": "data", "id": "2"}]

        # Create sample changes
        new_items = sample_data[:1]
        removed_items = [{"test": "removed", "id": "3"}]
        changed_items = [
            ({"test": "old", "id": "2"}, {"test": "new", "id": "2"}, {"test": ("old", "new")})
        ]

        # Format and send the test message
        message = self.formatter.format_changes_message(
            new_items, removed_items, changed_items, sample_data
        )
        self.send_telegram_alert(f"<b>--- TEST NOTIFICATION ---</b>\n\n{message}")

    def replay_last_changes(self) -> str | None:
        """Replay the last detected changes for testing notification formatting.

        Returns:
            The formatted change message if history is available, None otherwise.
        """
        try:
            with Path(self.data_file).open(encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "current" not in data or "previous" not in data:
                self.logger.warning("No change history available for replay.")
                return None

            current_items = data["current"]
            previous_items = data["previous"]

            if not previous_items:
                self.logger.warning("No previous data available for replay.")
                return None

            # Find changes between previous and current
            new_items, removed_items, changed_items = self.change_finder.find_changes(
                current_items, previous_items
            )

            # Use the same focused filtering as live monitoring
            if not (new_items or removed_items or changed_items):
                self.logger.info("No changes to replay.")
                return None

            # Format the message with focused filtering
            message = self.formatter.format_changes_message(
                new_items, removed_items, changed_items, current_items
            )

            self.logger.info("Replayed changes from history:")
            self.logger.info(message)

            # Send via Telegram
            self.send_telegram_alert(message)
            self.logger.info("Replayed message sent via Telegram.")

            return message

        except Exception as e:
            self.logger.error("Failed to replay changes: %s", str(e))
            return None
