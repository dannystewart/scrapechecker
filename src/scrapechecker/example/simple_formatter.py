"""Simple formatter for basic scrapers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapechecker.base_formatter import BaseFormatter

if TYPE_CHECKING:
    from scrapechecker.types import ItemChange  # noqa: F401


class SimpleFormatter(BaseFormatter):
    """Simple formatter that provides basic change notifications without advanced features.

    This formatter is suitable for simple scrapers that don't need contest-specific
    features like target tracking, competitive intelligence, or adaptive displays.
    """

    def display_item(self, item: dict[str, Any]) -> None:
        """Display an item's information."""
        formatted = self.site_scraper.format_item(item)
        print(f"• {formatted}")

    def format_changes_message(
        self,
        new_items: list[dict[str, Any]],
        removed_items: list[dict[str, Any]],
        changed_items: list[ItemChange],
        current_items: list[dict[str, Any]] | None = None,  # noqa: F841
    ) -> str:
        """Format a simple message describing changes in items."""
        message_parts = []

        if new_items:
            message_parts.append(self._format_new_items(new_items))

        if removed_items:
            message_parts.append(self._format_removed_items(removed_items))

        if changed_items:
            message_parts.append(self._format_changed_items(changed_items, current_items))

        return "\n\n".join(message_parts) if message_parts else "No changes detected."

    def _format_new_items(self, new_items: list[dict[str, Any]]) -> str:
        """Format new items section."""
        count = len(new_items)
        items_to_show = new_items[: self.max_results]

        message = f"🆕 {count} New Item{'s' if count != 1 else ''}:\n"

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

        message = f"❌ {count} Removed Item{'s' if count != 1 else ''}:\n"

        for item in items_to_show:
            formatted = self.site_scraper.format_item(item)
            message += f"• {formatted}\n"

        if count > self.max_results:
            message += f"... and {count - self.max_results} more\n"

        return message.rstrip()

    def _format_changed_items(
        self,
        changed_items: list[ItemChange],
        current_items: list[dict[str, Any]] | None = None,  # noqa: ARG002
    ) -> str:
        """Format changed items section."""
        count = len(changed_items)
        items_to_show = changed_items[: self.max_results]

        message = f"🔄 {count} Changed Item{'s' if count != 1 else ''}:\n"

        for item_change in items_to_show:
            formatted = self.site_scraper.format_item(item_change.new_item)
            message += f"• {formatted}\n"

            # Show what changed
            for field_change in item_change.changes.values():
                message += f"    └ {field_change.field_name}: {field_change.old_value} → {field_change.new_value}\n"

        if count > self.max_results:
            message += f"... and {count - self.max_results} more\n"

        return message.rstrip()
