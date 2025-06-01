"""Generic formatter for displaying items and changes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scrapechecker.base_scraper import BaseScraper


class Formatter:
    """Format display of items and change messages.

    Args:
        site_scraper: The site-specific scraper for formatting items.
        max_results: The maximum number of items to include in messages.
    """

    def __init__(self, site_scraper: BaseScraper, max_results: int = 5) -> None:
        """Initialize the formatter."""
        self.site_scraper = site_scraper
        self.max_results = max_results

    def display_item(self, item: dict[str, Any]) -> None:
        """Display an item's information."""
        formatted = self.site_scraper.format_item(item)
        print(formatted)

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
            The formatted HTML message string.
        """
        message_parts = []

        if new_items:
            message_parts.append(self._format_new_items(new_items))

        if removed_items:
            message_parts.append(self._format_removed_items(removed_items))

        if changed_items:
            message_parts.append(self._format_changed_items(changed_items))

        # Add current rankings section if we have current items and there were changes
        if current_items and (new_items or removed_items or changed_items):
            message_parts.append(self._format_current_rankings(current_items))

        return "\n\n".join(message_parts) if message_parts else "No changes detected."

    def _format_new_items(self, new_items: list[dict[str, Any]]) -> str:
        """Format new items section."""
        count = len(new_items)
        items_to_show = new_items[: self.max_results]

        message = f"<b>🆕 {count} New Item{'s' if count != 1 else ''}:</b>\n"

        for item in items_to_show:
            formatted = self.site_scraper.format_item(item)
            message += f"• {formatted}\n"

        if count > self.max_results:
            message += f"... and {count - self.max_results} more\n"

        return message.rstrip()

    def _format_removed_items(self, removed_items: list[dict[str, Any]]) -> str:
        """Format removed items section."""
        count = len(removed_items)
        items_to_show = removed_items[: self.max_results]

        message = f"<b>❌ {count} Removed Item{'s' if count != 1 else ''}:</b>\n"

        for item in items_to_show:
            formatted = self.site_scraper.format_item(item)
            message += f"• {formatted}\n"

        if count > self.max_results:
            message += f"... and {count - self.max_results} more\n"

        return message.rstrip()

    def _format_changed_items(
        self, changed_items: list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]]
    ) -> str:
        """Format changed items section."""
        # Filter to relevant changes when we have a target
        if self.site_scraper.target_item:
            items_to_show = self._get_focused_changes(changed_items)
        else:
            items_to_show = changed_items[: self.max_results]

        if not items_to_show:
            return ""  # No relevant changes to show

        message = (
            f"<b>🔄 {len(items_to_show)} Key Change{'s' if len(items_to_show) != 1 else ''}:</b>\n"
        )

        for _old_item, new_item, changes in items_to_show:
            formatted = self.site_scraper.format_item(new_item)
            message += f"• {formatted}\n"

            # Show what changed
            for field, (old_val, new_val) in changes.items():
                message += f"    └ <b>{field}:</b> {old_val} → {new_val}\n"

        return message.rstrip()

    def _format_current_rankings(self, current_items: list[dict[str, Any]]) -> str:
        """Format current rankings section."""
        count = len(current_items)

        if self.site_scraper.target_item:
            # For change notifications, only show a focused view around the target
            items_to_show = self._get_focused_rankings(current_items, max_items=5)
            if len(items_to_show) < count:
                message = f"<b>📊 Current Rankings (showing {len(items_to_show)} of {count}):</b>\n"
            else:
                message = f"<b>📊 Current Rankings ({count}):</b>\n"
        else:
            # For full listings, show up to max_results
            items_to_show = current_items[: self.max_results]
            message = f"<b>📊 Current Rankings ({count}):</b>\n"

        for item in items_to_show:
            formatted = self.site_scraper.format_item(item)
            message += f"• {formatted}\n"

        if len(items_to_show) < count and not self.site_scraper.target_item:
            message += f"... and {count - len(items_to_show)} more\n"

        return message.rstrip()

    def _get_focused_rankings(
        self, items: list[dict[str, Any]], max_items: int = 5
    ) -> list[dict[str, Any]]:
        """Get a focused view of rankings around the target contestant.

        Args:
            items: All ranking items, assumed to be sorted by rank.
            max_items: Maximum number of items to return.

        Returns:
            A filtered list focusing on target contestant and nearby competitors.
        """
        if not self.site_scraper.target_item:
            return items[:max_items]

        target_name = self.site_scraper.target_item.lower()
        target_index = None

        # Find the target contestant
        for i, item in enumerate(items):
            if "name" in item and target_name in item["name"].lower():
                target_index = i
                break

        if target_index is None:
            # Target not found, return top items
            return items[:max_items]

        # Calculate how many items to show above and below target (at least 2)
        items_above = min(2, target_index)
        items_below = min(2, len(items) - target_index - 1)

        # Adjust if we have room for more
        total_context = items_above + 1 + items_below  # +1 for target
        if total_context < max_items:
            # Add more items above if possible
            extra_above = min(max_items - total_context, target_index - items_above)
            items_above += extra_above
            total_context += extra_above

            # Add more items below if still have room
            if total_context < max_items:
                extra_below = min(
                    max_items - total_context, len(items) - target_index - 1 - items_below
                )
                items_below += extra_below

        start_index = target_index - items_above
        end_index = target_index + items_below + 1

        return items[start_index:end_index]

    def _get_focused_changes(
        self, changed_items: list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]]
    ) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]]:
        """Get a focused view of changed items around the target contestant.

        Args:
            changed_items: All changed items.

        Returns:
            A filtered list focusing on target contestant and nearby competitors.
        """
        if not self.site_scraper.target_item:
            return changed_items[: self.max_results]

        target_name = self.site_scraper.target_item.lower()
        focused_items = []
        target_old_rank = None
        target_new_rank = None

        # First pass: find target's old and new ranks
        for old_item, new_item, changes in changed_items:
            if "name" in new_item and target_name in new_item["name"].lower():
                target_old_rank = old_item.get("rank")
                target_new_rank = new_item.get("rank")
                focused_items.append((old_item, new_item, changes))
                break

        # If no target found, return empty
        if target_old_rank is None:
            return focused_items

        # Second pass: find competitors who directly threaten target's position
        for old_item, new_item, changes in changed_items:
            if "name" in new_item and target_name in new_item["name"].lower():
                continue  # Skip target (already added)

            old_rank = old_item.get("rank")
            new_rank = new_item.get("rank")

            # Only include competitors who moved into target's current rank range
            if (
                new_rank
                and target_new_rank
                and new_rank <= target_new_rank  # Competitor is now at or above target
                and (
                    # Competitor improved to threaten target's position
                    old_rank is None  # New competitor
                    or (
                        old_rank
                        and old_rank > target_new_rank  # Moved from below to above/equal target
                    )
                )
            ):
                focused_items.append((old_item, new_item, changes))

        return focused_items

    def format_full_rankings(self, current_items: list[dict[str, Any]]) -> str:
        """Format full rankings without filtering (used for --send command)."""
        count = len(current_items)
        items_to_show = current_items[: self.max_results]

        message = f"<b>📊 Current Rankings ({count}):</b>\n"

        for item in items_to_show:
            formatted = self.site_scraper.format_item(item)
            message += f"• {formatted}\n"

        if count > self.max_results:
            message += f"... and {count - self.max_results} more\n"

        return message.rstrip()
