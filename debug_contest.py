"""Debug script to see what the contest page actually contains."""

from __future__ import annotations

import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait


def debug_contest_page():
    """Debug the contest page to see its actual structure."""

    # Set up Firefox options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode

    driver = webdriver.Firefox(options=options)

    try:  # noqa: PLR1702
        print("Navigating to contest page...")
        driver.get("https://www.gogophotocontest.com/citydogsandcitykittiesrescue/search")

        # Wait for page to load
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Give extra time for dynamic content
        time.sleep(5)

        print("\n=== PAGE TITLE ===")
        print(driver.title)

        print("\n=== FULL PAGE SOURCE (first 2000 chars) ===")
        page_source = driver.page_source
        print(page_source[:2000])

        print("\n=== LOOKING FOR CONTEST ENTRIES ===")
        # Try to find elements that might contain contest data
        possible_selectors = [
            "div",
            ".entry",
            ".contestant",
            ".vote",
            "[class*='entry']",
            "[class*='vote']",
            "[class*='contest']",
        ]

        for selector in possible_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector '{selector}'")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.text.strip()
                        if text and len(text) < 200:
                            print(f"  Element {i}: {text}")
            except Exception as e:
                print(f"Error with selector '{selector}': {e}")

        print("\n=== SEARCHING FOR VOTE PATTERNS ===")
        import re

        # Look for various vote patterns
        patterns = [
            r"(\d+)\s+[Vv]otes?",
            r"[Vv]otes?:?\s*(\d+)",
            r"\[(\d+)([^0-9]+?)(\d+)\s+[Vv]otes?\]",
            r"(\w+).*?(\d+)\s+[Vv]otes?",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                print(f"Pattern '{pattern}' found {len(matches)} matches:")
                for match in matches[:5]:  # Show first 5
                    print(f"  {match}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    debug_contest_page()
