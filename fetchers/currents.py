"""
Currents API Fetcher — currentsapi.services
API Key: configured in config.py
"""
import logging
import aiohttp

logger = logging.getLogger("trend-pipeline.currents")

CURRENTS_URL = "https://api.currentsapi.services/v1/latest-news"

class CurrentsFetcher:
    def __init__(self, api_key, categories=None, limit=20):
        self.api_key = api_key
        self.categories = categories or ["technology", "business", "science"]
        self.limit = limit

    async def fetch(self, session):
        if not self.api_key:
            logger.warning("Currents API key not configured — skipping")
            return []

        all_articles = []
        for category in self.categories:
            if category.lower() == 'ai':
                continue  # Currents doesn't support 'AI' as a separate category
            try:
                params = {
                    "apiKey": self.api_key,
                    "category": category.lower(),
                    "language": "en",
                    "page_size": min(self.limit, 15),
                }
                async with session.get(CURRENTS_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        articles = data.get("news", [])
                        for a in articles:
                            title = a.get("title", "").strip()
                            if title and len(title) > 5:
                                all_articles.append({
                                    "title": title,
                                    "url": a.get("url", ""),
                                    "source": a.get("author", "Currents"),
                                    "description": (a.get("description") or "")[:200],
                                    "published_at": a.get("published", ""),
                                })
                        logger.info(f"Currents/{category}: {len(articles)} articles")
                    else:
                        text = await resp.text()
                        logger.warning(f"Currents/{category}: HTTP {resp.status} — {text[:100]}")
            except Exception as e:
                logger.error(f"Currents/{category}: {e}")
        return all_articles
