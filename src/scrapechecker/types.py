"""Generic data types for the scrapechecker framework."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FieldChange:
    """Represents a change in a single field of an item."""

    field_name: str
    old_value: str
    new_value: str

    def __str__(self) -> str:
        """Format the change for display."""
        return f"{self.field_name}: {self.old_value} → {self.new_value}"


@dataclass
class ItemChange:
    """Represents a change in an item between two states.

    This is a generic change representation that can work with any item type.
    The old_item and new_item can be raw dicts or domain-specific dataclasses.
    """

    old_item: Any  # Could be dict[str, Any] or domain-specific dataclass
    new_item: Any  # Could be dict[str, Any] or domain-specific dataclass
    changes: dict[str, FieldChange]

    def get_change(self, field_name: str) -> FieldChange | None:
        """Get a specific field change by name."""
        return self.changes.get(field_name)

    def has_change(self, field_name: str) -> bool:
        """Check if a specific field changed."""
        return field_name in self.changes

    def format_changes(self, indent: str = "    ") -> str:
        """Format all changes for display."""
        lines = [f"{indent}{change}" for change in self.changes.values()]
        return "\n".join(lines)
