# ScrapeChecker

A flexible monitoring framework that tracks changes on websites and sends notifications via Telegram. Perfect for monitoring contests, apartment listings, or any dynamic web content.

## Quick Start

### Contest Monitoring

Monitor pet contests, voting competitions, or rankings:

```bash
# Monitor all contestants
python -m scrapechecker.scrapers.contest_monitor https://contest-url

# Focus on specific contestant (only get notified about their changes)
python -m scrapechecker.scrapers.contest_monitor https://contest-url --target "Fido"

# Send current standings
python -m scrapechecker.scrapers.contest_monitor https://contest-url --send
```

## Configuration

Set up Telegram notifications by creating a `.env` file:

```bash
# Required for notifications
TELEGRAM_API_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional: Send to multiple recipients
TELEGRAM_CHAT_ID=123456789,987654321,555666777
```

## Key Features

- **Smart Filtering**: Only get notified about changes that matter to you
- **Multi-Chat Support**: Share updates with friends and family
- **Focused Notifications**: When monitoring a target item, see only relevant nearby context
- **Full Status on Demand**: Get complete rankings anytime with `--send`
- **Cross-Platform Storage**: Data files stored in proper OS-specific locations

## How It Works

The framework consists of modular components:

1. **Scrapers** extract data from specific websites
2. **Change Detection** identifies what's new, removed, or modified
3. **Smart Formatting** shows focused views for notifications, full context for manual requests
4. **Telegram Integration** sends rich HTML notifications to one or more recipients

### Target Item Behavior

When you specify a `--target`:

- **Change Notifications**: Only sent when your target item changes
- **Focused Display**: Shows your target ± nearby items (5 total)
- **Noise Reduction**: Ignores metadata changes and other contestants

Without a target:

- **All Changes**: Notified about any changes on the site
- **Full Display**: Shows all items up to reasonable limits

## Dependencies

- **Firefox + GeckoDriver**: For web scraping (auto-downloads if needed)
- **Python 3.12+**: With `selenium`, `requests`, and other standard libraries

It's recommended to install GeckoDriver yourself in `/usr/local/bin` to avoid having it reach out to GitHub each time it runs, which can cause rate limiting if run too often, but it will still do so if needed.

## Examples

```bash
# Monitor contest with daily status reports
python -m scrapechecker.scrapers.contest_monitor https://contest-url --target "Fido"

# Get current standings without monitoring
python -m scrapechecker.scrapers.contest_monitor https://contest-url --send

# Test your Telegram setup
python -m scrapechecker.scrapers.contest_monitor https://contest-url --test-alert
```

## Creating Custom Scrapers

Extend the framework for new websites:

```python
from scrapechecker.base_scraper import BaseScraper

class MyCustomScraper(BaseScraper):
    def extract_data(self, driver):
        # Your scraping logic here
        return [{"id": "item1", "name": "Example", "price": "$100"}]

    def get_item_key(self, item):
        return item["id"]  # Unique identifier for change tracking

    def format_item(self, item):
        return f"{item['name']} - {item['price']}"
```

The framework handles change detection, formatting, and notifications automatically.
