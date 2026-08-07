"""
GNews Fetcher — Google News via gnews.io API
API Key: configured in config.py
"""
import asyncio
import logging
import aiohttp

logger = logging.getLogger("trend-pipeline.gnews")

GNEWS_URL = "https://gnews.io/api/v4/top-headlines"

class GNewsFetcher:
    def __init__(self, api_key, country="in", limit=20):
        self.api_key = api_key
        self.country = country
        self.limit = limit

    async def fetch(self, session):
        if not self.api_key:
            logger.warning("GNews key not configured — skipping")
            return []

        all_articles = []
        categories = ["technology", "business", "science", "general"]

        for category in categories:
            try:
                params = {
                    "token": self.api_key,
                    "country": self.country,
                    "category": category,
                    "max": min(self.limit, 10),
                    "lang": "en",
                }
                async with session.get(GNEWS_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        articles = data.get("articles", [])
                        for a in articles:
                            title = a.get("title", "").strip()
                            if title and len(title) > 5:
                                all_articles.append({
                                    "title": title,
                                    "url": a.get("url", ""),
                                    "source": a.get("source", {}).get("name", "GNews") if isinstance(a.get("source"), dict) else "GNews",
                                    "description": (a.get("description") or "")[:200],
                                    "published_at": a.get("publishedAt", ""),
                                })
                        logger.info(f"GNews/{category}: {len(articles)} articles")
                    else:
                        text = await resp.text()
                        logger.warning(f"GNews/{category}: HTTP {resp.status}")
                await asyncio.sleep(2)  # Rate limit: 100 req/day free tier
            except Exception as e:
                logger.error(f"GNews/{category}: {e}")
        return all_articles
