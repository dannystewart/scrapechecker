"""Generic formatter for displaying items and changes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scrapechecker.base_scraper import BaseScraper


class ContestFormatter:
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
            message_parts.append(self._format_changed_items(changed_items, current_items))

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
        self,
        changed_items: list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]],
        current_items: list[dict[str, Any]] | None = None,
    ) -> str:
        """Format changed items section."""
        current_items = current_items or []

        # Filter to relevant changes when we have a target
        if self.site_scraper.target_item:
            items_to_show = self._get_focused_changes(changed_items, current_items)
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
            items_to_show = self._get_focused_rankings(current_items, max_items=7)
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
        self, items: list[dict[str, Any]], max_items: int = 7
    ) -> list[dict[str, Any]]:
        """Get a focused view of rankings with adaptive strategy.

        When target is close to top (within 10 spots): Show path to #1
        When target is further back: Show local context (±2 around target)

        Args:
            items: All ranking items, assumed to be sorted by rank.
            max_items: Maximum number of items to return.

        Returns:
            A filtered list with adaptive focus strategy.
        """
        if not self.site_scraper.target_item:
            return items[:max_items]

        target_name = self.site_scraper.target_item.lower()
        target_index = None
        target_rank = None

        # Find the target contestant
        for i, item in enumerate(items):
            if "name" in item and target_name in item["name"].lower():
                target_index = i
                target_rank = item.get("rank", i + 1)  # Use rank or position as fallback
                break

        if target_index is None:  # Target not found, return top items
            return items[:max_items]

        # Adaptive strategy based on target's rank
        if target_rank and target_rank <= 10:
            # Close to top: Show path to victory (include #1 through target + a bit below)
            end_index = min(target_index + 2, len(items))  # Target + 1-2 below
            return items[:end_index]

        # Further back: Show local context (±2 around target)
        items_above = min(2, target_index)
        items_below = min(2, len(items) - target_index - 1)

        start_index = target_index - items_above
        end_index = target_index + items_below + 1

        return items[start_index:end_index]

    def _get_focused_changes(
        self,
        changed_items: list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]],
        current_items: list[dict[str, Any]],
    ) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, tuple[str, str]]]]:
        """Get a focused view of changed items around the target contestant.

        Args:
            changed_items: All changed items.
            current_items: All current items.

        Returns:
            A filtered list focusing on target contestant and nearby competitors.
        """
        if not self.site_scraper.target_item:
            return changed_items[: self.max_results]

        target_name = self.site_scraper.target_item.lower()
        focused_items = []

        # Find target's current rank from current_items
        target_current_rank = None
        for item in current_items:
            if "name" in item and target_name in item["name"].lower():
                target_current_rank = item.get("rank")
                break

        if target_current_rank is None:
            return changed_items[: self.max_results]

        # Include target's changes if any
        for old_item, new_item, changes in changed_items:
            if "name" in new_item and target_name in new_item["name"].lower():
                focused_items.append((old_item, new_item, changes))
                break

        # Competitors who threaten target (moving above or getting stronger)
        for old_item, new_item, changes in changed_items:
            if "name" in new_item and target_name in new_item["name"].lower():
                continue  # Skip target (already handled)

            old_rank = old_item.get("rank")
            new_rank = new_item.get("rank")

            is_above_target = new_rank and target_current_rank and new_rank < target_current_rank
            moved_above_target = old_rank is None or (old_rank and old_rank >= target_current_rank)
            already_above_and_stronger = (
                old_rank and old_rank < target_current_rank and "votes" in changes
            )

            should_include = is_above_target and (moved_above_target or already_above_and_stronger)

            if should_include:
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
