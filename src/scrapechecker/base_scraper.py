"""Base scraper interface for site-specific implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from polykit.log import PolyLog

if TYPE_CHECKING:
    from selenium.webdriver.firefox.webdriver import WebDriver


class BaseScraper(ABC):
    """Abstract base class for site-specific scrapers."""

    def __init__(self, url: str, target_item: str | None = None) -> None:
        """Initialize the base scraper.

        Args:
            url: The URL to scrape.
            target_item: Optional target item name to focus monitoring on.
        """
        self.url = url
        self.target_item = target_item
        self.logger = PolyLog.get_logger()

    @abstractmethod
    def extract_data(self, driver: WebDriver) -> list[dict[str, Any]]:
        """Extract data from the webpage using the provided driver.

        Args:
            driver: The Selenium WebDriver instance.

        Returns:
            A list of dictionaries containing extracted data items.
        """

    @abstractmethod
    def get_item_key(self, item: dict[str, Any]) -> str:
        """Generate a unique key for an item to track changes.

        Args:
            item: The data item dictionary.

        Returns:
            A unique string identifier for the item.
        """

    def filter_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter items based on criteria. Override if needed.

        Args:
            items: The list of extracted items.

        Returns:
            A filtered list of items.
        """
        return items

    def format_item(self, item: dict[str, Any]) -> str:
        """Format an item for display. Override for custom formatting.

        Args:
            item: The data item dictionary.

        Returns:
            The formatted string representation of the item.
        """
        return str(item)
