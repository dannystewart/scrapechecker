"""Generic web scraper that works with any BaseScraper implementation."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from polykit.log import PolyLog
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

if TYPE_CHECKING:
    from scrapechecker.base_scraper import BaseScraper


class WebScraper:
    """Generic web scraper that works with any site-specific scraper."""

    def __init__(self, url: str, site_scraper: BaseScraper[Any]) -> None:
        """Initialize the generic web scraper.

        Args:
            url: URL to scrape
            site_scraper: Site-specific scraper implementation
        """
        self.logger = PolyLog.get_logger()
        self.url = url
        self.site_scraper = site_scraper

    def setup_driver(self) -> webdriver.Firefox:
        """Set up a headless Firefox driver."""
        self.logger.debug("Setting up Firefox driver.")
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")

        # Try to use locally installed GeckoDriver to avoid rate limiting
        geckodriver_path = "/usr/local/bin/geckodriver"
        if Path(geckodriver_path).exists():
            self.logger.debug("Using locally installed GeckoDriver.")
            service = FirefoxService(executable_path=geckodriver_path)
        else:
            self.logger.debug("Local GeckoDriver not found. Falling back to WebDriver Manager.")
            try:
                service = FirefoxService(GeckoDriverManager().install())
            except Exception as e:
                self.logger.error("Failed to set up driver using WebDriver Manager: %s", str(e))
                raise

        return webdriver.Firefox(service=service, options=firefox_options)

    @contextmanager
    def managed_driver(self):
        """Context manager for the driver."""
        self.logger.debug("Setting up driver.")
        driver = self.setup_driver()
        try:
            yield driver
        finally:
            self.logger.debug("Closing driver.")
            try:
                driver.quit()
            except Exception as e:
                self.logger.error("Error closing driver: %s", str(e))

    def scrape_data(self) -> list[Any]:
        """Scrape data using the site-specific scraper."""
        try:
            with self.managed_driver() as driver:
                self.logger.info("Navigating to %s", self.url)
                driver.get(self.url)

                self.logger.debug("Extracting data...")
                raw_data = self.site_scraper.extract_data(driver)

                self.logger.debug("Filtering data...")
                filtered_data = self.site_scraper.filter_items(raw_data)

            self.logger.info("Found %s items after filtering.", len(filtered_data))
            return filtered_data

        except Exception as e:
            self.logger.error("Error scraping data: %s", str(e))
            raise
