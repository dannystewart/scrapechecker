"""Contest scraper for pet voting contests."""

from __future__ import annotations

from operator import itemgetter
from typing import TYPE_CHECKING, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from scrapechecker.base_scraper import BaseScraper

if TYPE_CHECKING:
    from selenium.webdriver.firefox.webdriver import WebDriver


class ContestScraper(BaseScraper):
    """Scraper for pet contest voting sites.

    Tracks contestant rankings, vote counts, and changes in position.

    Args:
        url: The contest URL to monitor.
        target_item: Optional name of specific contestant to highlight.
    """

    def __init__(self, url: str, target_item: str | None = None) -> None:
        """Initialize the contest scraper."""
        super().__init__(url, target_item)

    def extract_data(self, driver: WebDriver) -> list[dict[str, Any]]:
        """Extract contestant data from the contest page."""
        contestants = []

        # Wait for the page to load
        wait = WebDriverWait(driver, 10)

        try:
            # Wait for the search results container to load
            wait.until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, "searchMainCont"))
            )

            # Find all contestant entries
            contestant_elements = driver.find_elements(By.CLASS_NAME, "searchEntryCont")

            for element in contestant_elements:
                try:
                    # Extract rank from lbNumberSearch div
                    rank_element = element.find_element(By.CLASS_NAME, "lbNumberSearch")
                    rank = int(rank_element.text.strip())

                    # Extract name from searchTitle div
                    name_element = element.find_element(By.CLASS_NAME, "searchTitle")
                    name = name_element.text.strip()

                    # Extract votes from searchVotes div
                    votes_element = element.find_element(By.CLASS_NAME, "searchVotes")
                    votes_text = votes_element.text.strip()
                    # Extract number from "150 Votes" format
                    votes = int(votes_text.split()[0])

                    contestant = {
                        "rank": rank,
                        "name": name,
                        "votes": votes,
                        "is_target": self.target_item and name.lower() == self.target_item.lower(),
                    }
                    contestants.append(contestant)

                except Exception as e:
                    self.logger.warning("Error parsing contestant element: %s", e)
                    continue

            # Sort by rank to ensure consistent ordering
            contestants.sort(key=itemgetter("rank"))

        except Exception as e:
            self.logger.error("Error extracting contest data: %s", e)
            return []

        return contestants

    def get_item_key(self, item: dict[str, Any]) -> str:
        """Generate unique key for each contestant."""
        return f"contestant_{item['name'].lower().replace(' ', '_')}"

    def filter_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Optional filtering - return all contestants by default."""
        return items

    def format_item(self, item: dict[str, Any]) -> str:
        """Format a contestant for display."""
        rank_emoji = self._get_rank_emoji(item["rank"])
        target_indicator = " 🎯" if item.get("is_target") else ""

        return f"{rank_emoji} {item['rank']}. <b>{item['name']}</b> ({item['votes']} votes{target_indicator})"

    def _get_rank_emoji(self, rank: int) -> str:
        """Get emoji for ranking position."""
        rank_emojis = {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }
        return rank_emojis.get(rank, "🏅")
