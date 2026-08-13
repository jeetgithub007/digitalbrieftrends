"""Google Trends fetcher — real-time daily trending topics.

Uses Google's official daily-trending RSS feed (pytrends' "trending now"
endpoints were deprecated and return 404). Each topic links to Google News
so users land on REAL articles, never the Google Trends explore page.
"""
import asyncio, logging
from urllib.parse import quote
from urllib.request import Request, urlopen

logger = logging.getLogger("trends.google")

TRENDING_RSS = {
    "India": "https://trends.google.com/trending/rss?geo=IN",
    "United States": "https://trends.google.com/trending/rss?geo=US",
}


def _news_url(query):
    """Link to real news articles about a topic (Google News search)."""
    return f"https://news.google.com/search?q={quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"


def _fetch_feed(url):
    import feedparser
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DigitalBrief/1.0)"})
    raw = urlopen(req, timeout=15).read()
    return feedparser.parse(raw)


def _real_description(entry):
    """Extract a real news headline about the topic (factual, not fabricated)."""
    for item in entry.get("ht_news_item", []) or []:
        title = (item.get("title") or "").strip()
        if title and len(title) > 20:
            return title
    return ""


def _is_english(text):
    """Keep only Latin-script (English) topics; skip regional-language trends."""
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    return ascii_chars / max(1, len(text)) > 0.85


async def fetch_google_trends(keywords):
    loop = __import__("asyncio").get_event_loop()
    return await loop.run_in_executor(None, _sync_fetch)


def _sync_fetch():
    items = []
    seen = set()
    for region, url in TRENDING_RSS.items():
        try:
            feed = _fetch_feed(url)
            for e in feed.entries:
                title = (e.get("title") or "").strip()
                if title and len(title) > 2 and title.lower() not in seen and _is_english(title):
                    seen.add(title.lower())
                    items.append({
                        "title": title,
                        "url": _news_url(title),
                        "source": "google_trends",
                        "region": region,
                        "description": _real_description(e),
                        "search_volume": 0,
                    })
            logger.info(f"Google Trends/{region}: {len(feed.entries)} trending topics")
        except Exception as err:
            logger.warning(f"Google Trends/{region}: {err}")
    logger.info(f"Google Trends: {len(items)} real-time topics")
    return items
