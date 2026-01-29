"""
Feed crawler for knowledge ingestion.

Crawls RSS/Atom feeds and documentation pages
to keep the Knowledge Base updated.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import feedparser
import httpx
from bs4 import BeautifulSoup

from aicippy.config import get_settings
from aicippy.utils.logging import get_logger
from aicippy.utils.retry import async_retry

logger = get_logger(__name__)


@dataclass
class FeedItem:
    """A single item from a feed."""

    title: str
    link: str
    content: str
    published: datetime | None
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedSource:
    """Configuration for a feed source."""

    name: str
    url: str
    feed_type: str = "rss"  # rss, atom, html
    poll_interval_hours: int = 6
    selector: str | None = None  # CSS selector for HTML feeds
    enabled: bool = True


# Default feed sources
DEFAULT_FEEDS: list[FeedSource] = [
    FeedSource(
        name="AWS What's New",
        url="https://aws.amazon.com/new/feed/",
        feed_type="rss",
        poll_interval_hours=6,
    ),
    FeedSource(
        name="GCP Release Notes",
        url="https://cloud.google.com/feeds/gcp-release-notes.xml",
        feed_type="atom",
        poll_interval_hours=6,
    ),
    FeedSource(
        name="GitHub Blog",
        url="https://github.com/blog.atom",
        feed_type="atom",
        poll_interval_hours=6,
    ),
    FeedSource(
        name="Anthropic Blog",
        url="https://www.anthropic.com/blog",
        feed_type="html",
        poll_interval_hours=24,
        selector="article",
    ),
]


class FeedCrawler:
    """
    Crawler for fetching and parsing feed content.

    Supports RSS, Atom, and HTML page scraping.
    """

    def __init__(
        self,
        feeds: list[FeedSource] | None = None,
        max_concurrent: int = 5,
    ) -> None:
        """
        Initialize the crawler.

        Args:
            feeds: List of feed sources to crawl.
            max_concurrent: Maximum concurrent requests.
        """
        self._feeds = feeds or DEFAULT_FEEDS
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "AiCippy Knowledge Crawler/1.0",
                },
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def crawl_all(self) -> list[FeedItem]:
        """
        Crawl all configured feeds.

        Returns:
            List of feed items from all sources.
        """
        logger.info("crawl_started", feed_count=len(self._feeds))

        tasks = [
            self._crawl_feed(feed)
            for feed in self._feeds
            if feed.enabled
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: list[FeedItem] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "feed_crawl_failed",
                    feed=self._feeds[i].name,
                    error=str(result),
                )
            elif result:
                all_items.extend(result)

        logger.info("crawl_completed", total_items=len(all_items))
        return all_items

    async def _crawl_feed(self, feed: FeedSource) -> list[FeedItem]:
        """
        Crawl a single feed source.

        Args:
            feed: Feed source configuration.

        Returns:
            List of feed items.
        """
        async with self._semaphore:
            if feed.feed_type in ("rss", "atom"):
                return await self._crawl_rss_feed(feed)
            elif feed.feed_type == "html":
                return await self._crawl_html_page(feed)
            else:
                logger.warning("unsupported_feed_type", feed_type=feed.feed_type)
                return []

    @async_retry(max_attempts=3, min_wait=2.0)
    async def _crawl_rss_feed(self, feed: FeedSource) -> list[FeedItem]:
        """
        Crawl an RSS or Atom feed.

        Args:
            feed: Feed source configuration.

        Returns:
            List of feed items.
        """
        client = await self._get_client()
        response = await client.get(feed.url)
        response.raise_for_status()

        # Parse feed
        parsed = feedparser.parse(response.text)

        items: list[FeedItem] = []
        for entry in parsed.entries:
            # Extract content
            content = ""
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].value
            elif hasattr(entry, "summary"):
                content = entry.summary
            elif hasattr(entry, "description"):
                content = entry.description

            # Parse published date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])

            items.append(
                FeedItem(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    content=content,
                    published=published,
                    source=feed.name,
                )
            )

        logger.info(
            "rss_feed_crawled",
            feed=feed.name,
            items=len(items),
        )
        return items

    @async_retry(max_attempts=3, min_wait=2.0)
    async def _crawl_html_page(self, feed: FeedSource) -> list[FeedItem]:
        """
        Crawl an HTML page for content.

        Args:
            feed: Feed source configuration with CSS selector.

        Returns:
            List of feed items.
        """
        client = await self._get_client()
        response = await client.get(feed.url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        items: list[FeedItem] = []
        selector = feed.selector or "article"

        for element in soup.select(selector)[:20]:  # Limit to 20 items
            # Extract title
            title_el = element.select_one("h1, h2, h3, .title")
            title = title_el.get_text(strip=True) if title_el else ""

            # Extract link
            link_el = element.select_one("a[href]")
            link = link_el["href"] if link_el else feed.url
            if link.startswith("/"):
                # Make absolute
                from urllib.parse import urljoin
                link = urljoin(feed.url, link)

            # Extract content
            content = element.get_text(strip=True, separator=" ")

            if title:
                items.append(
                    FeedItem(
                        title=title,
                        link=link,
                        content=content[:5000],  # Limit content length
                        published=None,
                        source=feed.name,
                    )
                )

        logger.info(
            "html_page_crawled",
            feed=feed.name,
            items=len(items),
        )
        return items

    def add_feed(self, feed: FeedSource) -> None:
        """Add a feed source."""
        self._feeds.append(feed)

    def remove_feed(self, name: str) -> bool:
        """Remove a feed source by name."""
        for i, feed in enumerate(self._feeds):
            if feed.name == name:
                del self._feeds[i]
                return True
        return False

    def list_feeds(self) -> list[FeedSource]:
        """Get all configured feeds."""
        return self._feeds.copy()
