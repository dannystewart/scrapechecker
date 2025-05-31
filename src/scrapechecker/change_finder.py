"""Generic change finder that works with any data structure."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from polykit.log import PolyLog

if TYPE_CHECKING:
    from scrapechecker.base_scraper import BaseScraper


class ChangeFinder:
    """Track and find changes in any type of data.

    Args:
        site_scraper: The site-specific scraper for generating item keys.
    """

    def __init__(self, site_scraper: BaseScraper) -> None:
        """Initialize the change finder."""
        self.logger = PolyLog.get_logger()
        self.site_scraper = site_scraper

        # Fields to ignore when detecting changes (noise fields)
        self.ignored_fields = {"is_target"}

    def find_changes(
        self, current_items: list[dict[str, Any]], previous_items: list[dict[str, Any]]
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]],
    ]:
        """Find new, removed, and changed items.

        Args:
            current_items: The current data items.
            previous_items: The previous data items.

        Returns:
            Tuple of (new_items, removed_items, changed_items).
        """
        self.logger.debug(
            "Checking for changes in %s current items vs %s previous items...",
            len(current_items),
            len(previous_items),
        )

        current_items_dict = {self.site_scraper.get_item_key(item): item for item in current_items}
        previous_items_dict = {
            self.site_scraper.get_item_key(item): item for item in previous_items
        }

        new_items = [
            item for key, item in current_items_dict.items() if key not in previous_items_dict
        ]
        removed_items = [
            item for key, item in previous_items_dict.items() if key not in current_items_dict
        ]
        changed_items = self._find_changed_items(current_items_dict, previous_items_dict)

        self.logger.debug(
            "Found %s new, %s removed, %s changed items.",
            len(new_items),
            len(removed_items),
            len(changed_items),
        )

        return new_items, removed_items, changed_items

    def _find_changed_items(
        self, current_items: dict, previous_items: dict
    ) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple]]]:
        """Find items that have changed between current and previous data."""
        changed_items = []
        for key, current_item in current_items.items():
            if key in previous_items:
                previous_item = previous_items[key]
                changes = self._get_item_changes(previous_item, current_item)
                if changes:
                    changed_items.append((previous_item, current_item, changes))
        return changed_items

    def _get_item_changes(self, old_item: dict, new_item: dict) -> dict[str, tuple[str, str]]:
        """Get the changes between two versions of an item."""
        return {
            key: (old_item[key], new_item[key])
            for key in old_item
            if key in new_item and old_item[key] != new_item[key] and key not in self.ignored_fields
        }

    def filter_to_target_only(
        self,
        new_items: list[dict[str, Any]],
        removed_items: list[dict[str, Any]],
        changed_items: list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]],
    ]:
        """Filter changes to only include the target contestant.

        Args:
            new_items: The list of new items.
            removed_items: The list of removed items.
            changed_items: The list of changed items.

        Returns:
            A tuple containing the filtered new items, removed items, and changed items.
        """
        if not self.site_scraper.target_item:
            return new_items, removed_items, changed_items

        target_name = self.site_scraper.target_item.lower()

        def is_target_item(item: dict[str, Any]) -> bool:
            """Check if an item is the target contestant."""
            return "name" in item and target_name in item["name"].lower()

        filtered_new = [item for item in new_items if is_target_item(item)]
        filtered_removed = [item for item in removed_items if is_target_item(item)]
        filtered_changed = [
            (old_item, new_item, changes)
            for old_item, new_item, changes in changed_items
            if is_target_item(new_item)
        ]

        return filtered_new, filtered_removed, filtered_changed
