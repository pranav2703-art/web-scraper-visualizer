"""
scraper.py
----------
Fetches and parses HTML from one or more URLs using requests + BeautifulSoup.
Returns a list of raw record dicts ready for the cleaning pipeline.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; WebScraperBot/1.0; "
        "+https://github.com/yourusername/web-scraper-visualizer)"
    )
}
REQUEST_TIMEOUT = 10  # seconds
RETRY_DELAY = 2  # seconds between retries


@dataclass
class ScrapeResult:
    url: str
    records: list[dict]
    status_code: int
    elapsed_ms: float
    error: Optional[str] = None


@dataclass
class ScraperConfig:
    urls: list[str]
    css_selectors: dict[str, str]  # e.g. {"text": "span.text", "author": "small.author"}
    max_retries: int = 3
    delay_between_requests: float = 1.0
    headers: dict = field(default_factory=lambda: DEFAULT_HEADERS.copy())


def _fetch(url: str, headers: dict, timeout: int, retries: int) -> requests.Response:
    """GET a URL with retry logic on transient failures."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            logger.warning("Attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            if attempt < retries:
                time.sleep(RETRY_DELAY)
    raise RuntimeError(f"All {retries} attempts failed for {url}")


def _parse(html: str, selectors: dict[str, str]) -> list[dict]:
    """Extract records from raw HTML using CSS selectors."""
    soup = BeautifulSoup(html, "html.parser")
    # Find the container elements by the first selector's parent scope.
    # Assumes all selectors point to children of the same repeating container.
    first_key = next(iter(selectors))
    containers = soup.select(selectors[first_key])

    records = []
    for container in containers:
        record = {}
        for field_name, selector in selectors.items():
            elements = soup.select(selector)
            # Align by index — each selector should return the same count.
            idx = containers.index(container)
            if idx < len(elements):
                record[field_name] = elements[idx].get_text(strip=True)
            else:
                record[field_name] = None
        records.append(record)

    return records


def scrape(config: ScraperConfig) -> list[ScrapeResult]:
    """
    Scrape all URLs defined in *config*.

    Returns a list of ScrapeResult objects — one per URL.
    """
    results: list[ScrapeResult] = []

    for url in config.urls:
        logger.info("Scraping: %s", url)
        start = time.monotonic()

        try:
            response = _fetch(url, config.headers, REQUEST_TIMEOUT, config.max_retries)
            elapsed = (time.monotonic() - start) * 1000
            records = _parse(response.text, config.css_selectors)
            results.append(
                ScrapeResult(
                    url=url,
                    records=records,
                    status_code=response.status_code,
                    elapsed_ms=round(elapsed, 2),
                )
            )
            logger.info("  → %d records in %.0f ms", len(records), elapsed)
        except Exception as exc:  # noqa: BLE001
            elapsed = (time.monotonic() - start) * 1000
            logger.error("Failed to scrape %s: %s", url, exc)
            results.append(
                ScrapeResult(
                    url=url,
                    records=[],
                    status_code=0,
                    elapsed_ms=round(elapsed, 2),
                    error=str(exc),
                )
            )

        time.sleep(config.delay_between_requests)

    return results
