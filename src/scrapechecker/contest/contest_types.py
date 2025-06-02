"""Contest-specific data types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ContestItem:
    """Represents a contest participant with typed fields."""

    name: str
    rank: int | None = None
    votes: int | None = None
    is_target: bool = False
    raw_data: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContestItem:
        """Create a ContestItem from raw scraped data."""
        return cls(
            name=data.get("name", ""),
            rank=data.get("rank"),
            votes=data.get("votes"),
            is_target=data.get("is_target", False),
            raw_data=data,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert back to dictionary format for compatibility."""
        result = {
            "name": self.name,
            "is_target": self.is_target,
        }

        if self.rank is not None:
            result["rank"] = self.rank
        if self.votes is not None:
            result["votes"] = self.votes

        # Include any additional fields from raw_data
        if self.raw_data:
            for key, value in self.raw_data.items():
                if key not in result:
                    result[key] = value

        return result
