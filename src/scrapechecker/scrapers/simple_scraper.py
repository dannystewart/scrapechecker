"""Example of a simple scraper for monitoring any basic website changes."""

from __future__ import annotations

from typing import Any

from selenium.webdriver.common.by import By

from scrapechecker.base_scraper import BaseScraper


class SimpleScraper(BaseScraper):
    """Simple scraper that can monitor text content on any webpage."""

    def __init__(self, css_selector: str = "body", attribute: str = "text"):
        """Initialize simple scraper.

        Args:
            css_selector: The CSS selector to find elements.
            attribute: The attribute to extract ('text', 'href', etc.) or 'text' for text content.
        """
        self.css_selector = css_selector
        self.attribute = attribute

    def extract_data(self, driver) -> list[dict[str, Any]]:
        """Extract data from webpage using CSS selector."""
        elements = driver.find_elements(By.CSS_SELECTOR, self.css_selector)

        items = []
        for i, element in enumerate(elements):
            if self.attribute == "text":
                content = element.text.strip()
            else:
                content = element.get_attribute(self.attribute)

            if content:  # Only include non-empty content
                items.append({
                    "id": f"item_{i}",
                    "content": content,
                    "selector": self.css_selector,
                    "position": i,
                })

        return items

    def get_item_key(self, item: dict[str, Any]) -> str:
        """Generate unique key for an item."""
        return f"{item['selector']}_{item['position']}"

    def format_item(self, item: dict[str, Any]) -> str:
        """Format item for display."""
        content = item["content"]
        if len(content) > 100:
            content = content[:97] + "..."
        return f"Position {item['position']}: {content}"


class ProductScraper(BaseScraper):
    """Example scraper for monitoring product listings."""

    def extract_data(self, driver) -> list[dict[str, Any]]:
        """Extract product data - customize this for your target site."""
        # Example: scrape product titles and prices
        products = []

        # This is a generic example - you'd customize these selectors
        try:
            product_elements = driver.find_elements(By.CSS_SELECTOR, ".product-item")

            for i, product in enumerate(product_elements):
                try:
                    title_elem = product.find_element(By.CSS_SELECTOR, ".product-title")
                    price_elem = product.find_element(By.CSS_SELECTOR, ".product-price")

                    products.append({
                        "id": f"product_{i}",
                        "title": title_elem.text.strip(),
                        "price": price_elem.text.strip(),
                        "position": i,
                    })
                except Exception:
                    continue  # Skip products with missing data

        except Exception:
            # Fallback: just get all text if specific selectors don't work
            body = driver.find_element(By.TAG_NAME, "body")
            products = [
                {
                    "id": "page_content",
                    "title": "Page Content",
                    "content": body.text[:500],  # First 500 chars
                    "position": 0,
                }
            ]

        return products

    def get_item_key(self, item: dict[str, Any]) -> str:
        """Generate unique key for a product."""
        return item["id"]

    def format_item(self, item: dict[str, Any]) -> str:
        """Format product for display."""
        if "title" in item and "price" in item:
            return f"{item['title']} - {item['price']}"
        return f"{item.get('title', item.get('content', str(item)))}"
