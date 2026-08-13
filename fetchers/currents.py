"""Currents API fetcher."""
import logging, aiohttp
logger = logging.getLogger("trends.currents")

URL = "https://api.currentsapi.services/v1/latest-news"

async def fetch_currents(session, api_key, limit=20):
    if not api_key:
        logger.warning("Currents: no key")
        return []
    articles = []
    for cat in ["technology", "business", "science"]:
        try:
            params = {"apiKey": api_key, "category": cat, "language": "en", "page_size": min(limit, 15)}
            async with session.get(URL, params=params) as r:
                if r.status == 200:
                    data = await r.json()
                    for a in data.get("news", []):
                        t = a.get("title", "").strip()
                        if t and len(t) > 5:
                            articles.append({"title": t, "url": a.get("url", ""),
                                             "description": (a.get("description") or "")[:200],
                                             "published_at": a.get("published", ""),
                                             "source": a.get("author", "Currents")})
                else:
                    logger.warning(f"Currents/{cat}: HTTP {r.status}")
        except Exception as e:
            logger.error(f"Currents/{cat}: {e}")
    logger.info(f"Currents: {len(articles)}")
    return articles
