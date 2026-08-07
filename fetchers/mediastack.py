"""
Mediastack Fetcher — live news from mediastack.com
API Key: configured in config.py
"""
import logging
import aiohttp

logger = logging.getLogger("trend-pipeline.mediastack")

MEDIASTACK_URL = "http://api.mediastack.com/v1/news"

class MediastackFetcher:
    def __init__(self, api_key, countries="in,us", categories="technology,business,science", limit=20):
        self.api_key = api_key
        self.countries = countries
        self.categories = categories
        self.limit = limit

    async def fetch(self, session):
        if not self.api_key:
            logger.warning("Mediastack key not configured — skipping")
            return []

        all_articles = []
        
        try:
            params = {
                "access_key": self.api_key,
                "countries": self.countries,
                "categories": self.categories,
                "limit": min(self.limit, 30),
                "sort": "published_desc",
                "languages": "en",
            }
            async with session.get(MEDIASTACK_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    articles = data.get("data", [])
                    for a in articles:
                        title = a.get("title", "").strip()
                        if title and len(title) > 5:
                            all_articles.append({
                                "title": title,
                                "url": a.get("url", ""),
                                "source": a.get("source", "Mediastack"),
                                "description": (a.get("description") or "")[:200],
                                "published_at": a.get("published_at", ""),
                            })
                    logger.info(f"Mediastack: {len(all_articles)} articles")
                else:
                    text = await resp.text()
                    logger.warning(f"Mediastack: HTTP {resp.status} — {text[:100]}")
        except Exception as e:
            logger.error(f"Mediastack: {e}")
        return all_articles
