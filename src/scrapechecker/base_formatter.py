"""Base formatter class for different scraper types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scrapechecker.base_scraper import BaseScraper


class BaseFormatter(ABC):
    """Base class for formatters that handle display and messaging for scrapers."""

    def __init__(self, site_scraper: BaseScraper, max_results: int = 10):
        """Initialize the formatter.

        Args:
            site_scraper: The scraper instance this formatter will work with.
            max_results: Maximum number of results to show in formatted output.
        """
        self.site_scraper = site_scraper
        self.max_results = max_results

    @abstractmethod
    def format_changes_message(
        self,
        new_items: list[dict[str, Any]],
        removed_items: list[dict[str, Any]],
        changed_items: list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]],
        current_items: list[dict[str, Any]] | None = None,
    ) -> str:
        """Format a message describing changes in items.

        Args:
            new_items: The list of new items.
            removed_items: The list of removed items.
            changed_items: The list of (old_item, new_item, changes) tuples.
            current_items: Optional current state of all items to show at the end.

        Returns:
            The formatted message string.
        """
        raise NotImplementedError

    @abstractmethod
    def display_item(self, item: dict[str, Any]) -> None:
        """Display a single item to the console.

        Args:
            item: The item to display.
        """
        raise NotImplementedError
