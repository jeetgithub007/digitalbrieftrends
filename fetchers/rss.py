"""
RSS Feed Fetcher — Tech & business news from major publications.
"""
import logging
import asyncio
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("trend-pipeline.rss")

class RSSFetcher:
    def __init__(self, feeds):
        self.feeds = feeds  # List of (name, url) tuples

    async def fetch(self):
        """Fetch latest entries from all configured RSS feeds."""
        import feedparser
        entries = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)

        for feed_name, feed_url in self.feeds:
            try:
                loop = asyncio.get_event_loop()
                parsed = await loop.run_in_executor(None, feedparser.parse, feed_url)
                for entry in parsed.entries[:8]:
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                    if published and published < cutoff:
                        continue

                    entries.append({
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "source": feed_name,
                        "published_at": published.isoformat() if published else "",
                    })
                logger.info(f"RSS/{feed_name}: {min(8, len(parsed.entries))} entries")
            except Exception as e:
                logger.warning(f"RSS/{feed_name}: {e}")
            await asyncio.sleep(1)
        return entries
