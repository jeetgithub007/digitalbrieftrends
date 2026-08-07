"""
NewsAPI Fetcher — headlines from 80K+ sources.
Free tier: 100 req/day. Sign up at https://newsapi.org/register
"""
import logging
import aiohttp

logger = logging.getLogger("trend-pipeline.newsapi")

NEWSAPI_URL = "https://newsapi.org/v2"

class NewsAPIFetcher:
    def __init__(self, api_key, country="in", categories=None):
        self.api_key = api_key
        self.country = country
        self.categories = categories or ["technology", "business", "science"]

    async def fetch(self, session):
        """Fetch top headlines from all configured categories."""
        all_articles = []
        if not self.api_key:
            logger.warning("NewsAPI key not configured — skipping")
            return []

        for category in self.categories:
            try:
                params = {
                    "country": self.country,
                    "category": category,
                    "apiKey": self.api_key,
                    "pageSize": 15,
                }
                async with session.get(f"{NEWSAPI_URL}/top-headlines", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        articles = data.get("articles", [])
                        for a in articles:
                            if a.get("title") and a.get("title") != "[Removed]":
                                all_articles.append({
                                    "title": a["title"],
                                    "url": a.get("url", ""),
                                    "source": a.get("source", {}).get("name", "NewsAPI"),
                                    "description": (a.get("description") or "")[:200],
                                    "published_at": a.get("publishedAt", ""),
                                })
                        logger.info(f"NewsAPI/{category}: {len(articles)} articles")
                    else:
                        logger.warning(f"NewsAPI/{category}: HTTP {resp.status}")
            except Exception as e:
                logger.error(f"NewsAPI/{category}: {e}")
        return all_articles
